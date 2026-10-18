"use strict";

/*
 * Cohort analysis in JavaScript
 *
 * This implementation models an event-driven customer product where raw
 * events are transformed into monthly behavioral cohorts. It deliberately
 * separates acquisition month, activity period, retention, revenue, and
 * customer segmentation so that repeated events from the same customer do
 * not inflate active-user counts.
 */

class CohortAnalysisError extends Error {
    constructor(message) {
        super(message);
        this.name = "CohortAnalysisError";
    }
}

function monthKey(date) {
    return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
}

function monthOffset(start, current) {
    return (
        (current.getUTCFullYear() - start.getUTCFullYear()) * 12 +
        current.getUTCMonth() -
        start.getUTCMonth()
    );
}

function assertDate(value, fieldName) {
    if (!(value instanceof Date) || Number.isNaN(value.getTime())) {
        throw new CohortAnalysisError(`${fieldName} must be a valid Date.`);
    }
}

function normalizeEvent(event) {
    assertDate(event.date, "event.date");

    if (typeof event.customerId !== "string" || event.customerId.length === 0) {
        throw new CohortAnalysisError("event.customerId is required.");
    }

    if (typeof event.type !== "string" || event.type.length === 0) {
        throw new CohortAnalysisError("event.type is required.");
    }

    if (!Number.isFinite(event.revenue) || event.revenue < 0) {
        throw new CohortAnalysisError("event.revenue must be a non-negative number.");
    }

    return Object.freeze({ ...event });
}

function normalizeCustomer(customer) {
    assertDate(customer.signupDate, "signupDate");

    if (!customer.id || !customer.channel || !customer.plan) {
        throw new CohortAnalysisError(
            "Customer requires id, signupDate, channel, and plan."
        );
    }

    return Object.freeze({ ...customer });
}

class CustomerCohortEngine {
    constructor(customers, events) {
        this.customers = customers.map(normalizeCustomer);
        this.events = events.map(normalizeEvent);

        this.customersById = new Map();

        for (const customer of this.customers) {
            if (this.customersById.has(customer.id)) {
                throw new CohortAnalysisError(
                    `Duplicate customer ID: ${customer.id}`
                );
            }

            this.customersById.set(customer.id, customer);
        }

        for (const event of this.events) {
            if (!this.customersById.has(event.customerId)) {
                throw new CohortAnalysisError(
                    `Unknown customer in event: ${event.customerId}`
                );
            }

            const customer = this.customersById.get(event.customerId);

            if (event.date < customer.signupDate) {
                throw new CohortAnalysisError(
                    `Event before signup for ${event.customerId}`
                );
            }
        }
    }

    cohorts() {
        const result = new Map();

        for (const customer of this.customers) {
            const cohort = monthKey(customer.signupDate);

            if (!result.has(cohort)) {
                result.set(cohort, new Set());
            }

            result.get(cohort).add(customer.id);
        }

        return result;
    }

    activityMatrix() {
        const matrix = new Map();

        for (const event of this.events) {
            const customer = this.customersById.get(event.customerId);
            const cohort = monthKey(customer.signupDate);
            const period = monthOffset(customer.signupDate, event.date);

            if (!matrix.has(cohort)) {
                matrix.set(cohort, new Map());
            }

            const periodMap = matrix.get(cohort);

            if (!periodMap.has(period)) {
                periodMap.set(period, new Set());
            }

            // Set is important: ten events from one customer still represent
            // one active customer for retention in that month.
            periodMap.get(period).add(event.customerId);
        }

        return matrix;
    }

    retention() {
        const cohorts = this.cohorts();
        const matrix = this.activityMatrix();
        const output = new Map();

        for (const [cohort, members] of cohorts) {
            const periods = matrix.get(cohort) ?? new Map();
            const retentionByPeriod = new Map();

            for (const [period, activeCustomers] of periods) {
                retentionByPeriod.set(
                    period,
                    activeCustomers.size / members.size
                );
            }

            output.set(cohort, retentionByPeriod);
        }

        return output;
    }

    revenueByPeriod() {
        const revenue = new Map();

        for (const event of this.events) {
            const customer = this.customersById.get(event.customerId);
            const cohort = monthKey(customer.signupDate);
            const period = monthOffset(customer.signupDate, event.date);

            if (!revenue.has(cohort)) {
                revenue.set(cohort, new Map());
            }

            const periods = revenue.get(cohort);
            periods.set(period, (periods.get(period) ?? 0) + event.revenue);
        }

        return revenue;
    }

    retentionBySegment(segmentField) {
        if (!["channel", "plan"].includes(segmentField)) {
            throw new CohortAnalysisError(
                "Supported segment fields are channel and plan."
            );
        }

        const groups = new Map();

        for (const customer of this.customers) {
            const segment = customer[segmentField];
            const cohort = monthKey(customer.signupDate);
            const key = `${cohort}|${segment}`;

            if (!groups.has(key)) {
                groups.set(key, {
                    cohort,
                    segment,
                    members: new Set(),
                    active: new Map()
                });
            }

            groups.get(key).members.add(customer.id);
        }

        for (const event of this.events) {
            const customer = this.customersById.get(event.customerId);
            const cohort = monthKey(customer.signupDate);
            const segment = customer[segmentField];
            const key = `${cohort}|${segment}`;
            const period = monthOffset(customer.signupDate, event.date);

            const group = groups.get(key);

            if (!group.active.has(period)) {
                group.active.set(period, new Set());
            }

            group.active.get(period).add(customer.id);
        }

        const result = [];

        for (const group of groups.values()) {
            const retention = new Map();

            for (const [period, customers] of group.active) {
                retention.set(
                    period,
                    customers.size / group.members.size
                );
            }

            result.push({
                cohort: group.cohort,
                segment: group.segment,
                size: group.members.size,
                retention
            });
        }

        return result;
    }

    async processEventsAsync(handler) {
        /*
         * The async generator models a streaming event pipeline. Yielding
         * control between events makes the processing shape suitable for
         * event-driven applications without requiring an external package.
         */
        for (const event of this.events) {
            await Promise.resolve();
            await handler(event);
        }
    }
}

function percentage(value) {
    return `${(value * 100).toFixed(1)}%`;
}

function printRetention(engine) {
    console.log("\nRETENTION MATRIX");
    console.log("=".repeat(70));

    for (const [cohort, periods] of engine.retention()) {
        const values = [...periods.entries()]
            .sort(([a], [b]) => a - b)
            .map(([period, rate]) => `M${period}=${percentage(rate)}`)
            .join(" | ");

        console.log(`${cohort} | ${values}`);
    }
}

function printSegmentAnalysis(engine) {
    console.log("\nPLAN-SEGMENT RETENTION");
    console.log("=".repeat(70));

    for (const group of engine.retentionBySegment("plan")) {
        const periods = [...group.retention.entries()]
            .sort(([a], [b]) => a - b)
            .map(([period, rate]) => `M${period}=${percentage(rate)}`)
            .join(" | ");

        console.log(
            `${group.cohort} | ${group.segment} | size=${group.size} | ${periods}`
        );
    }
}

async function demonstrateEventStream(engine) {
    const eventCounts = new Map();

    await engine.processEventsAsync(async (event) => {
        const key = event.type;
        eventCounts.set(key, (eventCounts.get(key) ?? 0) + 1);
    });

    console.log("\nEVENT STREAM COUNTS");
    console.log("=".repeat(70));

    for (const [type, count] of eventCounts) {
        console.log(`${type}: ${count}`);
    }
}

function buildData() {
    const customers = [
        {
            id: "C001",
            signupDate: new Date("2026-01-05T00:00:00Z"),
            channel: "organic",
            plan: "pro"
        },
        {
            id: "C002",
            signupDate: new Date("2026-01-14T00:00:00Z"),
            channel: "paid",
            plan: "basic"
        },
        {
            id: "C003",
            signupDate: new Date("2026-01-22T00:00:00Z"),
            channel: "referral",
            plan: "pro"
        },
        {
            id: "C004",
            signupDate: new Date("2026-02-04T00:00:00Z"),
            channel: "organic",
            plan: "basic"
        },
        {
            id: "C005",
            signupDate: new Date("2026-02-15T00:00:00Z"),
            channel: "paid",
            plan: "pro"
        },
        {
            id: "C006",
            signupDate: new Date("2026-03-03T00:00:00Z"),
            channel: "referral",
            plan: "basic"
        }
    ];

    const events = [
        { customerId: "C001", date: new Date("2026-01-05T00:00:00Z"), type: "signup", revenue: 0 },
        { customerId: "C001", date: new Date("2026-01-10T00:00:00Z"), type: "purchase", revenue: 49 },
        { customerId: "C001", date: new Date("2026-02-12T00:00:00Z"), type: "login", revenue: 0 },
        { customerId: "C001", date: new Date("2026-03-15T00:00:00Z"), type: "purchase", revenue: 49 },

        { customerId: "C002", date: new Date("2026-01-14T00:00:00Z"), type: "signup", revenue: 0 },
        { customerId: "C002", date: new Date("2026-01-18T00:00:00Z"), type: "purchase", revenue: 19 },
        { customerId: "C002", date: new Date("2026-02-02T00:00:00Z"), type: "login", revenue: 0 },

        { customerId: "C003", date: new Date("2026-01-22T00:00:00Z"), type: "signup", revenue: 0 },
        { customerId: "C003", date: new Date("2026-01-24T00:00:00Z"), type: "purchase", revenue: 49 },
        { customerId: "C003", date: new Date("2026-02-16T00:00:00Z"), type: "purchase", revenue: 49 },

        { customerId: "C004", date: new Date("2026-02-04T00:00:00Z"), type: "signup", revenue: 0 },
        { customerId: "C004", date: new Date("2026-02-08T00:00:00Z"), type: "purchase", revenue: 19 },
        { customerId: "C004", date: new Date("2026-03-11T00:00:00Z"), type: "login", revenue: 0 },

        { customerId: "C005", date: new Date("2026-02-15T00:00:00Z"), type: "signup", revenue: 0 },
        { customerId: "C005", date: new Date("2026-02-17T00:00:00Z"), type: "purchase", revenue: 49 },
        { customerId: "C005", date: new Date("2026-03-19T00:00:00Z"), type: "purchase", revenue: 49 },

        { customerId: "C006", date: new Date("2026-03-03T00:00:00Z"), type: "signup", revenue: 0 },
        { customerId: "C006", date: new Date("2026-03-06T00:00:00Z"), type: "purchase", revenue: 19 }
    ];

    return { customers, events };
}

async function main() {
    const { customers, events } = buildData();
    const engine = new CustomerCohortEngine(customers, events);

    console.log("COHORT ANALYSIS");
    console.log("=".repeat(70));
    console.log(
        "Retention uses unique active customers per cohort period, while revenue is aggregated separately."
    );

    printRetention(engine);

    console.log("\nCOHORT REVENUE");
    console.log("=".repeat(70));

    for (const [cohort, periods] of engine.revenueByPeriod()) {
        const values = [...periods.entries()]
            .sort(([a], [b]) => a - b)
            .map(([period, amount]) => `M${period}=$${amount.toFixed(2)}`)
            .join(" | ");

        console.log(`${cohort} | ${values}`);
    }

    printSegmentAnalysis(engine);
    await demonstrateEventStream(engine);
}

main().catch((error) => {
    console.error(`${error.name}: ${error.message}`);
    process.exitCode = 1;
});
