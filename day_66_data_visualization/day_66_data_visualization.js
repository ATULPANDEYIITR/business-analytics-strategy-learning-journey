"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { EventEmitter } = require("node:events");

const OUTPUT_DIR = path.resolve("business_reports_js");

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class PerformanceDataset {
    #records = new Map();

    constructor(records) {
        if (!Array.isArray(records) || records.length === 0) {
            throw new ValidationError("Dataset must contain records.");
        }

        for (const record of records) {
            this.add(record);
        }
    }

    add(record) {
        const required = [
            "month",
            "revenue",
            "expenses",
            "orders",
            "customers",
            "target"
        ];

        for (const key of required) {
            if (!(key in record)) {
                throw new ValidationError(`Missing field: ${key}`);
            }
        }

        if (typeof record.month !== "string" || !record.month.trim()) {
            throw new ValidationError("Invalid month.");
        }

        for (const field of ["revenue", "expenses", "orders", "customers", "target"]) {
            if (!Number.isFinite(record[field])) {
                throw new ValidationError(`Invalid numeric value: ${field}`);
            }
        }

        if (
            record.revenue < 0 ||
            record.expenses < 0 ||
            record.orders < 0 ||
            record.customers < 0 ||
            record.target <= 0
        ) {
            throw new ValidationError("Negative values or invalid target.");
        }

        if (record.customers > record.orders && record.orders > 0) {
            throw new ValidationError("Customers cannot exceed orders.");
        }

        if (this.#records.has(record.month)) {
            throw new ValidationError(`Duplicate month: ${record.month}`);
        }

        this.#records.set(record.month, Object.freeze({ ...record }));
    }

    get records() {
        return [...this.#records.values()];
    }

    getMetrics() {
        return this.records.map(record => {
            const profit = record.revenue - record.expenses;

            return {
                ...record,
                profit,
                margin: record.revenue
                    ? profit / record.revenue * 100
                    : 0,
                targetAchievement: record.revenue / record.target * 100,
                expenseRatio: record.revenue
                    ? record.expenses / record.revenue * 100
                    : 0
            };
        });
    }
}

class VisualizationEngine {
    constructor(dataset, outputDirectory) {
        this.dataset = dataset;
        this.outputDirectory = outputDirectory;
        this.events = new EventEmitter();

        fs.mkdirSync(outputDirectory, { recursive: true });
    }

    async exportReport() {
        const metrics = this.dataset.getMetrics();

        const totals = metrics.reduce(
            (acc, record) => {
                acc.revenue += record.revenue;
                acc.expenses += record.expenses;
                acc.profit += record.profit;
                acc.orders += record.orders;
                acc.customers += record.customers;
                return acc;
            },
            {
                revenue: 0,
                expenses: 0,
                profit: 0,
                orders: 0,
                customers: 0
            }
        );

        const report = {
            generatedAt: new Date().toISOString(),
            currency: "INR",
            reportingPeriods: metrics.length,
            totals,
            averageMargin: totals.revenue
                ? totals.profit / totals.revenue * 100
                : 0,
            monthlyPerformance: metrics
        };

        const destination = path.join(
            this.outputDirectory,
            "business_report.json"
        );

        const temporary = `${destination}.tmp`;

        try {
            // Write to a temporary file and rename to avoid partial reports.
            await fs.promises.writeFile(
                temporary,
                JSON.stringify(report, null, 2),
                { encoding: "utf8", flag: "w" }
            );

            await fs.promises.rename(temporary, destination);

            this.events.emit("report:generated", {
                destination,
                reportingPeriods: metrics.length
            });

            return report;
        } catch (error) {
            await fs.promises.rm(temporary, { force: true }).catch(() => {});
            this.events.emit("report:error", error);
            throw new Error(`Report export failed: ${error.message}`);
        }
    }

    async createMonthlySummary() {
        const metrics = this.dataset.getMetrics();

        return metrics.map(record => ({
            month: record.month,
            revenue: record.revenue,
            expenses: record.expenses,
            profit: record.profit,
            margin: Number(record.margin.toFixed(2)),
            targetAchievement: Number(
                record.targetAchievement.toFixed(2)
            ),
            performance:
                record.targetAchievement >= 100
                    ? "TARGET_ACHIEVED"
                    : "BELOW_TARGET"
        }));
    }

    async createAnomalyReport() {
        const metrics = this.dataset.getMetrics();

        const values = metrics.map(record => record.revenue);
        const mean = values.reduce((a, b) => a + b, 0) / values.length;

        const variance = values.reduce(
            (sum, value) => sum + (value - mean) ** 2,
            0
        ) / values.length;

        const standardDeviation = Math.sqrt(variance);

        return metrics
            .filter(record => {
                // A zero standard deviation means there is no variation.
                if (standardDeviation === 0) return false;

                const zScore = Math.abs(
                    (record.revenue - mean) / standardDeviation
                );

                return zScore > 1.5;
            })
            .map(record => ({
                month: record.month,
                revenue: record.revenue,
                classification: "UNUSUAL_REVENUE"
            }));
    }

    async calculateMovingAverage(windowSize = 3) {
        const metrics = this.dataset.getMetrics();

        if (
            !Number.isInteger(windowSize) ||
            windowSize < 1 ||
            windowSize > metrics.length
        ) {
            throw new ValidationError("Invalid moving-average window.");
        }

        const result = [];

        for (let i = 0; i < metrics.length; i++) {
            if (i + 1 < windowSize) continue;

            const window = metrics.slice(
                i - windowSize + 1,
                i + 1
            );

            const average = window.reduce(
                (sum, item) => sum + item.revenue,
                0
            ) / windowSize;

            result.push({
                month: metrics[i].month,
                movingAverage: Number(average.toFixed(2))
            });
        }

        return result;
    }
}

class DashboardController {
    constructor(engine) {
        this.engine = engine;
        this.state = "IDLE";

        this.engine.events.on("report:generated", event => {
            this.state = "COMPLETED";
            process.stdout.write(
                `Report generated: ${event.destination}\n`
            );
        });

        this.engine.events.on("report:error", error => {
            this.state = "FAILED";
            process.stderr.write(`${error.message}\n`);
        });
    }

    async execute() {
        if (this.state === "RUNNING") {
            throw new Error("A report operation is already running.");
        }

        this.state = "RUNNING";

        try {
            const [report, summary, anomalies, movingAverage] =
                await Promise.all([
                    this.engine.exportReport(),
                    this.engine.createMonthlySummary(),
                    this.engine.createAnomalyReport(),
                    this.engine.calculateMovingAverage(3)
                ]);

            this.state = "COMPLETED";

            return {
                report,
                summary,
                anomalies,
                movingAverage
            };
        } catch (error) {
            this.state = "FAILED";
            throw error;
        }
    }
}

async function main() {
    const records = [
        { month: "January", revenue: 450000, expenses: 310000, orders: 420, customers: 350, target: 430000 },
        { month: "February", revenue: 480000, expenses: 325000, orders: 450, customers: 370, target: 450000 },
        { month: "March", revenue: 520000, expenses: 340000, orders: 490, customers: 395, target: 500000 },
        { month: "April", revenue: 495000, expenses: 350000, orders: 465, customers: 380, target: 510000 },
        { month: "May", revenue: 560000, expenses: 365000, orders: 530, customers: 425, target: 530000 },
        { month: "June", revenue: 590000, expenses: 375000, orders: 560, customers: 445, target: 550000 },
        { month: "July", revenue: 610000, expenses: 390000, orders: 580, customers: 460, target: 580000 },
        { month: "August", revenue: 575000, expenses: 385000, orders: 550, customers: 440, target: 590000 },
        { month: "September", revenue: 650000, expenses: 405000, orders: 610, customers: 490, target: 620000 },
        { month: "October", revenue: 680000, expenses: 420000, orders: 640, customers: 510, target: 650000 },
        { month: "November", revenue: 710000, expenses: 440000, orders: 670, customers: 535, target: 680000 },
        { month: "December", revenue: 780000, expenses: 465000, orders: 740, customers: 590, target: 720000 }
    ];

    const dataset = new PerformanceDataset(records);
    const engine = new VisualizationEngine(dataset, OUTPUT_DIR);
    const dashboard = new DashboardController(engine);

    const results = await dashboard.execute();

    console.log("\nBUSINESS PERFORMANCE");
    console.table(results.summary);

    console.log("\nANOMALIES");
    console.table(results.anomalies);

    console.log("\nTHREE-MONTH MOVING AVERAGE");
    console.table(results.movingAverage);

    console.log("\nTOTALS");
    console.log(results.report.totals);
    console.log(`Dashboard state: ${dashboard.state}`);
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
