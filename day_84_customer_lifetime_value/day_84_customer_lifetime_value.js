"use strict";

/*
 * CUSTOMER LIFETIME VALUE ENGINE
 *
 * Node.js 18+
 * Implements event-driven customer accounting, discounted CLV,
 * acquisition economics, cohort retention, segmentation and
 * strategic marketing policy evaluation.
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

class DomainError extends Error {
    constructor(message) {
        super(message);
        this.name = "DomainError";
    }
}

const Segment = Object.freeze({
    HIGH_VALUE: "HIGH_VALUE",
    GROWING: "GROWING",
    STANDARD: "STANDARD",
    LOW_VALUE: "LOW_VALUE",
    UNPROFITABLE: "UNPROFITABLE"
});

function requireFiniteNonNegative(value, field) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < 0
    ) {
        throw new DomainError(`${field} must be a finite non-negative number.`);
    }
}

function validDate(value) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        throw new DomainError("Invalid date.");
    }

    return date;
}

function yearsBetween(first, last) {
    return Math.max(
        0,
        (last.getTime() - first.getTime()) /
            (365.25 * 24 * 60 * 60 * 1000)
    );
}

class Customer {
    constructor({
        id,
        acquiredAt,
        channel,
        acquisitionCost = 0
    }) {
        if (!id || !channel) {
            throw new DomainError("Customer ID and channel are required.");
        }

        requireFiniteNonNegative(acquisitionCost, "Acquisition cost");

        this.id = id;
        this.acquiredAt = validDate(acquiredAt);
        this.channel = channel;
        this.acquisitionCost = acquisitionCost;

        this.transactions = new Map();
        this.lastActivity = this.acquiredAt;
    }

    addPurchase(purchase) {
        const {
            id,
            date,
            revenue,
            variableCost
        } = purchase;

        if (!id || this.transactions.has(id)) {
            throw new DomainError("Missing or duplicate transaction ID.");
        }

        requireFiniteNonNegative(revenue, "Revenue");
        requireFiniteNonNegative(variableCost, "Variable cost");

        if (variableCost > revenue) {
            throw new DomainError("Variable cost cannot exceed revenue.");
        }

        const transactionDate = validDate(date);

        if (transactionDate < this.acquiredAt) {
            throw new DomainError("Purchase predates customer acquisition.");
        }

        const record = Object.freeze({
            id,
            date: transactionDate,
            revenue,
            variableCost,
            contribution: revenue - variableCost
        });

        this.transactions.set(id, record);

        if (transactionDate > this.lastActivity) {
            this.lastActivity = transactionDate;
        }

        return record;
    }

    get purchases() {
        return [...this.transactions.values()].sort(
            (a, b) => a.date - b.date
        );
    }

    get revenue() {
        return this.purchases.reduce((sum, item) => sum + item.revenue, 0);
    }

    get contribution() {
        return this.purchases.reduce(
            (sum, item) => sum + item.contribution,
            0
        );
    }

    get averageOrderValue() {
        const count = this.transactions.size;
        return count ? this.revenue / count : 0;
    }

    get annualPurchaseFrequency() {
        const purchases = this.purchases;

        if (purchases.length < 2) {
            return 0;
        }

        const elapsed = yearsBetween(
            purchases[0].date,
            purchases[purchases.length - 1].date
        );

        return elapsed > 0 ? purchases.length / elapsed : purchases.length;
    }
}

class CLVModel {
    constructor({
        churnRate = 0.20,
        discountRate = 0.10,
        defaultMargin = 0.60,
        maximumLifetime = 10
    } = {}) {
        if (!(churnRate > 0 && churnRate <= 1)) {
            throw new DomainError("Invalid churn rate.");
        }

        if (!(discountRate >= 0 && discountRate < 1)) {
            throw new DomainError("Invalid discount rate.");
        }

        if (!(defaultMargin >= 0 && defaultMargin <= 1)) {
            throw new DomainError("Invalid margin.");
        }

        if (!(maximumLifetime > 0)) {
            throw new DomainError("Invalid maximum lifetime.");
        }

        this.churnRate = churnRate;
        this.discountRate = discountRate;
        this.defaultMargin = defaultMargin;
        this.maximumLifetime = maximumLifetime;
    }

    classify(netCLV) {
        if (netCLV < 0) return Segment.UNPROFITABLE;
        if (netCLV >= 10000) return Segment.HIGH_VALUE;
        if (netCLV >= 5000) return Segment.GROWING;
        if (netCLV >= 1000) return Segment.STANDARD;
        return Segment.LOW_VALUE;
    }

    calculate(customer) {
        const revenue = customer.revenue;
        const contribution = customer.contribution;

        const margin = revenue > 0
            ? contribution / revenue
            : this.defaultMargin;

        const annualRevenue =
            customer.averageOrderValue *
            customer.annualPurchaseFrequency;

        const annualContribution = annualRevenue * margin;

        const lifetime = Math.min(
            this.maximumLifetime,
            1 / this.churnRate
        );

        let projectedCLV;

        if (this.discountRate === 0) {
            projectedCLV = annualContribution * lifetime;
        } else {
            projectedCLV =
                annualContribution *
                (
                    1 -
                    Math.pow(
                        1 + this.discountRate,
                        -lifetime
                    )
                ) /
                this.discountRate;
        }

        const netCLV = projectedCLV - customer.acquisitionCost;

        return Object.freeze({
            customerId: customer.id,
            revenue,
            contribution,
            acquisitionCost: customer.acquisitionCost,
            margin,
            projectedCLV,
            netCLV,
            lifetime,
            segment: this.classify(netCLV),
            confidence:
                customer.transactions.size >= 5
                    ? "HIGH"
                    : customer.transactions.size >= 2
                        ? "MEDIUM"
                        : "LOW"
        });
    }
}

class CustomerService extends EventEmitter {
    constructor(model) {
        super();

        this.model = model;
        this.customers = new Map();
        this.processedEvents = new Set();
    }

    register(customer) {
        if (this.customers.has(customer.id)) {
            throw new DomainError("Customer already registered.");
        }

        this.customers.set(customer.id, customer);

        this.emit("customer:registered", {
            customerId: customer.id,
            channel: customer.channel
        });
    }

    processPurchase(customerId, purchase, eventId) {
        if (!eventId || this.processedEvents.has(eventId)) {
            throw new DomainError("Missing or duplicate event identifier.");
        }

        const customer = this.customers.get(customerId);

        if (!customer) {
            throw new DomainError("Unknown customer.");
        }

        // Record the event only after the transaction is validated.
        const transaction = customer.addPurchase(purchase);

        this.processedEvents.add(eventId);

        const valuation = this.model.calculate(customer);

        this.emit("purchase:recorded", {
            customerId,
            transactionId: transaction.id,
            revenue: transaction.revenue
        });

        this.emit("clv:updated", valuation);

        return valuation;
    }

    portfolio() {
        return [...this.customers.values()].map(
            customer => this.model.calculate(customer)
        );
    }

    async processBatch(events, concurrency = 4) {
        if (!Array.isArray(events)) {
            throw new DomainError("Batch must be an array.");
        }

        if (!Number.isInteger(concurrency) || concurrency < 1) {
            throw new DomainError("Invalid concurrency.");
        }

        const results = new Array(events.length);
        let nextIndex = 0;

        const workers = Array.from(
            { length: Math.min(concurrency, events.length) },
            async () => {
                while (true) {
                    const index = nextIndex++;

                    if (index >= events.length) {
                        return;
                    }

                    const event = events[index];

                    try {
                        results[index] = {
                            success: true,
                            valuation: this.processPurchase(
                                event.customerId,
                                event.purchase,
                                event.eventId
                            )
                        };
                    } catch (error) {
                        results[index] = {
                            success: false,
                            error: error.message
                        };
                    }
                }
            }
        );

        await Promise.all(workers);
        return results;
    }
}

class AcquisitionAnalytics {
    static evaluate(marketingSpend, acquiredCustomers, averageCLV) {
        requireFiniteNonNegative(marketingSpend, "Marketing spend");
        requireFiniteNonNegative(averageCLV, "Average CLV");

        if (!Number.isInteger(acquiredCustomers) || acquiredCustomers <= 0) {
            throw new DomainError("Invalid acquired customer count.");
        }

        const cac = marketingSpend / acquiredCustomers;

        return Object.freeze({
            cac,
            averageCLV,
            clvToCacRatio: cac > 0 ? averageCLV / cac : Infinity,
            assessment:
                cac === 0 ? "ZERO_ACQUISITION_COST" :
                averageCLV / cac >= 3 ? "HEALTHY" :
                averageCLV / cac >= 1 ? "REVIEW" :
                "UNSUSTAINABLE"
        });
    }
}

class RetentionPolicy {
    static evaluate(valuation, churnRisk) {
        if (!(churnRisk >= 0 && churnRisk <= 1)) {
            throw new DomainError("Churn risk must be between 0 and 1.");
        }

        const decisions = [];

        if (valuation.netCLV < 0) {
            decisions.push("REASSESS_ACQUISITION_AND_PRICING");
        } else if (valuation.segment === Segment.HIGH_VALUE) {
            decisions.push("PREMIUM_LOYALTY_PROGRAM");
        } else if (valuation.segment === Segment.GROWING) {
            decisions.push("CROSS_SELL_AND_UPSELL");
        } else {
            decisions.push("COST_EFFICIENT_ENGAGEMENT");
        }

        if (churnRisk >= 0.7) {
            decisions.push("URGENT_RETENTION_CAMPAIGN");
        } else if (churnRisk >= 0.4) {
            decisions.push("PROACTIVE_RETENTION_MONITORING");
        }

        if (valuation.confidence === "LOW") {
            decisions.push("COLLECT_MORE_BEHAVIORAL_DATA");
        }

        return decisions;
    }
}

function cohortRetention(acquisitionDates, activityPeriods, cohortMonth) {
    const cohort = new Set(
        Object.entries(acquisitionDates)
            .filter(([, acquiredAt]) => {
                const date = validDate(acquiredAt);

                return (
                    date.getUTCFullYear() === cohortMonth.getUTCFullYear() &&
                    date.getUTCMonth() === cohortMonth.getUTCMonth()
                );
            })
            .map(([id]) => id)
    );

    if (cohort.size === 0) return [];

    return [...activityPeriods.entries()]
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([period, activeCustomers]) => {
            const retained = [...cohort].filter(
                id => activeCustomers.has(id)
            ).length;

            return {
                period,
                cohortSize: cohort.size,
                retained,
                retentionRate: retained / cohort.size
            };
        });
}

function channelAnalysis(customers, model) {
    const groups = new Map();

    for (const customer of customers) {
        const valuation = model.calculate(customer);

        if (!groups.has(customer.channel)) {
            groups.set(customer.channel, []);
        }

        groups.get(customer.channel).push(valuation);
    }

    return Object.fromEntries(
        [...groups.entries()].map(([channel, values]) => {
            const average =
                values.reduce((sum, item) => sum + item.netCLV, 0) /
                values.length;

            return [
                channel,
                {
                    customerCount: values.length,
                    averageNetCLV: average,
                    totalNetCLV: values.reduce(
                        (sum, item) => sum + item.netCLV,
                        0
                    )
                }
            ];
        })
    );
}

async function exportReport(results, filename) {
    if (
        typeof filename !== "string" ||
        filename.includes("..") ||
        filename.includes("/") ||
        filename.includes("\\")
    ) {
        throw new DomainError("Invalid report filename.");
    }

    await fs.writeFile(
        filename,
        JSON.stringify(results, null, 2),
        {
            encoding: "utf8",
            flag: "w"
        }
    );
}

function createDemoService() {
    const model = new CLVModel();
    const service = new CustomerService(model);

    service.on("customer:registered", event => {
        console.log("Registered:", event.customerId);
    });

    service.on("clv:updated", event => {
        console.log(
            "Updated CLV:",
            event.customerId,
            event.netCLV.toFixed(2)
        );
    });

    const customers = [
        new Customer({
            id: "C001",
            acquiredAt: "2024-01-10",
            channel: "organic",
            acquisitionCost: 500
        }),
        new Customer({
            id: "C002",
            acquiredAt: "2024-03-15",
            channel: "paid_search",
            acquisitionCost: 2000
        }),
        new Customer({
            id: "C003",
            acquiredAt: "2024-05-20",
            channel: "referral",
            acquisitionCost: 300
        })
    ];

    customers.forEach(customer => service.register(customer));

    const purchases = [
        ["C001", "T001", "2024-02-01", 5000, 1800],
        ["C001", "T002", "2024-05-01", 6500, 2200],
        ["C001", "T003", "2024-09-01", 7000, 2500],
        ["C001", "T004", "2025-02-01", 8000, 2800],

        ["C002", "T005", "2024-04-01", 1500, 900],
        ["C002", "T006", "2024-07-01", 1800, 1000],
        ["C002", "T007", "2024-10-01", 2000, 1100],

        ["C003", "T008", "2024-06-01", 3000, 1200],
        ["C003", "T009", "2024-10-01", 4000, 1500],
        ["C003", "T010", "2025-03-01", 5000, 1800]
    ];

    purchases.forEach(
        ([customerId, id, date, revenue, variableCost]) => {
            service.processPurchase(
                customerId,
                { id, date, revenue, variableCost },
                `EVENT-${id}`
            );
        }
    );

    return service;
}

async function main() {
    const service = createDemoService();

    const portfolio = service.portfolio();

    console.log("\nPORTFOLIO VALUATION");

    for (const valuation of portfolio) {
        console.log({
            customer: valuation.customerId,
            netCLV: valuation.netCLV.toFixed(2),
            segment: valuation.segment,
            confidence: valuation.confidence
        });

        console.log(
            RetentionPolicy.evaluate(valuation, 0.65)
        );
    }

    console.log("\nCHANNEL ANALYSIS");

    console.log(
        channelAnalysis(
            [...service.customers.values()],
            service.model
        )
    );

    console.log("\nACQUISITION ECONOMICS");

    console.log(
        AcquisitionAnalytics.evaluate(50000, 100, 6000)
    );

    await exportReport(portfolio, "customer_ltv_report.json");

    console.log("\nReport exported.");
}

async function runTests() {
    const model = new CLVModel();

    const customer = new Customer({
        id: "TEST",
        acquiredAt: "2025-01-01",
        channel: "test",
        acquisitionCost: 200
    });

    customer.addPurchase({
        id: "P1",
        date: "2025-02-01",
        revenue: 1000,
        variableCost: 400
    });

    customer.addPurchase({
        id: "P2",
        date: "2025-08-01",
        revenue: 2000,
        variableCost: 800
    });

    const result = model.calculate(customer);

    if (customer.revenue !== 3000) {
        throw new Error("Revenue calculation failed.");
    }

    if (result.netCLV <= 0) {
        throw new Error("CLV calculation failed.");
    }

    if (model.classify(-1) !== Segment.UNPROFITABLE) {
        throw new Error("Segmentation failed.");
    }

    let duplicateRejected = false;

    try {
        customer.addPurchase({
            id: "P1",
            date: "2025-09-01",
            revenue: 100,
            variableCost: 20
        });
    } catch {
        duplicateRejected = true;
    }

    if (!duplicateRejected) {
        throw new Error("Duplicate transaction was accepted.");
    }

    console.log("All JavaScript tests passed.");
}

if (require.main === module) {
    runTests()
        .then(main)
        .catch(error => {
            console.error("Execution failed:", error.message);
            process.exitCode = 1;
        });
}

module.exports = {
    Customer,
    CLVModel,
    CustomerService,
    AcquisitionAnalytics,
    RetentionPolicy,
    cohortRetention,
    channelAnalysis,
    Segment
};
