"use strict";

/*
 * BUDGET PREPARATION AND VARIANCE ANALYSIS
 *
 * Node.js 18+
 *
 * Event-driven budgeting engine featuring:
 * - Budget lifecycle events
 * - Department allocations
 * - Static and flexible budgets
 * - Actual transaction processing
 * - Revenue and expense variance evaluation
 * - Forecasting
 * - Approval workflows
 * - Budget policy enforcement
 * - Asynchronous report generation
 * - JSON persistence
 */

const fs = require("node:fs/promises");
const EventEmitter = require("node:events");

// ---------------------------------------------------------
// Financial utilities
// ---------------------------------------------------------

const MONEY_SCALE = 100;

function amount(value) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < 0
    ) {
        throw new TypeError("Financial amount must be a finite non-negative number.");
    }

    return Math.round((value + Number.EPSILON) * MONEY_SCALE) /
        MONEY_SCALE;
}

function signedAmount(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        throw new TypeError("Invalid signed financial amount.");
    }

    return Math.round((value + Math.sign(value) * Number.EPSILON) *
        MONEY_SCALE) / MONEY_SCALE;
}

function percent(numerator, denominator) {
    if (denominator === 0) return 0;
    return signedAmount((numerator / denominator) * 100);
}

function requireText(value, field) {
    if (typeof value !== "string" || value.trim().length === 0) {
        throw new TypeError(`${field} is required.`);
    }
}

function requirePeriod(period) {
    if (!Number.isInteger(period) || period < 1 || period > 12) {
        throw new RangeError("Accounting period must be between 1 and 12.");
    }
}

// ---------------------------------------------------------
// Enumerations
// ---------------------------------------------------------

const AccountType = Object.freeze({
    REVENUE: "REVENUE",
    EXPENSE: "EXPENSE"
});

const CostType = Object.freeze({
    FIXED: "FIXED",
    VARIABLE: "VARIABLE",
    MIXED: "MIXED"
});

const BudgetState = Object.freeze({
    DRAFT: "DRAFT",
    SUBMITTED: "SUBMITTED",
    APPROVED: "APPROVED",
    REJECTED: "REJECTED",
    CLOSED: "CLOSED"
});

const VarianceState = Object.freeze({
    FAVORABLE: "FAVORABLE",
    UNFAVORABLE: "UNFAVORABLE",
    ON_TARGET: "ON_TARGET"
});

// ---------------------------------------------------------
// Domain objects
// ---------------------------------------------------------

class Department {
    constructor(id, name, spendingLimit) {
        requireText(id, "Department ID");
        requireText(name, "Department name");

        this.id = id;
        this.name = name;
        this.spendingLimit = amount(spendingLimit);
        Object.freeze(this);
    }
}

class BudgetItem {
    constructor({
        code,
        description,
        departmentId,
        accountType,
        costType,
        fixedAmount = 0,
        variableRate = 0,
        plannedActivity = 0
    }) {
        requireText(code, "Account code");
        requireText(description, "Description");
        requireText(departmentId, "Department ID");

        if (!Object.values(AccountType).includes(accountType)) {
            throw new TypeError("Invalid account type.");
        }

        if (!Object.values(CostType).includes(costType)) {
            throw new TypeError("Invalid cost type.");
        }

        if (accountType === AccountType.REVENUE &&
            costType !== CostType.FIXED) {
            throw new Error("Revenue must use the revenue planning model.");
        }

        this.code = code;
        this.description = description;
        this.departmentId = departmentId;
        this.accountType = accountType;
        this.costType = costType;
        this.fixedAmount = amount(fixedAmount);
        this.variableRate = amount(variableRate);
        this.plannedActivity = amount(plannedActivity);

        Object.freeze(this);
    }

    calculate(activity = this.plannedActivity) {
        if (this.accountType === AccountType.REVENUE) {
            return this.fixedAmount;
        }

        if (this.costType === CostType.FIXED) {
            return this.fixedAmount;
        }

        if (this.costType === CostType.VARIABLE) {
            return amount(this.variableRate * activity);
        }

        return amount(
            this.fixedAmount + this.variableRate * activity
        );
    }
}

// ---------------------------------------------------------
// Budget aggregate
// ---------------------------------------------------------

class Budget extends EventEmitter {
    #items = new Map();
    #state = BudgetState.DRAFT;

    constructor(id, fiscalYear, departments) {
        super();

        requireText(id, "Budget ID");

        if (!Number.isInteger(fiscalYear) ||
            fiscalYear < 2000 || fiscalYear > 2200) {
            throw new RangeError("Invalid fiscal year.");
        }

        this.id = id;
        this.fiscalYear = fiscalYear;
        this.departments = departments;
        this.revision = 1;
    }

    get state() {
        return this.#state;
    }

    get items() {
        return [...this.#items.values()];
    }

    addItem(item) {
        if (this.#state !== BudgetState.DRAFT) {
            throw new Error("Budget modifications require draft status.");
        }

        if (!(item instanceof BudgetItem)) {
            throw new TypeError("Expected a BudgetItem.");
        }

        if (!this.departments.has(item.departmentId)) {
            throw new Error("Unknown department.");
        }

        const key = `${item.departmentId}:${item.code}`;

        if (this.#items.has(key)) {
            throw new Error("Duplicate budget item.");
        }

        this.#items.set(key, item);
        this.emit("itemAdded", item);
    }

    total(accountType) {
        return amount(
            this.items
                .filter(item => item.accountType === accountType)
                .reduce((sum, item) => sum + item.calculate(), 0)
        );
    }

    get plannedProfit() {
        return signedAmount(
            this.total(AccountType.REVENUE) -
            this.total(AccountType.EXPENSE)
        );
    }

    transition(expectedState, nextState) {
        if (this.#state !== expectedState) {
            throw new Error(
                `Invalid transition: ${this.#state} -> ${nextState}`
            );
        }

        this.#state = nextState;

        this.emit("stateChanged", {
            budgetId: this.id,
            previous: expectedState,
            current: nextState,
            timestamp: new Date().toISOString()
        });
    }
}

// ---------------------------------------------------------
// Policy engine
// ---------------------------------------------------------

class BudgetPolicy {
    constructor({
        requireApproval = true,
        enforceDepartmentLimits = true,
        maximumRevision = 10
    } = {}) {
        this.requireApproval = requireApproval;
        this.enforceDepartmentLimits = enforceDepartmentLimits;
        this.maximumRevision = maximumRevision;
    }

    evaluate(budget) {
        const errors = [];
        const totals = new Map();

        for (const item of budget.items) {
            if (item.accountType !== AccountType.EXPENSE) {
                continue;
            }

            totals.set(
                item.departmentId,
                amount(
                    (totals.get(item.departmentId) || 0) +
                    item.calculate()
                )
            );
        }

        if (this.enforceDepartmentLimits) {
            for (const [id, total] of totals) {
                const department = budget.departments.get(id);

                if (total > department.spendingLimit) {
                    errors.push(
                        `${id} exceeds spending limit by ${
                            amount(total - department.spendingLimit)
                        }`
                    );
                }
            }
        }

        if (budget.revision > this.maximumRevision) {
            errors.push("Maximum revision count exceeded.");
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }
}

// ---------------------------------------------------------
// Workflow service
// ---------------------------------------------------------

class BudgetWorkflow {
    constructor(policy) {
        this.policy = policy;
    }

    submit(budget) {
        if (budget.state !== BudgetState.DRAFT) {
            throw new Error("Only draft budgets can be submitted.");
        }

        const result = this.policy.evaluate(budget);

        if (!result.valid) {
            throw new Error(result.errors.join("; "));
        }

        budget.transition(
            BudgetState.DRAFT,
            BudgetState.SUBMITTED
        );
    }

    approve(budget, approver) {
        requireText(approver, "Approver");

        if (budget.state !== BudgetState.SUBMITTED) {
            throw new Error("Budget is not awaiting approval.");
        }

        budget.transition(
            BudgetState.SUBMITTED,
            BudgetState.APPROVED
        );

        budget.emit("approved", {
            budgetId: budget.id,
            approver,
            approvedAt: new Date().toISOString()
        });
    }

    reject(budget, approver, reason) {
        requireText(approver, "Approver");
        requireText(reason, "Rejection reason");

        budget.transition(
            BudgetState.SUBMITTED,
            BudgetState.REJECTED
        );

        budget.emit("rejected", {
            budgetId: budget.id,
            approver,
            reason
        });
    }
}

// ---------------------------------------------------------
// Actual transaction stream
// ---------------------------------------------------------

class ActualLedger extends EventEmitter {
    #transactions = new Map();

    record(transaction, budget) {
        if (budget.state !== BudgetState.APPROVED) {
            throw new Error("Actuals require an approved budget.");
        }

        requireText(transaction.id, "Transaction ID");

        if (transaction.budgetId !== budget.id) {
            throw new Error("Budget reference mismatch.");
        }

        requirePeriod(transaction.period);

        if (this.#transactions.has(transaction.id)) {
            throw new Error("Duplicate transaction.");
        }

        const value = amount(transaction.amount);

        const matching = budget.items.some(item =>
            item.code === transaction.accountCode &&
            item.departmentId === transaction.departmentId &&
            item.accountType === transaction.accountType
        );

        if (!matching) {
            throw new Error("Transaction has no matching budget account.");
        }

        const normalized = Object.freeze({
            ...transaction,
            amount: value
        });

        this.#transactions.set(normalized.id, normalized);

        this.emit("transactionRecorded", normalized);
    }

    aggregate({
        budgetId,
        accountCode,
        departmentId,
        accountType,
        period = null
    }) {
        return amount(
            [...this.#transactions.values()]
                .filter(transaction =>
                    transaction.budgetId === budgetId &&
                    transaction.accountCode === accountCode &&
                    transaction.departmentId === departmentId &&
                    transaction.accountType === accountType &&
                    (period === null || transaction.period === period)
                )
                .reduce((sum, transaction) =>
                    sum + transaction.amount, 0)
        );
    }

    get transactions() {
        return [...this.#transactions.values()];
    }
}

// ---------------------------------------------------------
// Variance calculation
// ---------------------------------------------------------

class VarianceEngine {
    classify(accountType, variance) {
        if (variance === 0) return VarianceState.ON_TARGET;

        const favorable =
            accountType === AccountType.REVENUE
                ? variance > 0
                : variance < 0;

        return favorable
            ? VarianceState.FAVORABLE
            : VarianceState.UNFAVORABLE;
    }

    evaluate(budget, ledger, period = null) {
        if (budget.state !== BudgetState.APPROVED) {
            throw new Error("Budget must be approved.");
        }

        if (period !== null) requirePeriod(period);

        return budget.items.map(item => {
            const planned = period === null
                ? item.calculate()
                : amount(item.calculate() / 12);

            const actual = ledger.aggregate({
                budgetId: budget.id,
                accountCode: item.code,
                departmentId: item.departmentId,
                accountType: item.accountType,
                period
            });

            const variance = signedAmount(actual - planned);

            return Object.freeze({
                accountCode: item.code,
                departmentId: item.departmentId,
                accountType: item.accountType,
                budget: planned,
                actual,
                variance,
                variancePercentage: percent(variance, planned),
                status: this.classify(item.accountType, variance)
            });
        });
    }

    flexibleExpense(item, actualActivity) {
        if (item.accountType !== AccountType.EXPENSE) {
            throw new Error("Flexible expense calculation requires an expense.");
        }

        return item.calculate(amount(actualActivity));
    }

    evaluateFlexible(budget, ledger, period, activityByDepartment) {
        requirePeriod(period);

        return budget.items
            .filter(item => item.accountType === AccountType.EXPENSE)
            .map(item => {
                const activity = amount(
                    activityByDepartment.get(item.departmentId) ?? 0
                );

                const planned = this.flexibleExpense(item, activity);

                const actual = ledger.aggregate({
                    budgetId: budget.id,
                    accountCode: item.code,
                    departmentId: item.departmentId,
                    accountType: AccountType.EXPENSE,
                    period
                });

                const variance = signedAmount(actual - planned);

                return Object.freeze({
                    accountCode: item.code,
                    departmentId: item.departmentId,
                    budget: planned,
                    actual,
                    variance,
                    variancePercentage: percent(variance, planned),
                    status: this.classify(
                        AccountType.EXPENSE,
                        variance
                    )
                });
            });
    }
}

// ---------------------------------------------------------
// Reporting and forecasting
// ---------------------------------------------------------

class ReportingService {
    static departmentSummary(results) {
        const summary = new Map();

        for (const result of results) {
            if (!summary.has(result.departmentId)) {
                summary.set(result.departmentId, {
                    budget: 0,
                    actual: 0,
                    variance: 0
                });
            }

            const row = summary.get(result.departmentId);

            row.budget = amount(row.budget + result.budget);
            row.actual = amount(row.actual + result.actual);
            row.variance = signedAmount(
                row.variance + result.variance
            );
        }

        return summary;
    }

    static forecast(yearToDateActual, elapsedMonths) {
        if (
            !Number.isInteger(elapsedMonths) ||
            elapsedMonths < 1 ||
            elapsedMonths > 12
        ) {
            throw new RangeError("Invalid elapsed month count.");
        }

        return amount(
            amount(yearToDateActual) * 12 / elapsedMonths
        );
    }

    static utilization(actual, approvedBudget) {
        if (approvedBudget <= 0) {
            throw new RangeError("Budget must be positive.");
        }

        return percent(actual, approvedBudget);
    }

    static print(results) {
        console.log("\nVARIANCE REPORT");
        console.log(
            "ACCOUNT     DEPARTMENT     BUDGET       ACTUAL       VARIANCE      STATUS"
        );

        for (const row of results) {
            console.log(
                `${row.accountCode.padEnd(12)}` +
                `${row.departmentId.padEnd(15)}` +
                `${row.budget.toFixed(2).padStart(11)}` +
                `${row.actual.toFixed(2).padStart(13)}` +
                `${row.variance.toFixed(2).padStart(13)}` +
                `  ${row.status}`
            );
        }
    }
}

// ---------------------------------------------------------
// Asynchronous persistence
// ---------------------------------------------------------

async function saveReport(filename, results) {
    const temporary = `${filename}.tmp`;

    try {
        const serialized = JSON.stringify(
            results,
            null,
            2
        );

        await fs.writeFile(temporary, serialized, {
            encoding: "utf8",
            flag: "wx"
        });

        await fs.rename(temporary, filename);
    } catch (error) {
        await fs.rm(temporary, { force: true }).catch(() => {});
        throw error;
    }
}

// ---------------------------------------------------------
// Application event subscriptions
// ---------------------------------------------------------

async function main() {
    const departments = new Map([
        ["FIN", new Department("FIN", "Finance", 500000)],
        ["OPS", new Department("OPS", "Operations", 900000)],
        ["IT", new Department("IT", "Technology", 600000)]
    ]);

    const budget = new Budget("BUDGET-2027", 2027, departments);

    budget.on("stateChanged", event => {
        console.log(
            `[EVENT] ${event.budgetId}: ${event.previous} -> ${event.current}`
        );
    });

    budget.on("itemAdded", item => {
        console.log(`[EVENT] Budget item registered: ${item.code}`);
    });

    budget.on("approved", event => {
        console.log(`[EVENT] Approved by ${event.approver}`);
    });

    const definitions = [
        {
            code: "REV001",
            description: "Service revenue",
            departmentId: "FIN",
            accountType: AccountType.REVENUE,
            costType: CostType.FIXED,
            fixedAmount: 3000000
        },
        {
            code: "EXP001",
            description: "Salaries",
            departmentId: "FIN",
            accountType: AccountType.EXPENSE,
            costType: CostType.FIXED,
            fixedAmount: 360000
        },
        {
            code: "EXP002",
            description: "Materials",
            departmentId: "OPS",
            accountType: AccountType.EXPENSE,
            costType: CostType.VARIABLE,
            variableRate: 120,
            plannedActivity: 5000
        },
        {
            code: "EXP003",
            description: "IT infrastructure",
            departmentId: "IT",
            accountType: AccountType.EXPENSE,
            costType: CostType.MIXED,
            fixedAmount: 180000,
            variableRate: 20,
            plannedActivity: 5000
        }
    ];

    for (const definition of definitions) {
        budget.addItem(new BudgetItem(definition));
    }

    console.log("\nBUDGET PREPARATION");
    console.log("Planned revenue:", budget.total(AccountType.REVENUE));
    console.log("Planned expenses:", budget.total(AccountType.EXPENSE));
    console.log("Planned profit:", budget.plannedProfit);

    const workflow = new BudgetWorkflow(
        new BudgetPolicy({
            requireApproval: true,
            enforceDepartmentLimits: true
        })
    );

    workflow.submit(budget);
    workflow.approve(budget, "Finance Controller");

    const ledger = new ActualLedger();

    ledger.on("transactionRecorded", transaction => {
        console.log(`[EVENT] Recorded transaction ${transaction.id}`);
    });

    const transactions = [
        {
            id: "TX001",
            budgetId: budget.id,
            accountCode: "REV001",
            departmentId: "FIN",
            accountType: AccountType.REVENUE,
            period: 1,
            amount: 280000
        },
        {
            id: "TX002",
            budgetId: budget.id,
            accountCode: "EXP001",
            departmentId: "FIN",
            accountType: AccountType.EXPENSE,
            period: 1,
            amount: 30000
        },
        {
            id: "TX003",
            budgetId: budget.id,
            accountCode: "EXP002",
            departmentId: "OPS",
            accountType: AccountType.EXPENSE,
            period: 1,
            amount: 55000
        },
        {
            id: "TX004",
            budgetId: budget.id,
            accountCode: "EXP003",
            departmentId: "IT",
            accountType: AccountType.EXPENSE,
            period: 1,
            amount: 19000
        }
    ];

    for (const transaction of transactions) {
        ledger.record(transaction, budget);
    }

    const engine = new VarianceEngine();

    const annual = engine.evaluate(budget, ledger);
    ReportingService.print(annual);

    const monthly = engine.evaluate(budget, ledger, 1);

    console.log("\nMONTHLY VARIANCE");
    ReportingService.print(monthly);

    const flexible = engine.evaluateFlexible(
        budget,
        ledger,
        1,
        new Map([
            ["OPS", 450],
            ["IT", 500]
        ])
    );

    console.log("\nFLEXIBLE BUDGET ANALYSIS");
    ReportingService.print(flexible);

    console.log("\nDEPARTMENT REPORT");

    for (const [department, figures] of
        ReportingService.departmentSummary(annual)) {
        console.log(department, figures);
    }

    console.log("\nFORECAST");
    console.log(
        "Projected annual expense:",
        ReportingService.forecast(55000, 1)
    );

    console.log("\nUTILIZATION");
    console.log(
        "Operations:",
        ReportingService.utilization(55000, 600000)
    );

    await saveReport("budget_variance_report.json", monthly);

    console.log("\nVALIDATION");

    if (percent(25, 100) !== 25) {
        throw new Error("Percentage validation failed.");
    }

    if (engine.classify(AccountType.REVENUE, 100) !==
        VarianceState.FAVORABLE) {
        throw new Error("Revenue variance validation failed.");
    }

    if (engine.classify(AccountType.EXPENSE, 100) !==
        VarianceState.UNFAVORABLE) {
        throw new Error("Expense variance validation failed.");
    }

    try {
        ledger.record(transactions[0], budget);
    } catch (error) {
        console.log("Duplicate transaction rejected:", error.message);
    }

    console.log("All budgeting checks passed.");
}

main().catch(error => {
    console.error("Budgeting system error:", error.message);
    process.exitCode = 1;
});
