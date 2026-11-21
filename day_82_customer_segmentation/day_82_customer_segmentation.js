"use strict";

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

const CustomerStatus = Object.freeze({
    ACTIVE: "active",
    INACTIVE: "inactive",
    SUSPENDED: "suspended"
});

const SegmentTypes = Object.freeze({
    DEMOGRAPHIC: "demographic",
    BEHAVIORAL: "behavioral",
    VALUE: "value_based"
});

const ValueSegments = Object.freeze({
    HIGH: "high_value",
    MEDIUM: "medium_value",
    LOW: "low_value"
});

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class Customer {
    constructor(data) {
        this.id = data.id;
        this.name = data.name;
        this.age = data.age;
        this.location = data.location;
        this.income = data.income;
        this.occupation = data.occupation;
        this.purchaseCount = data.purchaseCount;
        this.totalSpend = data.totalSpend;
        this.lastPurchase = new Date(data.lastPurchase);
        this.sessions = data.sessions;
        this.cartAbandonments = data.cartAbandonments;
        this.emailClicks = data.emailClicks;
        this.productViews = data.productViews;
        this.preferredCategory = data.preferredCategory;
        this.status = data.status || CustomerStatus.ACTIVE;
    }

    validate() {
        if (!Number.isSafeInteger(this.id) || this.id <= 0) {
            throw new ValidationError("Invalid customer ID.");
        }

        if (typeof this.name !== "string" || !this.name.trim()) {
            throw new ValidationError("Customer name is required.");
        }

        if (!Number.isInteger(this.age) || this.age < 18 || this.age > 120) {
            throw new ValidationError("Age must be between 18 and 120.");
        }

        const nonNegative = [
            this.income,
            this.purchaseCount,
            this.totalSpend,
            this.sessions,
            this.cartAbandonments,
            this.emailClicks,
            this.productViews
        ];

        if (
            nonNegative.some(
                value => !Number.isFinite(value) || value < 0
            )
        ) {
            throw new ValidationError(
                "Customer financial and behavioral metrics must be non-negative."
            );
        }

        if (!Number.isInteger(this.purchaseCount)) {
            throw new ValidationError("Purchase count must be an integer.");
        }

        if (this.totalSpend > 0 && this.purchaseCount === 0) {
            throw new ValidationError(
                "Spending cannot exist without purchases."
            );
        }

        if (Number.isNaN(this.lastPurchase.getTime())) {
            throw new ValidationError("Invalid purchase date.");
        }

        if (this.lastPurchase > new Date()) {
            throw new ValidationError("Future purchase dates are invalid.");
        }

        if (!Object.values(CustomerStatus).includes(this.status)) {
            throw new ValidationError("Invalid customer status.");
        }
    }
}

class CustomerStore {
    #customers = new Map();

    add(customer) {
        customer.validate();

        if (this.#customers.has(customer.id)) {
            throw new ValidationError(
                `Customer ${customer.id} already exists.`
            );
        }

        this.#customers.set(customer.id, customer);
    }

    get(id) {
        const customer = this.#customers.get(id);

        if (!customer) {
            throw new ValidationError(`Customer ${id} not found.`);
        }

        return customer;
    }

    values() {
        return Array.from(this.#customers.values());
    }
}

class SegmentationPolicy {
    constructor({
        highValue = 100000,
        mediumValue = 30000,
        highIncome = 1200000,
        recentDays = 30,
        dormantDays = 180,
        frequentPurchases = 10,
        engagedSessions = 20,
        engagedEmailClicks = 10
    } = {}) {
        this.highValue = highValue;
        this.mediumValue = mediumValue;
        this.highIncome = highIncome;
        this.recentDays = recentDays;
        this.dormantDays = dormantDays;
        this.frequentPurchases = frequentPurchases;
        this.engagedSessions = engagedSessions;
        this.engagedEmailClicks = engagedEmailClicks;

        this.validate();
    }

    validate() {
        if (
            !Number.isFinite(this.highValue) ||
            !Number.isFinite(this.mediumValue) ||
            this.highValue <= this.mediumValue ||
            this.mediumValue < 0
        ) {
            throw new ValidationError("Invalid spending thresholds.");
        }

        if (
            this.recentDays <= 0 ||
            this.dormantDays <= this.recentDays ||
            this.frequentPurchases <= 0
        ) {
            throw new ValidationError("Invalid behavioral thresholds.");
        }
    }
}

class SegmentationEngine {
    constructor(policy = new SegmentationPolicy()) {
        this.policy = policy;
    }

    calculateRecency(customer, referenceDate) {
        const milliseconds =
            referenceDate.getTime() - customer.lastPurchase.getTime();

        const days = Math.floor(milliseconds / 86400000);

        if (days < 0) {
            throw new ValidationError("Negative purchase recency.");
        }

        return days;
    }

    demographic(customer) {
        const ageGroup =
            customer.age < 30 ? "young_adult" :
            customer.age < 45 ? "adult" :
            customer.age < 60 ? "middle_aged" :
            "senior";

        const incomeGroup =
            customer.income >= this.policy.highIncome
                ? "high_income" :
            customer.income >= this.policy.highIncome / 3
                ? "middle_income" :
            "lower_income";

        return {
            ageGroup,
            incomeGroup,
            segment: `${ageGroup}_${incomeGroup}`
        };
    }

    behavioral(customer, recency) {
        if (recency > this.policy.dormantDays) {
            return "dormant";
        }

        if (
            recency <= this.policy.recentDays &&
            customer.purchaseCount >= this.policy.frequentPurchases
        ) {
            return "loyal_active";
        }

        if (recency <= this.policy.recentDays) {
            return "recent_customer";
        }

        if (
            customer.sessions >= this.policy.engagedSessions ||
            customer.emailClicks >= this.policy.engagedEmailClicks
        ) {
            return "digitally_engaged";
        }

        if (
            customer.purchaseCount >= this.policy.frequentPurchases
        ) {
            return "repeat_customer";
        }

        return "occasional_customer";
    }

    valueBased(customer) {
        if (customer.totalSpend >= this.policy.highValue) {
            return ValueSegments.HIGH;
        }

        if (customer.totalSpend >= this.policy.mediumValue) {
            return ValueSegments.MEDIUM;
        }

        return ValueSegments.LOW;
    }

    evaluate(customer, referenceDate = new Date()) {
        customer.validate();

        const recency = this.calculateRecency(
            customer,
            referenceDate
        );

        const demographic = this.demographic(customer);
        const behavioral = this.behavioral(customer, recency);
        const value = this.valueBased(customer);

        return Object.freeze({
            customerId: customer.id,
            demographic,
            behavioral,
            value,
            recencyDays: recency,
            frequency: customer.purchaseCount,
            monetaryValue: customer.totalSpend,
            averageOrderValue: customer.purchaseCount
                ? customer.totalSpend / customer.purchaseCount
                : 0,
            evaluatedAt: referenceDate.toISOString()
        });
    }
}

class CampaignDecisionEngine {
    evaluate(customer, segmentation) {
        if (customer.status !== CustomerStatus.ACTIVE) {
            return {
                eligible: false,
                reason: "Customer account is not active."
            };
        }

        if (segmentation.behavioral === "dormant") {
            return {
                eligible: false,
                reason: "Dormant customers require a separate campaign."
            };
        }

        if (segmentation.value === ValueSegments.HIGH) {
            return {
                eligible: true,
                campaign: "premium_retention",
                priority: 1
            };
        }

        if (segmentation.behavioral === "digitally_engaged") {
            return {
                eligible: true,
                campaign: "digital_engagement",
                priority: 2
            };
        }

        return {
            eligible: true,
            campaign: "standard_engagement",
            priority: 3
        };
    }
}

/*
 * Event-driven processing:
 * A completed purchase triggers a segmentation refresh.
 * The event does not directly grant marketing consent.
 */
class CustomerEventProcessor extends EventEmitter {
    constructor(store, engine) {
        super();

        this.store = store;
        this.engine = engine;
        this.results = new Map();

        this.on("purchase.completed", event => {
            try {
                const customer = this.store.get(event.customerId);

                const result = this.engine.evaluate(
                    customer,
                    new Date()
                );

                this.results.set(customer.id, result);

                this.emit("segmentation.updated", result);
            } catch (error) {
                this.emit("processing.error", {
                    event,
                    message: error.message
                });
            }
        });
    }

    publishPurchase(customerId, transactionId) {
        if (!transactionId || typeof transactionId !== "string") {
            throw new ValidationError("Transaction ID is required.");
        }

        this.emit("purchase.completed", {
            customerId,
            transactionId,
            eventId: crypto.randomUUID(),
            occurredAt: new Date().toISOString()
        });
    }
}

class SegmentAnalytics {
    static analyze(results) {
        const dimensions = {
            demographic: new Map(),
            behavioral: new Map(),
            value: new Map()
        };

        let totalSpend = 0;

        const increment = (map, key) => {
            map.set(key, (map.get(key) || 0) + 1);
        };

        for (const result of results) {
            increment(
                dimensions.demographic,
                result.demographic.segment
            );

            increment(
                dimensions.behavioral,
                result.behavioral
            );

            increment(
                dimensions.value,
                result.value
            );

            totalSpend += result.monetaryValue;
        }

        const serialize = map =>
            Object.fromEntries(
                Array.from(map.entries()).sort(
                    ([a], [b]) => a.localeCompare(b)
                )
            );

        return {
            customerCount: results.length,
            totalSpend,
            averageSpend: results.length
                ? totalSpend / results.length
                : 0,
            distributions: {
                demographic: serialize(dimensions.demographic),
                behavioral: serialize(dimensions.behavioral),
                value: serialize(dimensions.value)
            }
        };
    }

    static crossTabulate(results) {
        const matrix = new Map();

        for (const result of results) {
            if (!matrix.has(result.behavioral)) {
                matrix.set(result.behavioral, new Map());
            }

            const row = matrix.get(result.behavioral);

            row.set(
                result.value,
                (row.get(result.value) || 0) + 1
            );
        }

        return Object.fromEntries(
            Array.from(matrix.entries()).map(([behavior, values]) => [
                behavior,
                Object.fromEntries(values)
            ])
        );
    }
}

class ReportExporter {
    static async export(results, destination) {
        if (path.extname(destination).toLowerCase() !== ".json") {
            throw new ValidationError("Only JSON export is supported.");
        }

        const absolutePath = path.resolve(destination);

        const temporaryPath =
            `${absolutePath}.${crypto.randomUUID()}.tmp`;

        const data = JSON.stringify(results, null, 2);

        try {
            await fs.writeFile(
                temporaryPath,
                data,
                {
                    encoding: "utf8",
                    flag: "wx",
                    mode: 0o600
                }
            );

            await fs.rename(temporaryPath, absolutePath);
        } catch (error) {
            await fs.unlink(temporaryPath).catch(() => {});

            throw new Error(
                `Report export failed: ${error.message}`
            );
        }
    }
}

function buildCustomers() {
    const today = new Date();

    const daysAgo = days => {
        const value = new Date(today);
        value.setDate(value.getDate() - days);
        return value.toISOString();
    };

    return [
        {
            id: 2001,
            name: "Customer A",
            age: 26,
            location: "Delhi",
            income: 1800000,
            occupation: "Engineer",
            purchaseCount: 20,
            totalSpend: 165000,
            lastPurchase: daysAgo(5),
            sessions: 50,
            cartAbandonments: 3,
            emailClicks: 20,
            productViews: 90,
            preferredCategory: "Electronics"
        },
        {
            id: 2002,
            name: "Customer B",
            age: 39,
            location: "Mumbai",
            income: 850000,
            occupation: "Manager",
            purchaseCount: 8,
            totalSpend: 65000,
            lastPurchase: daysAgo(25),
            sessions: 28,
            cartAbandonments: 5,
            emailClicks: 12,
            productViews: 45,
            preferredCategory: "Fashion"
        },
        {
            id: 2003,
            name: "Customer C",
            age: 55,
            location: "Lucknow",
            income: 450000,
            occupation: "Teacher",
            purchaseCount: 3,
            totalSpend: 18000,
            lastPurchase: daysAgo(95),
            sessions: 8,
            cartAbandonments: 1,
            emailClicks: 2,
            productViews: 12,
            preferredCategory: "Books"
        },
        {
            id: 2004,
            name: "Customer D",
            age: 65,
            location: "Pune",
            income: 2200000,
            occupation: "Consultant",
            purchaseCount: 22,
            totalSpend: 245000,
            lastPurchase: daysAgo(12),
            sessions: 75,
            cartAbandonments: 2,
            emailClicks: 35,
            productViews: 120,
            preferredCategory: "Travel"
        },
        {
            id: 2005,
            name: "Customer E",
            age: 32,
            location: "Jaipur",
            income: 700000,
            occupation: "Analyst",
            purchaseCount: 1,
            totalSpend: 2500,
            lastPurchase: daysAgo(250),
            sessions: 3,
            cartAbandonments: 0,
            emailClicks: 0,
            productViews: 4,
            preferredCategory: "Home"
        }
    ];
}

function runTests(engine, store) {
    const customer = store.get(2001);
    const result = engine.evaluate(customer);

    console.assert(
        result.value === ValueSegments.HIGH,
        "High-value classification failed."
    );

    console.assert(
        result.behavioral === "loyal_active",
        "Loyal customer classification failed."
    );

    const zeroPurchase = new Customer({
        id: 2099,
        name: "No Purchase",
        age: 25,
        income: 300000,
        purchaseCount: 0,
        totalSpend: 0,
        lastPurchase: new Date(),
        sessions: 2,
        cartAbandonments: 0,
        emailClicks: 0,
        productViews: 2
    });

    console.assert(
        engine.evaluate(zeroPurchase).averageOrderValue === 0,
        "Zero-purchase handling failed."
    );

    console.log("JavaScript segmentation tests completed.");
}

async function main() {
    const store = new CustomerStore();

    for (const data of buildCustomers()) {
        store.add(new Customer(data));
    }

    const engine = new SegmentationEngine();
    const campaignEngine = new CampaignDecisionEngine();

    runTests(engine, store);

    const processor = new CustomerEventProcessor(store, engine);

    processor.on("segmentation.updated", result => {
        console.log(
            `Segmentation updated for customer ${result.customerId}.`
        );
    });

    processor.on("processing.error", error => {
        console.error("Event processing failure:", error);
    });

    processor.publishPurchase(2001, "TXN-10001");

    const results = store.values().map(customer => {
        const segmentation = engine.evaluate(customer);

        return {
            ...segmentation,
            campaign: campaignEngine.evaluate(
                customer,
                segmentation
            )
        };
    });

    console.log("\nCUSTOMER SEGMENTATION");

    console.log(JSON.stringify(results, null, 2));

    console.log("\nSEGMENT ANALYTICS");

    console.log(
        JSON.stringify(
            SegmentAnalytics.analyze(results),
            null,
            2
        )
    );

    console.log("\nBEHAVIORAL-VALUE CROSS TABULATION");

    console.log(
        JSON.stringify(
            SegmentAnalytics.crossTabulate(results),
            null,
            2
        )
    );

    await ReportExporter.export(
        results,
        "customer_segmentation_js_report.json"
    );

    console.log("Report exported successfully.");
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
