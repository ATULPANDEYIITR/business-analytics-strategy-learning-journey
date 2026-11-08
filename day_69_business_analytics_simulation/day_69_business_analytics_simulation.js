"use strict";

/**
 * Business Analytics Automation
 * Node.js 18+
 *
 * Features:
 * - Asynchronous CSV ingestion
 * - Data validation and duplicate detection
 * - KPI calculations
 * - Regional and product segmentation
 * - Periodic aggregation
 * - Moving averages
 * - Revenue anomaly detection
 * - JSON and CSV report generation
 * - Event-driven job monitoring
 *
 * No third-party packages required.
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");
const { randomUUID } = require("node:crypto");

const ROOT = __dirname;
const INPUT = path.join(ROOT, "sales_data.csv");
const OUTPUT = path.join(ROOT, "analytics_output");

const Status = Object.freeze({
    PENDING: "PENDING",
    RUNNING: "RUNNING",
    COMPLETED: "COMPLETED",
    FAILED: "FAILED"
});

class AnalyticsError extends Error {
    constructor(message, code = "ANALYTICS_ERROR") {
        super(message);
        this.name = "AnalyticsError";
        this.code = code;
    }
}

class SalesTransaction {
    constructor(data) {
        const required = [
            "transaction_id",
            "transaction_date",
            "region",
            "product",
            "category",
            "quantity",
            "unit_price",
            "cost_per_unit"
        ];

        for (const field of required) {
            if (
                data[field] === undefined ||
                data[field] === null ||
                String(data[field]).trim() === ""
            ) {
                throw new AnalyticsError(
                    `Missing field: ${field}`,
                    "INVALID_RECORD"
                );
            }
        }

        const date = new Date(`${data.transaction_date}T00:00:00Z`);

        if (
            !Number.isFinite(date.getTime()) ||
            date.toISOString().slice(0, 10) !== data.transaction_date
        ) {
            throw new AnalyticsError("Invalid transaction date.");
        }

        const quantity = Number(data.quantity);
        const price = Number(data.unit_price);
        const cost = Number(data.cost_per_unit);

        if (
            !Number.isSafeInteger(quantity) ||
            quantity < 0 ||
            !Number.isFinite(price) ||
            !Number.isFinite(cost) ||
            price < 0 ||
            cost < 0
        ) {
            throw new AnalyticsError("Invalid numerical values.");
        }

        if (quantity > 0 && price === 0) {
            throw new AnalyticsError("Positive quantity requires a price.");
        }

        this.id = String(data.transaction_id).trim();
        this.date = data.transaction_date;
        this.region = String(data.region).trim();
        this.product = String(data.product).trim();
        this.category = String(data.category).trim();
        this.quantity = quantity;
        this.unitPrice = price;
        this.unitCost = cost;

        if (!this.id || !this.region || !this.product || !this.category) {
            throw new AnalyticsError("Empty business dimension.");
        }

        Object.freeze(this);
    }

    get revenue() {
        return this.quantity * this.unitPrice;
    }

    get cost() {
        return this.quantity * this.unitCost;
    }

    get profit() {
        return this.revenue - this.cost;
    }
}

class CSVParser {
    /**
     * Parses CSV records while respecting quoted commas,
     * escaped quotation marks and embedded newlines.
     */
    static parse(content) {
        const rows = [];
        let row = [];
        let field = "";
        let quoted = false;

        for (let i = 0; i < content.length; i++) {
            const char = content[i];

            if (quoted) {
                if (char === '"' && content[i + 1] === '"') {
                    field += '"';
                    i++;
                } else if (char === '"') {
                    quoted = false;
                } else {
                    field += char;
                }
            } else if (char === '"') {
                if (field.length !== 0) {
                    throw new AnalyticsError("Invalid CSV quote position.");
                }
                quoted = true;
            } else if (char === ",") {
                row.push(field);
                field = "";
            } else if (char === "\n") {
                row.push(field);
                rows.push(row);
                row = [];
                field = "";
            } else if (char !== "\r") {
                field += char;
            }
        }

        if (quoted) {
            throw new AnalyticsError("Unclosed CSV quotation.");
        }

        if (field.length > 0 || row.length > 0) {
            row.push(field);
            rows.push(row);
        }

        if (rows.length < 2) {
            throw new AnalyticsError("CSV contains no data rows.");
        }

        const headers = rows.shift().map(h => h.trim());

        if (new Set(headers).size !== headers.length) {
            throw new AnalyticsError("Duplicate CSV column names.");
        }

        return rows
            .filter(values => values.some(v => v.trim() !== ""))
            .map(values => {
                if (values.length !== headers.length) {
                    throw new AnalyticsError("CSV column count mismatch.");
                }

                return Object.fromEntries(
                    headers.map((header, index) => [
                        header,
                        values[index]
                    ])
                );
            });
    }
}

class AnalyticsJob extends EventEmitter {
    #status = Status.PENDING;
    #transactions = [];
    #quality = {
        accepted: 0,
        rejected: 0,
        duplicates: 0
    };

    constructor(options = {}) {
        super();

        this.id = randomUUID();
        this.input = options.input || INPUT;
        this.output = options.output || OUTPUT;
        this.threshold = options.threshold ?? 2;

        if (!Number.isFinite(this.threshold) || this.threshold <= 0) {
            throw new AnalyticsError("Threshold must be positive.");
        }
    }

    get status() {
        return this.#status;
    }

    transition(next) {
        const allowed = {
            [Status.PENDING]: [Status.RUNNING],
            [Status.RUNNING]: [Status.COMPLETED, Status.FAILED],
            [Status.COMPLETED]: [],
            [Status.FAILED]: []
        };

        if (!allowed[this.#status].includes(next)) {
            throw new AnalyticsError(
                `Invalid transition: ${this.#status} -> ${next}`
            );
        }

        const previous = this.#status;
        this.#status = next;

        this.emit("status", {
            jobId: this.id,
            previous,
            current: next,
            timestamp: new Date().toISOString()
        });
    }

    async load() {
        const content = await fs.readFile(this.input, "utf8");
        const rows = CSVParser.parse(content);
        const seen = new Set();

        for (let index = 0; index < rows.length; index++) {
            try {
                const transaction = new SalesTransaction(rows[index]);

                if (seen.has(transaction.id)) {
                    this.#quality.duplicates++;
                    this.#quality.rejected++;
                    continue;
                }

                seen.add(transaction.id);
                this.#transactions.push(transaction);
                this.#quality.accepted++;
            } catch (error) {
                this.#quality.rejected++;
                this.emit("recordRejected", {
                    row: index + 2,
                    message: error.message
                });
            }
        }

        if (this.#transactions.length === 0) {
            throw new AnalyticsError("No valid transactions available.");
        }

        this.emit("dataLoaded", {
            count: this.#transactions.length,
            quality: { ...this.#quality }
        });
    }

    static aggregate(transactions) {
        const revenue = transactions.reduce(
            (sum, item) => sum + item.revenue, 0
        );

        const cost = transactions.reduce(
            (sum, item) => sum + item.cost, 0
        );

        const profit = revenue - cost;

        return {
            transactions: transactions.length,
            units: transactions.reduce(
                (sum, item) => sum + item.quantity, 0
            ),
            revenue: Number(revenue.toFixed(2)),
            cost: Number(cost.toFixed(2)),
            profit: Number(profit.toFixed(2)),
            marginPercent: Number(
                (revenue ? profit / revenue * 100 : 0).toFixed(2)
            )
        };
    }

    groupBy(selector) {
        const groups = new Map();

        for (const transaction of this.#transactions) {
            const key = selector(transaction);

            if (!groups.has(key)) {
                groups.set(key, []);
            }

            groups.get(key).push(transaction);
        }

        return Object.fromEntries(
            [...groups.entries()]
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([key, items]) => [
                    key,
                    AnalyticsJob.aggregate(items)
                ])
        );
    }

    calculateMovingAverage(windowSize = 3) {
        if (
            !Number.isInteger(windowSize) ||
            windowSize < 1
        ) {
            throw new AnalyticsError("Invalid moving average window.");
        }

        const monthly = new Map();

        for (const transaction of this.#transactions) {
            const month = transaction.date.slice(0, 7);
            monthly.set(
                month,
                (monthly.get(month) || 0) + transaction.revenue
            );
        }

        const periods = [...monthly.entries()].sort(
            ([a], [b]) => a.localeCompare(b)
        );

        return periods.map(([month, revenue], index) => {
            const start = Math.max(0, index - windowSize + 1);
            const window = periods.slice(start, index + 1);
            const average = window.reduce(
                (sum, item) => sum + item[1], 0
            ) / window.length;

            return {
                month,
                revenue: Number(revenue.toFixed(2)),
                movingAverage: Number(average.toFixed(2))
            };
        });
    }

    detectAnomalies() {
        const revenues = this.#transactions.map(t => t.revenue);
        const mean = revenues.reduce((a, b) => a + b, 0) / revenues.length;

        const variance = revenues.reduce(
            (sum, value) => sum + (value - mean) ** 2, 0
        ) / revenues.length;

        const deviation = Math.sqrt(variance);

        if (deviation === 0 || revenues.length < 3) {
            return [];
        }

        return this.#transactions
            .map(transaction => ({
                transactionId: transaction.id,
                region: transaction.region,
                revenue: transaction.revenue,
                zScore: (transaction.revenue - mean) / deviation
            }))
            .filter(item => Math.abs(item.zScore) >= this.threshold)
            .map(item => ({
                ...item,
                zScore: Number(item.zScore.toFixed(3))
            }));
    }

    buildReport() {
        const summary = AnalyticsJob.aggregate(this.#transactions);

        return {
            jobId: this.id,
            generatedAt: new Date().toISOString(),
            status: Status.COMPLETED,
            summary: {
                ...summary,
                averageTransactionValue: Number(
                    (summary.revenue / summary.transactions).toFixed(2)
                )
            },
            regions: this.groupBy(t => t.region),
            products: this.groupBy(t => t.product),
            categories: this.groupBy(t => t.category),
            monthly: this.groupBy(t => t.date.slice(0, 7)),
            movingAverages: this.calculateMovingAverage(3),
            anomalies: this.detectAnomalies(),
            dataQuality: { ...this.#quality }
        };
    }

    async save(report) {
        await fs.mkdir(this.output, { recursive: true });

        const json = JSON.stringify(report, null, 2);
        const destination = path.join(this.output, "business_report.json");
        const temporary = `${destination}.${this.id}.tmp`;

        try {
            // Write to a temporary file before replacing the report.
            await fs.writeFile(temporary, json, {
                encoding: "utf8",
                flag: "wx"
            });

            await fs.rename(temporary, destination);
        } catch (error) {
            await fs.rm(temporary, { force: true }).catch(() => {});
            throw error;
        }

        const lines = [
            "REGION,TRANSACTIONS,UNITS,REVENUE,COST,PROFIT,MARGIN_PERCENT"
        ];

        for (const [region, metrics] of Object.entries(report.regions)) {
            lines.push([
                region,
                metrics.transactions,
                metrics.units,
                metrics.revenue,
                metrics.cost,
                metrics.profit,
                metrics.marginPercent
            ].map(CSVParser.escape).join(","));
        }

        await fs.writeFile(
            path.join(this.output, "regional_report.csv"),
            lines.join("\n") + "\n",
            "utf8"
        );
    }

    async run() {
        this.transition(Status.RUNNING);

        try {
            await this.load();
            const report = this.buildReport();
            await this.save(report);
            this.transition(Status.COMPLETED);
            this.emit("completed", report);
            return report;
        } catch (error) {
            this.transition(Status.FAILED);
            this.emit("failed", error);
            throw error;
        }
    }
}

CSVParser.escape = function (value) {
    const text = String(value);

    return /[",\r\n]/.test(text)
        ? `"${text.replaceAll('"', '""')}"`
        : text;
};

async function createSampleData(file) {
    try {
        await fs.access(file);
        return;
    } catch {
        // Create the dataset only when it does not exist.
    }

    const rows = [
        ["T001", "2026-01-05", "North", "Laptop", "Electronics", 3, 75000, 60000],
        ["T002", "2026-01-08", "South", "Phone", "Electronics", 8, 25000, 18000],
        ["T003", "2026-01-12", "East", "Desk", "Furniture", 5, 12000, 8000],
        ["T004", "2026-02-03", "West", "Laptop", "Electronics", 4, 75000, 60000],
        ["T005", "2026-02-09", "North", "Chair", "Furniture", 10, 5000, 3000],
        ["T006", "2026-02-15", "South", "Phone", "Electronics", 12, 25000, 18000],
        ["T007", "2026-03-02", "East", "Desk", "Furniture", 7, 12000, 8000],
        ["T008", "2026-03-10", "West", "Laptop", "Electronics", 2, 75000, 60000],
        ["T009", "2026-03-18", "North", "Phone", "Electronics", 15, 25000, 18000],
        ["T010", "2026-03-22", "South", "Chair", "Furniture", 9, 5000, 3000],
        ["T011", "2026-04-04", "East", "Laptop", "Electronics", 30, 75000, 60000],
        ["T012", "2026-04-12", "West", "Desk", "Furniture", 6, 12000, 8000]
    ];

    const header = [
        "transaction_id", "transaction_date", "region",
        "product", "category", "quantity", "unit_price", "cost_per_unit"
    ];

    const content = [
        header,
        ...rows
    ].map(row => row.map(CSVParser.escape).join(",")).join("\n");

    await fs.mkdir(path.dirname(file), { recursive: true });
    await fs.writeFile(file, content + "\n", "utf8");
}

async function main() {
    const input = process.argv[2] || INPUT;
    const output = process.argv[3] || OUTPUT;

    await createSampleData(input);

    const job = new AnalyticsJob({
        input,
        output,
        threshold: 2
    });

    job.on("status", event => {
        console.log(
            `[STATUS] ${event.previous} -> ${event.current}`
        );
    });

    job.on("dataLoaded", event => {
        console.log(`[DATA] ${event.count} accepted records`);
    });

    job.on("recordRejected", event => {
        console.error(
            `[VALIDATION] Row ${event.row}: ${event.message}`
        );
    });

    job.on("completed", report => {
        console.log("\nBUSINESS ANALYTICS REPORT");
        console.log("=========================");
        console.log(report.summary);
        console.log("Regional performance:", report.regions);
        console.log("Moving averages:", report.movingAverages);
        console.log("Anomalies:", report.anomalies.length);
        console.log(`Reports saved to: ${output}`);
    });

    job.on("failed", error => {
        console.error("[JOB FAILED]", error.message);
    });

    await job.run();
}

if (require.main === module) {
    main().catch(error => {
        console.error(error.stack || error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    AnalyticsJob,
    AnalyticsError,
    SalesTransaction,
    CSVParser
};
