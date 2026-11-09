"use strict";

/*
 * BUSINESS ANALYTICS EVENT ENGINE
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 *
 * Features:
 * - Event-driven transaction processing
 * - Streaming KPI calculation
 * - Regional and product analytics
 * - Customer behavior monitoring
 * - Revenue anomaly detection
 * - Business policy evaluation
 * - Asynchronous report generation
 * - JSON report persistence
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class Transaction {
    constructor(data) {
        this.id = String(data.id ?? "").trim();
        this.date = new Date(data.date);
        this.customerId = String(data.customerId ?? "").trim();
        this.productId = String(data.productId ?? "").trim();
        this.category = String(data.category ?? "").trim();
        this.region = String(data.region ?? "").trim();
        this.quantity = Number(data.quantity);
        this.unitPrice = Number(data.unitPrice);
        this.unitCost = Number(data.unitCost);

        this.validate();
        Object.freeze(this);
    }

    validate() {
        if (!this.id || !this.customerId || !this.productId) {
            throw new ValidationError("Transaction identifiers are required.");
        }

        if (Number.isNaN(this.date.getTime())) {
            throw new ValidationError("Invalid transaction date.");
        }

        if (
            !this.category ||
            !this.region ||
            !Number.isSafeInteger(this.quantity) ||
            this.quantity <= 0
        ) {
            throw new ValidationError("Invalid transaction dimensions.");
        }

        if (
            !Number.isFinite(this.unitPrice) ||
            !Number.isFinite(this.unitCost) ||
            this.unitPrice <= 0 ||
            this.unitCost < 0 ||
            this.unitCost > this.unitPrice
        ) {
            throw new ValidationError("Invalid transaction pricing.");
        }
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

class BusinessPolicy {
    constructor({
        minimumMargin = 20,
        minimumRepeatRate = 30,
        anomalyThreshold = 1.5
    } = {}) {
        this.minimumMargin = minimumMargin;
        this.minimumRepeatRate = minimumRepeatRate;
        this.anomalyThreshold = anomalyThreshold;

        for (const value of Object.values({
            minimumMargin,
            minimumRepeatRate,
            anomalyThreshold
        })) {
            if (!Number.isFinite(value) || value < 0) {
                throw new ValidationError("Invalid business policy.");
            }
        }
    }

    evaluate(metrics, anomalies) {
        const findings = [];

        if (metrics.marginPercent < this.minimumMargin) {
            findings.push({
                severity: "HIGH",
                type: "LOW_GROSS_MARGIN",
                message: "Gross margin is below the configured threshold."
            });
        }

        if (metrics.repeatRate < this.minimumRepeatRate) {
            findings.push({
                severity: "MEDIUM",
                type: "CUSTOMER_RETENTION",
                message: "Repeat customer rate requires attention."
            });
        }

        for (const anomaly of anomalies) {
            findings.push({
                severity: "HIGH",
                type: "REVENUE_ANOMALY",
                message: `Unusual revenue detected for ${anomaly.month}.`
            });
        }

        return findings;
    }
}

class AnalyticsEngine extends EventEmitter {
    constructor(policy = new BusinessPolicy()) {
        super();

        this.policy = policy;
        this.transactions = new Map();
        this.products = new Map();
        this.regions = new Map();
        this.customers = new Map();
        this.monthly = new Map();

        this.totalRevenue = 0;
        this.totalCost = 0;
        this.totalUnits = 0;
    }

    addTransaction(transactionData) {
        const transaction = new Transaction(transactionData);

        if (this.transactions.has(transaction.id)) {
            throw new ValidationError(
                `Duplicate transaction: ${transaction.id}`
            );
        }

        this.transactions.set(transaction.id, transaction);

        this.totalRevenue += transaction.revenue;
        this.totalCost += transaction.cost;
        this.totalUnits += transaction.quantity;

        this.updateDimension(
            this.products,
            transaction.productId,
            transaction
        );

        this.updateDimension(
            this.regions,
            transaction.region,
            transaction
        );

        this.updateCustomer(transaction);
        this.updateMonthly(transaction);

        this.emit("transaction:processed", {
            id: transaction.id,
            revenue: transaction.revenue
        });

        return transaction;
    }

    updateDimension(map, key, transaction) {
        if (!map.has(key)) {
            map.set(key, {
                revenue: 0,
                profit: 0,
                units: 0,
                transactions: 0
            });
        }

        const value = map.get(key);

        value.revenue += transaction.revenue;
        value.profit += transaction.profit;
        value.units += transaction.quantity;
        value.transactions++;
    }

    updateCustomer(transaction) {
        if (!this.customers.has(transaction.customerId)) {
            this.customers.set(transaction.customerId, {
                frequency: 0,
                monetaryValue: 0,
                lastPurchase: transaction.date
            });
        }

        const customer = this.customers.get(transaction.customerId);

        customer.frequency++;
        customer.monetaryValue += transaction.revenue;

        if (transaction.date > customer.lastPurchase) {
            customer.lastPurchase = transaction.date;
        }
    }

    updateMonthly(transaction) {
        const month = transaction.date.toISOString().slice(0, 7);

        if (!this.monthly.has(month)) {
            this.monthly.set(month, {
                revenue: 0,
                profit: 0,
                transactions: 0
            });
        }

        const entry = this.monthly.get(month);

        entry.revenue += transaction.revenue;
        entry.profit += transaction.profit;
        entry.transactions++;
    }

    calculateKPIs() {
        const count = this.transactions.size;
        const profit = this.totalRevenue - this.totalCost;

        let repeatCustomers = 0;

        for (const customer of this.customers.values()) {
            if (customer.frequency > 1) {
                repeatCustomers++;
            }
        }

        const customerCount = this.customers.size;

        return {
            transactionCount: count,
            totalRevenue: this.totalRevenue,
            totalCost: this.totalCost,
            grossProfit: profit,
            marginPercent: this.totalRevenue
                ? profit / this.totalRevenue * 100
                : 0,
            averageOrderValue: count
                ? this.totalRevenue / count
                : 0,
            totalUnits: this.totalUnits,
            customerCount,
            repeatCustomers,
            repeatRate: customerCount
                ? repeatCustomers / customerCount * 100
                : 0
        };
    }

    analyzeCustomers() {
        const referenceDate = new Date(
            Math.max(
                ...Array.from(
                    this.customers.values(),
                    customer => customer.lastPurchase.getTime()
                )
            )
        );

        const segments = {
            "High Value": [],
            "Regular": [],
            "Occasional": [],
            "At Risk": []
        };

        for (const [id, customer] of this.customers) {
            const recency = Math.floor(
                (referenceDate - customer.lastPurchase) / 86400000
            );

            let segment;

            if (
                customer.frequency >= 5 &&
                customer.monetaryValue >= 50000 &&
                recency <= 90
            ) {
                segment = "High Value";
            } else if (
                customer.frequency >= 3 &&
                recency <= 180
            ) {
                segment = "Regular";
            } else if (recency > 180) {
                segment = "At Risk";
            } else {
                segment = "Occasional";
            }

            segments[segment].push({
                customerId: id,
                frequency: customer.frequency,
                monetaryValue: customer.monetaryValue,
                recencyDays: recency
            });
        }

        return segments;
    }

    analyzeMonthlyRevenue() {
        const months = Array.from(this.monthly.entries())
            .sort(([a], [b]) => a.localeCompare(b));

        const values = months.map(([month, data]) => ({
            month,
            ...data
        }));

        if (values.length < 4) {
            return {
                monthly: values,
                anomalies: [],
                forecast: null
            };
        }

        const revenues = values.map(item => item.revenue);

        const mean = revenues.reduce((a, b) => a + b, 0)
            / revenues.length;

        const variance = revenues.reduce(
            (sum, value) => sum + (value - mean) ** 2,
            0
        ) / revenues.length;

        const deviation = Math.sqrt(variance);

        const anomalies = deviation === 0
            ? []
            : values.filter(
                item =>
                    (item.revenue - mean) / deviation < -this.policy.anomalyThreshold
            );

        const n = revenues.length;
        const xMean = (n - 1) / 2;
        const yMean = mean;

        let numerator = 0;
        let denominator = 0;

        for (let i = 0; i < n; i++) {
            numerator += (i - xMean) * (revenues[i] - yMean);
            denominator += (i - xMean) ** 2;
        }

        const slope = denominator
            ? numerator / denominator
            : 0;

        const forecast = Math.max(
            0,
            yMean + slope * (n - xMean)
        );

        return {
            monthly: values,
            anomalies: anomalies.map(item => ({
                month: item.month,
                revenue: item.revenue
            })),
            forecast: {
                method: "Ordinary Least Squares",
                nextPeriodRevenue: Number(forecast.toFixed(2)),
                slope: Number(slope.toFixed(2))
            }
        };
    }

    generateReport() {
        if (!this.transactions.size) {
            throw new ValidationError(
                "Cannot generate a report without transactions."
            );
        }

        const kpis = this.calculateKPIs();
        const monthly = this.analyzeMonthlyRevenue();

        const findings = this.policy.evaluate(
            kpis,
            monthly.anomalies
        );

        const report = {
            generatedAt: new Date().toISOString(),
            currency: "INR",
            kpis,
            productPerformance: Object.fromEntries(this.products),
            regionalPerformance: Object.fromEntries(this.regions),
            customerSegments: this.analyzeCustomers(),
            monthlyAnalysis: monthly,
            policyFindings: findings
        };

        this.emit("report:generated", {
            transactions: kpis.transactionCount,
            findings: findings.length
        });

        return report;
    }
}

function createSampleTransactions() {
    const products = [
        {
            id: "P001",
            category: "Electronics",
            price: 25000,
            cost: 18000
        },
        {
            id: "P002",
            category: "Furniture",
            price: 18000,
            cost: 12000
        },
        {
            id: "P003",
            category: "Clothing",
            price: 2500,
            cost: 1200
        },
        {
            id: "P004",
            category: "Groceries",
            price: 900,
            cost: 650
        }
    ];

    const regions = ["North", "South", "East", "West", "Central"];
    const records = [];

    for (let i = 1; i <= 300; i++) {
        const product = products[i % products.length];
        const month = String((Math.floor((i - 1) / 25) % 12) + 1)
            .padStart(2, "0");

        records.push({
            id: `TXN${String(i).padStart(5, "0")}`,
            date: `2025-${month}-${String((i % 28) + 1).padStart(2, "0")}`,
            customerId: `C${String((i % 80) + 1).padStart(4, "0")}`,
            productId: product.id,
            category: product.category,
            region: regions[i % regions.length],
            quantity: (i % 5) + 1,
            unitPrice: product.price,
            unitCost: product.cost
        });
    }

    return records;
}

async function main() {
    const engine = new AnalyticsEngine();

    engine.on("transaction:processed", event => {
        if (event.id.endsWith("00001")) {
            console.log("First transaction processed:", event);
        }
    });

    engine.on("report:generated", event => {
        console.log("Report generation event:", event);
    });

    const records = createSampleTransactions();

    // Process in bounded batches to avoid building large temporary arrays.
    const batchSize = 50;

    for (let start = 0; start < records.length; start += batchSize) {
        const batch = records.slice(start, start + batchSize);

        await Promise.all(
            batch.map(async record => {
                engine.addTransaction(record);
            })
        );
    }

    const report = engine.generateReport();

    const outputDirectory = path.join(process.cwd(), "output");

    await fs.mkdir(outputDirectory, { recursive: true });

    const reportPath = path.join(
        outputDirectory,
        "javascript_business_report.json"
    );

    await fs.writeFile(
        reportPath,
        JSON.stringify(report, null, 2),
        { encoding: "utf8", flag: "w" }
    );

    console.log("\nBUSINESS ANALYTICS RESULTS");
    console.log("==========================");
    console.log(
        "Revenue:",
        report.kpis.totalRevenue.toFixed(2),
        "INR"
    );
    console.log(
        "Gross Profit:",
        report.kpis.grossProfit.toFixed(2),
        "INR"
    );
    console.log(
        "Gross Margin:",
        report.kpis.marginPercent.toFixed(2),
        "%"
    );
    console.log(
        "Customers:",
        report.kpis.customerCount
    );
    console.log(
        "Repeat Rate:",
        report.kpis.repeatRate.toFixed(2),
        "%"
    );

    console.log("\nPolicy Findings:");

    for (const finding of report.policyFindings) {
        console.log(
            `[${finding.severity}] ${finding.type}: ${finding.message}`
        );
    }

    console.log(`\nReport saved to: ${reportPath}`);
}

async function runTests() {
    const engine = new AnalyticsEngine();

    const transaction = {
        id: "TEST001",
        date: "2025-01-01",
        customerId: "C001",
        productId: "P001",
        category: "Electronics",
        region: "North",
        quantity: 2,
        unitPrice: 1000,
        unitCost: 600
    };

    engine.addTransaction(transaction);

    const metrics = engine.calculateKPIs();

    if (metrics.totalRevenue !== 2000) {
        throw new Error("Revenue validation failed.");
    }

    if (metrics.grossProfit !== 800) {
        throw new Error("Profit validation failed.");
    }

    let duplicateRejected = false;

    try {
        engine.addTransaction(transaction);
    } catch (error) {
        duplicateRejected = error instanceof ValidationError;
    }

    if (!duplicateRejected) {
        throw new Error("Duplicate transaction validation failed.");
    }

    console.log("All JavaScript validation tests passed.");
}

if (require.main === module) {
    (async () => {
        try {
            await runTests();
            await main();
        } catch (error) {
            console.error("Business analytics failure:", error.message);
            process.exitCode = 1;
        }
    })();
}

module.exports = {
    Transaction,
    BusinessPolicy,
    AnalyticsEngine,
    ValidationError
};
