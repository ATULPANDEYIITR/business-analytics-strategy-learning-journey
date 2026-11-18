"use strict";

/*
 * Financial Forecasting and Scenario Evaluation Engine.
 *
 * Node.js 18+
 * No external dependencies.
 *
 * Provides:
 * - Event-driven financial data updates
 * - Revenue and expense forecasts
 * - Cash-flow projections
 * - Scenario policy evaluation
 * - Forecast version tracking
 * - Budget controls
 * - CSV export
 * - Asynchronous forecast execution
 * - Financial validation and audit events
 */

const fs = require("node:fs/promises");
const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

class FinancialError extends Error {}
class ValidationError extends FinancialError {}
class InsufficientDataError extends FinancialError {}
class StateError extends FinancialError {}

const Scenario = Object.freeze({
    BASE: "BASE",
    OPTIMISTIC: "OPTIMISTIC",
    PESSIMISTIC: "PESSIMISTIC"
});

const ForecastStatus = Object.freeze({
    HEALTHY: "HEALTHY",
    LOW_CASH: "LOW_CASH",
    NEGATIVE_CASH: "NEGATIVE_CASH"
});

function validateMoney(value, name, allowNegative = false) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value)
    ) {
        throw new ValidationError(`${name} must be a finite number.`);
    }

    if (!allowNegative && value < 0) {
        throw new ValidationError(`${name} cannot be negative.`);
    }

    return value;
}

function validatePeriod(period) {
    if (
        typeof period !== "string" ||
        !/^\d{4}-(0[1-9]|1[0-2])$/.test(period)
    ) {
        throw new ValidationError(`Invalid period: ${period}`);
    }

    return period;
}

function roundMoney(value) {
    return Math.round((value + Number.EPSILON) * 100) / 100;
}

function nextMonth(period) {
    const [year, month] = period.split("-").map(Number);

    const next = new Date(Date.UTC(year, month, 1));

    return `${next.getUTCFullYear()}-${String(
        next.getUTCMonth() + 1
    ).padStart(2, "0")}`;
}

class FinancialRecord {
    constructor(data) {
        this.period = validatePeriod(data.period);

        this.revenue = validateMoney(data.revenue, "Revenue");
        this.operatingExpenses = validateMoney(
            data.operatingExpenses,
            "Operating expenses"
        );

        this.investingExpenses = validateMoney(
            data.investingExpenses,
            "Investing expenses"
        );

        this.financingCashFlow = validateMoney(
            data.financingCashFlow ?? 0,
            "Financing cash flow",
            true
        );

        this.openingCash = validateMoney(
            data.openingCash,
            "Opening cash"
        );

        Object.freeze(this);
    }

    get operatingProfit() {
        return this.revenue - this.operatingExpenses;
    }

    get netCashFlow() {
        return (
            this.operatingProfit -
            this.investingExpenses +
            this.financingCashFlow
        );
    }

    get closingCash() {
        return this.openingCash + this.netCashFlow;
    }
}

class FinancialRepository extends EventEmitter {
    #records = new Map();
    #revision = 0;

    add(record) {
        if (!(record instanceof FinancialRecord)) {
            throw new ValidationError("Invalid financial record.");
        }

        if (this.#records.has(record.period)) {
            throw new ValidationError(
                `Period ${record.period} already exists.`
            );
        }

        this.#records.set(record.period, record);
        this.#revision++;

        this.emit("recordAdded", {
            period: record.period,
            revision: this.#revision
        });
    }

    get revision() {
        return this.#revision;
    }

    getRecords() {
        return Object.freeze(
            [...this.#records.values()].sort(
                (a, b) => a.period.localeCompare(b.period)
            )
        );
    }

    getLatest() {
        const records = this.getRecords();

        if (records.length === 0) {
            throw new InsufficientDataError("No financial data.");
        }

        return records[records.length - 1];
    }

    snapshot() {
        return Object.freeze({
            revision: this.#revision,
            records: this.getRecords()
        });
    }
}

class GrowthCalculator {
    static calculate(values) {
        if (values.length < 2) {
            return 0;
        }

        if (values.some(value => value < 0)) {
            throw new ValidationError(
                "Growth calculations require nonnegative values."
            );
        }

        const first = values[0];
        const last = values[values.length - 1];

        if (first > 0) {
            return Math.pow(
                last / first,
                1 / (values.length - 1)
            ) - 1;
        }

        const changes = [];

        for (let i = 1; i < values.length; i++) {
            changes.push(
                (values[i] - values[i - 1]) /
                Math.max(Math.abs(values[i - 1]), 1)
            );
        }

        return changes.reduce((a, b) => a + b, 0) /
            changes.length;
    }

    static movingAverage(values, window) {
        if (
            !Number.isInteger(window) ||
            window < 1 ||
            values.length === 0
        ) {
            throw new ValidationError("Invalid moving-average window.");
        }

        const selected = values.slice(-window);

        return selected.reduce((a, b) => a + b, 0) /
            selected.length;
    }
}

class ScenarioPolicy {
    constructor({
        optimisticRevenueAdjustment = 0.05,
        pessimisticRevenueAdjustment = -0.05,
        expenseAdjustment = 0.02
    } = {}) {
        this.optimisticRevenueAdjustment =
            optimisticRevenueAdjustment;

        this.pessimisticRevenueAdjustment =
            pessimisticRevenueAdjustment;

        this.expenseAdjustment = expenseAdjustment;

        for (const value of Object.values(this)) {
            if (!Number.isFinite(value)) {
                throw new ValidationError(
                    "Scenario adjustments must be finite."
                );
            }
        }

        Object.freeze(this);
    }

    evaluate(scenario) {
        switch (scenario) {
            case Scenario.BASE:
                return {
                    revenueAdjustment: 0,
                    expenseAdjustment: 0
                };

            case Scenario.OPTIMISTIC:
                return {
                    revenueAdjustment:
                        this.optimisticRevenueAdjustment,
                    expenseAdjustment: 0
                };

            case Scenario.PESSIMISTIC:
                return {
                    revenueAdjustment:
                        this.pessimisticRevenueAdjustment,
                    expenseAdjustment: this.expenseAdjustment
                };

            default:
                throw new ValidationError(
                    `Unknown scenario: ${scenario}`
                );
        }
    }
}

class ForecastEngine {
    constructor(repository, {
        horizon = 6,
        window = 3,
        scenarioPolicy = new ScenarioPolicy()
    } = {}) {
        if (!(repository instanceof FinancialRepository)) {
            throw new ValidationError("Invalid repository.");
        }

        if (
            !Number.isInteger(horizon) ||
            horizon < 1 ||
            horizon > 120
        ) {
            throw new ValidationError("Horizon must be 1 to 120.");
        }

        if (!Number.isInteger(window) || window < 1) {
            throw new ValidationError("Window must be positive.");
        }

        this.repository = repository;
        this.horizon = horizon;
        this.window = window;
        this.scenarioPolicy = scenarioPolicy;
    }

    async run(scenario = Scenario.BASE) {
        // Yield control so the forecast can participate in async workflows.
        await Promise.resolve();

        const snapshot = this.repository.snapshot();
        const records = snapshot.records;

        if (records.length < this.window) {
            throw new InsufficientDataError(
                "Insufficient historical observations."
            );
        }

        const policy = this.scenarioPolicy.evaluate(scenario);

        const revenueValues = records.map(r => r.revenue);
        const expenseValues = records.map(
            r => r.operatingExpenses
        );

        const investmentValues = records.map(
            r => r.investingExpenses
        );

        let revenueGrowth = GrowthCalculator.calculate(
            revenueValues
        ) + policy.revenueAdjustment;

        let expenseGrowth = GrowthCalculator.calculate(
            expenseValues
        ) + policy.expenseAdjustment;

        revenueGrowth = Math.max(-0.95, Math.min(1, revenueGrowth));
        expenseGrowth = Math.max(-0.95, Math.min(1, expenseGrowth));

        let revenue = GrowthCalculator.movingAverage(
            revenueValues,
            this.window
        );

        let expenses = GrowthCalculator.movingAverage(
            expenseValues,
            this.window
        );

        const investments = GrowthCalculator.movingAverage(
            investmentValues,
            this.window
        );

        let cash = records[records.length - 1].closingCash;
        let period = nextMonth(records[records.length - 1].period);

        const results = [];

        for (let index = 0; index < this.horizon; index++) {
            revenue *= 1 + revenueGrowth;
            expenses *= 1 + expenseGrowth;

            const operatingProfit = revenue - expenses;
            const netCashFlow = operatingProfit - investments;

            const openingCash = cash;
            const closingCash = openingCash + netCashFlow;

            const profitMargin = revenue > 0
                ? operatingProfit / revenue
                : 0;

            const cashStatus =
                closingCash < 0
                    ? ForecastStatus.NEGATIVE_CASH
                    : closingCash < expenses
                        ? ForecastStatus.LOW_CASH
                        : ForecastStatus.HEALTHY;

            results.push(Object.freeze({
                period,
                scenario,
                revenue: roundMoney(revenue),
                operatingExpenses: roundMoney(expenses),
                investingExpenses: roundMoney(investments),
                operatingProfit: roundMoney(operatingProfit),
                netCashFlow: roundMoney(netCashFlow),
                openingCash: roundMoney(openingCash),
                closingCash: roundMoney(closingCash),
                profitMargin: roundMoney(profitMargin),
                cashStatus
            }));

            cash = closingCash;
            period = nextMonth(period);
        }

        return Object.freeze({
            forecastId: crypto.randomUUID(),
            sourceRevision: snapshot.revision,
            scenario,
            generatedAt: new Date().toISOString(),
            results: Object.freeze(results)
        });
    }
}

class FinancialAnalytics {
    static summarize(forecast) {
        const rows = forecast.results;

        if (!rows.length) {
            throw new InsufficientDataError("Forecast is empty.");
        }

        const sum = key => rows.reduce(
            (total, row) => total + row[key],
            0
        );

        return Object.freeze({
            scenario: forecast.scenario,
            periods: rows.length,
            revenue: roundMoney(sum("revenue")),
            operatingExpenses: roundMoney(
                sum("operatingExpenses")
            ),
            operatingProfit: roundMoney(
                sum("operatingProfit")
            ),
            endingCash: rows[rows.length - 1].closingCash,
            averageProfitMargin: roundMoney(
                rows.reduce((total, row) => (
                    total + row.profitMargin
                ), 0) / rows.length
            ),
            negativeCashPeriods: rows.filter(
                row => row.closingCash < 0
            ).length
        });
    }

    static compareBudget(actual, budget) {
        validateMoney(actual, "Actual");
        validateMoney(budget, "Budget");

        const variance = actual - budget;

        return Object.freeze({
            actual,
            budget,
            variance: roundMoney(variance),
            variancePercentage: budget === 0
                ? null
                : roundMoney(variance / Math.abs(budget) * 100),
            favorable: variance >= 0
        });
    }
}

class AuditLog extends EventEmitter {
    constructor(repository) {
        super();

        repository.on("recordAdded", event => {
            const auditEvent = Object.freeze({
                type: "FINANCIAL_RECORD_ADDED",
                ...event,
                timestamp: new Date().toISOString()
            });

            this.emit("audit", auditEvent);
        });
    }
}

function toCsv(results) {
    const fields = [
        "period",
        "scenario",
        "revenue",
        "operatingExpenses",
        "investingExpenses",
        "operatingProfit",
        "netCashFlow",
        "openingCash",
        "closingCash",
        "profitMargin",
        "cashStatus"
    ];

    const escape = value => {
        const text = String(value);

        return /[",\n]/.test(text)
            ? `"${text.replace(/"/g, '""')}"`
            : text;
    };

    return [
        fields.join(","),
        ...results.map(row => (
            fields.map(field => escape(row[field])).join(",")
        ))
    ].join("\n") + "\n";
}

function createSampleRepository() {
    const repository = new FinancialRepository();

    const data = [
        ["2026-01", 850000, 520000, 65000, 20000, 300000],
        ["2026-02", 875000, 530000, 70000, 0, 595000],
        ["2026-03", 900000, 540000, 60000, -10000, 870000],
        ["2026-04", 925000, 555000, 75000, 15000, 1155000],
        ["2026-05", 960000, 565000, 80000, 0, 1465000],
        ["2026-06", 990000, 580000, 70000, 10000, 1780000]
    ];

    for (const row of data) {
        repository.add(new FinancialRecord({
            period: row[0],
            revenue: row[1],
            operatingExpenses: row[2],
            investingExpenses: row[3],
            financingCashFlow: row[4],
            openingCash: row[5]
        }));
    }

    return repository;
}

async function runTests() {
    const repository = createSampleRepository();

    const engine = new ForecastEngine(repository, {
        horizon: 6,
        window: 3
    });

    const [base, optimistic, pessimistic] = await Promise.all([
        engine.run(Scenario.BASE),
        engine.run(Scenario.OPTIMISTIC),
        engine.run(Scenario.PESSIMISTIC)
    ]);

    if (
        optimistic.results[0].revenue <=
        base.results[0].revenue
    ) {
        throw new Error("Optimistic scenario validation failed.");
    }

    if (
        pessimistic.results[0].revenue >=
        base.results[0].revenue
    ) {
        throw new Error("Pessimistic scenario validation failed.");
    }

    if (base.results.length !== 6) {
        throw new Error("Forecast horizon validation failed.");
    }

    const variance = FinancialAnalytics.compareBudget(
        950,
        1000
    );

    if (variance.variance !== -50) {
        throw new Error("Budget variance test failed.");
    }

    const invalid = () => new FinancialRecord({
        period: "2026-13",
        revenue: 100,
        operatingExpenses: 50,
        investingExpenses: 10,
        openingCash: 100
    });

    try {
        invalid();
        throw new Error("Invalid period was accepted.");
    } catch (error) {
        if (!(error instanceof ValidationError)) {
            throw error;
        }
    }

    return { base, optimistic, pessimistic };
}

async function main() {
    const repository = createSampleRepository();
    const audit = new AuditLog(repository);

    audit.on("audit", event => {
        console.log("AUDIT:", JSON.stringify(event));
    });

    const engine = new ForecastEngine(repository, {
        horizon: 6,
        window: 3,
        scenarioPolicy: new ScenarioPolicy({
            optimisticRevenueAdjustment: 0.05,
            pessimisticRevenueAdjustment: -0.05,
            expenseAdjustment: 0.02
        })
    });

    const scenarios = {};

    for (const scenario of Object.values(Scenario)) {
        const forecast = await engine.run(scenario);

        scenarios[scenario] = FinancialAnalytics.summarize(
            forecast
        );

        console.log(`\n${scenario} FORECAST`);

        for (const row of forecast.results) {
            console.log(
                row.period,
                "Revenue:", row.revenue.toLocaleString("en-IN"),
                "Profit:", row.operatingProfit.toLocaleString("en-IN"),
                "Closing cash:", row.closingCash.toLocaleString("en-IN"),
                "Status:", row.cashStatus
            );
        }

        if (scenario === Scenario.BASE) {
            await fs.writeFile(
                "financial_forecast.csv",
                toCsv(forecast.results),
                "utf8"
            );
        }
    }

    console.log("\nSCENARIO COMPARISON");
    console.log(JSON.stringify(scenarios, null, 2));

    await runTests();

    console.log("\nAll financial forecasting tests passed.");
    console.log("Exported financial_forecast.csv");
}

main().catch(error => {
    console.error("Forecasting failure:", error.message);
    process.exitCode = 1;
});
