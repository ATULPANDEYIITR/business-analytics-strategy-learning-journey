"use strict";

/*
 * UNIT ECONOMICS EVENT-DRIVEN ANALYTICS
 *
 * CAC, LTV, contribution margin, payback,
 * cohort aggregation, channel evaluation,
 * policy checks and asynchronous report generation.
 *
 * Runtime: Node.js 18+
 * Dependencies: Built-in modules only.
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");
const path = require("node:path");
const crypto = require("node:crypto");

class DomainError extends Error {
    constructor(message, code = "DOMAIN_ERROR") {
        super(message);
        this.name = "DomainError";
        this.code = code;
    }
}

const Channel = Object.freeze({
    ORGANIC: "organic",
    PAID_SEARCH: "paid_search",
    SOCIAL: "social",
    REFERRAL: "referral",
    PARTNERSHIP: "partnership"
});

const SubscriptionStatus = Object.freeze({
    ACTIVE: "active",
    CHURNED: "churned",
    SUSPENDED: "suspended"
});

function requireFiniteNonNegative(value, field) {
    if (!Number.isFinite(value) || value < 0) {
        throw new DomainError(`${field} must be finite and non-negative.`);
    }
}

function requirePositiveInteger(value, field) {
    if (!Number.isInteger(value) || value <= 0) {
        throw new DomainError(`${field} must be a positive integer.`);
    }
}

function money(value) {
    return Math.round((value + Number.EPSILON) * 100) / 100;
}

class AcquisitionRecord {
    constructor({
        channel,
        advertisingCost,
        salesCost,
        marketingCost,
        customers,
        period
    }) {
        if (!Object.values(Channel).includes(channel)) {
            throw new DomainError("Unknown acquisition channel.");
        }

        requireFiniteNonNegative(advertisingCost, "Advertising cost");
        requireFiniteNonNegative(salesCost, "Sales cost");
        requireFiniteNonNegative(marketingCost, "Marketing cost");
        requirePositiveInteger(customers, "Customers");

        if (!period || !/^\d{4}-\d{2}$/.test(period)) {
            throw new DomainError("Period must use YYYY-MM format.");
        }

        this.channel = channel;
        this.advertisingCost = advertisingCost;
        this.salesCost = salesCost;
        this.marketingCost = marketingCost;
        this.customers = customers;
        this.period = period;
        Object.freeze(this);
    }

    get totalCost() {
        return this.advertisingCost +
            this.salesCost +
            this.marketingCost;
    }

    get cac() {
        return this.totalCost / this.customers;
    }
}

class Subscription {
    constructor({
        customerId,
        cohort,
        channel,
        monthlyRevenue,
        variableCost,
        expectedLifetime,
        churnRate,
        status = SubscriptionStatus.ACTIVE
    }) {
        if (!customerId || !customerId.trim()) {
            throw new DomainError("Customer ID is required.");
        }

        if (!Object.values(Channel).includes(channel)) {
            throw new DomainError("Invalid acquisition channel.");
        }

        requireFiniteNonNegative(monthlyRevenue, "Revenue");
        requireFiniteNonNegative(variableCost, "Variable cost");

        if (expectedLifetime <= 0 || !Number.isFinite(expectedLifetime)) {
            throw new DomainError("Expected lifetime must be positive.");
        }

        if (!Number.isFinite(churnRate) || churnRate < 0 || churnRate >= 1) {
            throw new DomainError("Churn rate must be in [0, 1).");
        }

        if (!Object.values(SubscriptionStatus).includes(status)) {
            throw new DomainError("Invalid subscription status.");
        }

        if (variableCost > 0 && monthlyRevenue === 0) {
            throw new DomainError("Variable cost without revenue is invalid.");
        }

        this.customerId = customerId;
        this.cohort = cohort;
        this.channel = channel;
        this.monthlyRevenue = monthlyRevenue;
        this.variableCost = variableCost;
        this.expectedLifetime = expectedLifetime;
        this.churnRate = churnRate;
        this.status = status;
        Object.freeze(this);
    }

    get monthlyContribution() {
        return this.monthlyRevenue - this.variableCost;
    }

    get contributionMargin() {
        return this.monthlyRevenue === 0
            ? 0
            : this.monthlyContribution / this.monthlyRevenue;
    }
}

class EconomicsCalculator {
    evaluate(acquisition, subscription) {
        if (acquisition.channel !== subscription.channel) {
            throw new DomainError(
                "Acquisition and subscription channels must match."
            );
        }

        const cac = acquisition.cac;
        const contribution = subscription.monthlyContribution;

        const grossLtv =
            subscription.monthlyRevenue * subscription.expectedLifetime;

        const contributionLtv =
            contribution * subscription.expectedLifetime;

        const payback = contribution > 0
            ? cac / contribution
            : null;

        const ratio = cac > 0
            ? contributionLtv / cac
            : contributionLtv > 0
                ? Infinity
                : 0;

        let classification;

        if (contribution <= 0) {
            classification = "NEGATIVE_CONTRIBUTION";
        } else if (contributionLtv <= cac) {
            classification = "UNPROFITABLE";
        } else if (payback <= subscription.expectedLifetime) {
            classification = "LIFETIME_POSITIVE";
        } else {
            classification = "PAYBACK_EXCEEDS_LIFETIME";
        }

        return Object.freeze({
            customerId: subscription.customerId,
            channel: subscription.channel,
            cac: money(cac),
            monthlyContribution: money(contribution),
            contributionMarginPercent:
                money(subscription.contributionMargin * 100),
            grossLtv: money(grossLtv),
            contributionLtv: money(contributionLtv),
            ltvCacRatio: Number.isFinite(ratio) ? money(ratio) : null,
            paybackMonths: payback === null ? null : money(payback),
            classification
        });
    }
}

class CohortRegistry {
    #cohorts = new Map();

    add(subscription) {
        if (!(subscription instanceof Subscription)) {
            throw new DomainError("Invalid subscription object.");
        }

        const cohort = this.#cohorts.get(subscription.cohort) || new Map();

        if (cohort.has(subscription.customerId)) {
            throw new DomainError("Duplicate customer in cohort.");
        }

        cohort.set(subscription.customerId, subscription);
        this.#cohorts.set(subscription.cohort, cohort);
    }

    analyze() {
        return [...this.#cohorts.entries()].map(([name, customers]) => {
            let revenue = 0;
            let variableCost = 0;
            const channels = new Set();

            for (const customer of customers.values()) {
                revenue += customer.monthlyRevenue;
                variableCost += customer.variableCost;
                channels.add(customer.channel);
            }

            const contribution = revenue - variableCost;

            return {
                cohort: name,
                customers: customers.size,
                revenue: money(revenue),
                variableCost: money(variableCost),
                contribution: money(contribution),
                marginPercent: revenue > 0
                    ? money(contribution / revenue * 100)
                    : 0,
                acquisitionChannels: [...channels].sort()
            };
        });
    }
}

class ChannelPerformance {
    static evaluate(records) {
        const channels = new Map();

        for (const record of records) {
            const current = channels.get(record.channel) || {
                totalCost: 0,
                customers: 0
            };

            current.totalCost += record.totalCost;
            current.customers += record.customers;

            channels.set(record.channel, current);
        }

        return [...channels.entries()]
            .map(([channel, data]) => ({
                channel,
                customers: data.customers,
                totalCost: money(data.totalCost),
                cac: money(data.totalCost / data.customers)
            }))
            .sort((a, b) => a.cac - b.cac);
    }
}

class EconomicsPolicy {
    constructor({
        minimumLtvCacRatio = 3,
        maximumPaybackMonths = 12,
        minimumContributionMargin = 0.5
    } = {}) {
        if (minimumLtvCacRatio <= 0 ||
            maximumPaybackMonths <= 0 ||
            minimumContributionMargin < 0 ||
            minimumContributionMargin > 1) {
            throw new DomainError("Invalid policy thresholds.");
        }

        this.minimumLtvCacRatio = minimumLtvCacRatio;
        this.maximumPaybackMonths = maximumPaybackMonths;
        this.minimumContributionMargin = minimumContributionMargin;
        Object.freeze(this);
    }

    evaluate(result) {
        const violations = [];

        if (result.ltvCacRatio === null ||
            result.ltvCacRatio < this.minimumLtvCacRatio) {
            violations.push("LTV_CAC_BELOW_THRESHOLD");
        }

        if (result.paybackMonths === null ||
            result.paybackMonths > this.maximumPaybackMonths) {
            violations.push("PAYBACK_EXCEEDS_POLICY");
        }

        if (result.contributionMarginPercent <
            this.minimumContributionMargin * 100) {
            violations.push("LOW_CONTRIBUTION_MARGIN");
        }

        return {
            eligible: violations.length === 0,
            violations
        };
    }
}

class AnalyticsService extends EventEmitter {
    #calculator;
    #policy;
    #results = new Map();

    constructor(policy = new EconomicsPolicy()) {
        super();
        this.#calculator = new EconomicsCalculator();
        this.#policy = policy;
    }

    process(acquisition, subscription) {
        const result = this.#calculator.evaluate(
            acquisition,
            subscription
        );

        const policyResult = this.#policy.evaluate(result);

        const transactionId = crypto.randomUUID();

        const event = Object.freeze({
            transactionId,
            timestamp: new Date().toISOString(),
            result,
            policyResult
        });

        this.#results.set(transactionId, event);

        this.emit("calculated", event);

        if (!policyResult.eligible) {
            this.emit("policyViolation", event);
        }

        return event;
    }

    getResults() {
        return [...this.#results.values()];
    }
}

async function exportReport(report, filename = "unit_economics_report.json") {
    const destination = path.resolve(process.cwd(), filename);

    if (path.dirname(destination) !== process.cwd()) {
        throw new DomainError("Export must remain in the working directory.");
    }

    const temporary = `${destination}.${crypto.randomUUID()}.tmp`;

    try {
        await fs.writeFile(
            temporary,
            JSON.stringify(report, null, 2),
            { encoding: "utf8", flag: "wx", mode: 0o600 }
        );

        await fs.rename(temporary, destination);
        return destination;
    } catch (error) {
        await fs.rm(temporary, { force: true }).catch(() => {});
        throw error;
    }
}

async function runTests() {
    const calculator = new EconomicsCalculator();

    const acquisition = new AcquisitionRecord({
        channel: Channel.PAID_SEARCH,
        advertisingCost: 30000,
        salesCost: 10000,
        marketingCost: 10000,
        customers: 100,
        period: "2026-01"
    });

    const customer = new Subscription({
        customerId: "C001",
        cohort: "2026-Q1",
        channel: Channel.PAID_SEARCH,
        monthlyRevenue: 1000,
        variableCost: 300,
        expectedLifetime: 18,
        churnRate: 0.04
    });

    const result = calculator.evaluate(acquisition, customer);

    if (result.cac !== 500 || result.monthlyContribution !== 700) {
        throw new Error("Calculation test failed.");
    }

    if (result.paybackMonths !== 0.71) {
        throw new Error("Payback test failed.");
    }

    console.log("Calculation tests passed.");
}

async function main() {
    await runTests();

    const policy = new EconomicsPolicy({
        minimumLtvCacRatio: 3,
        maximumPaybackMonths: 12,
        minimumContributionMargin: 0.5
    });

    const service = new AnalyticsService(policy);
    const cohorts = new CohortRegistry();

    service.on("calculated", event => {
        console.log(
            `Processed ${event.result.customerId}: ` +
            `CAC=${event.result.cac}, ` +
            `LTV/CAC=${event.result.ltvCacRatio}`
        );
    });

    service.on("policyViolation", event => {
        console.warn(
            "Policy violations:",
            event.policyResult.violations
        );
    });

    const acquisitionData = [
        new AcquisitionRecord({
            channel: Channel.PAID_SEARCH,
            advertisingCost: 30000,
            salesCost: 10000,
            marketingCost: 10000,
            customers: 100,
            period: "2026-01"
        }),
        new AcquisitionRecord({
            channel: Channel.SOCIAL,
            advertisingCost: 18000,
            salesCost: 6000,
            marketingCost: 6000,
            customers: 120,
            period: "2026-01"
        }),
        new AcquisitionRecord({
            channel: Channel.REFERRAL,
            advertisingCost: 5000,
            salesCost: 2000,
            marketingCost: 3000,
            customers: 100,
            period: "2026-01"
        })
    ];

    const subscriptions = [
        new Subscription({
            customerId: "C001",
            cohort: "2026-Q1",
            channel: Channel.PAID_SEARCH,
            monthlyRevenue: 1000,
            variableCost: 300,
            expectedLifetime: 18,
            churnRate: 0.04
        }),
        new Subscription({
            customerId: "C002",
            cohort: "2026-Q1",
            channel: Channel.SOCIAL,
            monthlyRevenue: 800,
            variableCost: 280,
            expectedLifetime: 15,
            churnRate: 0.05
        }),
        new Subscription({
            customerId: "C003",
            cohort: "2026-Q1",
            channel: Channel.REFERRAL,
            monthlyRevenue: 1200,
            variableCost: 350,
            expectedLifetime: 24,
            churnRate: 0.025
        })
    ];

    for (let index = 0; index < subscriptions.length; index++) {
        cohorts.add(subscriptions[index]);
        service.process(acquisitionData[index], subscriptions[index]);
    }

    const report = {
        currency: "INR",
        generatedAt: new Date().toISOString(),
        policy: {
            minimumLtvCacRatio: policy.minimumLtvCacRatio,
            maximumPaybackMonths: policy.maximumPaybackMonths,
            minimumContributionMargin: policy.minimumContributionMargin
        },
        channelPerformance: ChannelPerformance.evaluate(acquisitionData),
        cohorts: cohorts.analyze(),
        transactions: service.getResults()
    };

    const output = await exportReport(report);
    console.log(`Report saved: ${output}`);
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
