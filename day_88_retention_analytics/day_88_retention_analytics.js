'use strict';

/*
 * RETENTION ANALYTICS
 * Event-driven customer churn and loyalty management.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library
 *
 * Features:
 * - Event-driven customer lifecycle
 * - Behavioral engagement monitoring
 * - Churn policy evaluation
 * - Customer segmentation
 * - Loyalty points and tier management
 * - Cohort retention calculations
 * - Campaign targeting
 * - Campaign ROI evaluation
 * - Asynchronous batch processing
 * - Structured analytics exports
 */

const fs = require('node:fs/promises');
const path = require('node:path');
const { EventEmitter } = require('node:events');
const crypto = require('node:crypto');


// ============================================================
// 1. DOMAIN CONSTANTS
// ============================================================

const CUSTOMER_STATUS = Object.freeze({
    ACTIVE: 'active',
    AT_RISK: 'at_risk',
    CHURNED: 'churned',
    REACTIVATED: 'reactivated'
});

const EVENT_TYPES = new Set([
    'purchase',
    'login',
    'support',
    'email_open',
    'email_click',
    'subscription',
    'refund'
]);

const LOYALTY_TIERS = Object.freeze({
    BRONZE: 'bronze',
    SILVER: 'silver',
    GOLD: 'gold',
    PLATINUM: 'platinum'
});

const CAMPAIGN_STATES = Object.freeze({
    DRAFT: 'draft',
    ACTIVE: 'active',
    PAUSED: 'paused',
    COMPLETED: 'completed'
});


// ============================================================
// 2. CUSTOM ERRORS
// ============================================================

class DomainError extends Error {
    constructor(message) {
        super(message);
        this.name = this.constructor.name;
    }
}

class ValidationError extends DomainError {}
class NotFoundError extends DomainError {}
class ConflictError extends DomainError {}
class BudgetExceededError extends DomainError {}


// ============================================================
// 3. VALIDATION UTILITIES
// ============================================================

function requireString(value, field) {
    if (typeof value !== 'string' || value.trim() === '') {
        throw new ValidationError(`${field} is required.`);
    }

    return value.trim();
}

function requireFiniteNumber(value, field, minimum = 0) {
    if (
        typeof value !== 'number' ||
        !Number.isFinite(value) ||
        value < minimum
    ) {
        throw new ValidationError(`Invalid ${field}.`);
    }

    return value;
}

function requireDate(value, field) {
    const parsed = new Date(value);

    if (Number.isNaN(parsed.getTime())) {
        throw new ValidationError(`Invalid ${field}.`);
    }

    return parsed;
}

function daysBetween(later, earlier) {
    return Math.max(
        0,
        Math.floor((later.getTime() - earlier.getTime()) / 86400000)
    );
}

function monthKey(date) {
    return `${date.getUTCFullYear()}-${String(
        date.getUTCMonth() + 1
    ).padStart(2, '0')}`;
}

function monthDifference(start, end) {
    return (
        (end.getUTCFullYear() - start.getUTCFullYear()) * 12 +
        end.getUTCMonth() - start.getUTCMonth()
    );
}


// ============================================================
// 4. CUSTOMER DOMAIN
// ============================================================

class Customer {
    constructor({
        id,
        name,
        email,
        acquisitionDate,
        region,
        monthlyRevenue = 0
    }) {
        this.id = requireString(id, 'Customer ID');
        this.name = requireString(name, 'Customer name');
        this.email = requireString(email, 'Email').toLowerCase();

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.email)) {
            throw new ValidationError('Invalid email address.');
        }

        this.acquisitionDate = requireDate(
            acquisitionDate,
            'Acquisition date'
        );

        this.region = requireString(region, 'Region');

        this.monthlyRevenue = requireFiniteNumber(
            monthlyRevenue,
            'Monthly revenue'
        );

        this.status = CUSTOMER_STATUS.ACTIVE;
        this.loyaltyTier = LOYALTY_TIERS.BRONZE;
        this.loyaltyPoints = 0;
        this.createdAt = new Date();
        this.updatedAt = new Date();
    }

    transition(nextStatus) {
        const allowed = {
            active: ['at_risk', 'churned'],
            at_risk: ['active', 'churned'],
            churned: ['reactivated'],
            reactivated: ['active', 'at_risk']
        };

        if (!allowed[this.status]?.includes(nextStatus)) {
            throw new ConflictError(
                `Invalid transition: ${this.status} -> ${nextStatus}`
            );
        }

        this.status = nextStatus;
        this.updatedAt = new Date();
    }
}


// ============================================================
// 5. EVENT-DRIVEN CUSTOMER ACTIVITY
// ============================================================

class CustomerEvent {
    constructor({
        id = crypto.randomUUID(),
        customerId,
        type,
        occurredAt = new Date(),
        amount = 0,
        metadata = {}
    }) {
        this.id = requireString(id, 'Event ID');
        this.customerId = requireString(
            customerId,
            'Customer ID'
        );

        if (!EVENT_TYPES.has(type)) {
            throw new ValidationError('Unsupported event type.');
        }

        this.type = type;
        this.occurredAt = requireDate(occurredAt, 'Event timestamp');
        this.amount = requireFiniteNumber(amount, 'Amount');

        if (type !== 'purchase' && type !== 'subscription' &&
            amount !== 0) {
            throw new ValidationError(
                'This event type cannot contain a monetary amount.'
            );
        }

        this.metadata = structuredClone(metadata);
    }
}


// ============================================================
// 6. EVENT BUS
// ============================================================

class CustomerEventBus extends EventEmitter {

    constructor() {
        super();
        this.setMaxListeners(50);
    }

    publish(event) {
        this.emit(event.type, event);
        this.emit('customer.activity', event);
    }
}


// ============================================================
// 7. CUSTOMER REPOSITORY
// ============================================================

class CustomerStore {

    constructor() {
        this.byId = new Map();
        this.byEmail = new Map();
    }

    add(customer) {
        if (this.byId.has(customer.id)) {
            throw new ConflictError('Duplicate customer ID.');
        }

        if (this.byEmail.has(customer.email)) {
            throw new ConflictError('Duplicate customer email.');
        }

        this.byId.set(customer.id, customer);
        this.byEmail.set(customer.email, customer.id);
    }

    get(id) {
        const customer = this.byId.get(id);

        if (!customer) {
            throw new NotFoundError(`Customer ${id} not found.`);
        }

        return customer;
    }

    values() {
        return [...this.byId.values()];
    }
}


// ============================================================
// 8. EVENT STORE
// ============================================================

class CustomerEventStore {

    constructor(customerStore, eventBus) {
        this.customerStore = customerStore;
        this.eventBus = eventBus;
        this.events = new Map();
        this.byCustomer = new Map();
    }

    record(event) {
        this.customerStore.get(event.customerId);

        if (this.events.has(event.id)) {
            throw new ConflictError('Duplicate event ID.');
        }

        this.events.set(event.id, event);

        const events = this.byCustomer.get(event.customerId) || [];
        events.push(event);

        this.byCustomer.set(event.customerId, events);

        this.eventBus.publish(event);
    }

    forCustomer(customerId) {
        this.customerStore.get(customerId);

        return [...(this.byCustomer.get(customerId) || [])]
            .sort(
                (a, b) =>
                    a.occurredAt.getTime() - b.occurredAt.getTime()
            );
    }

    all() {
        return [...this.events.values()];
    }
}


// ============================================================
// 9. CUSTOMER BEHAVIORAL SEGMENTATION
// ============================================================

class BehavioralSegmenter {

    evaluate(customer, events, referenceDate) {

        const purchases = events.filter(
            event =>
                event.type === 'purchase' &&
                event.occurredAt <= referenceDate
        );

        const lastPurchase = purchases.reduce(
            (latest, event) =>
                !latest || event.occurredAt > latest
                    ? event.occurredAt
                    : latest,
            null
        );

        const recency = lastPurchase
            ? daysBetween(referenceDate, lastPurchase)
            : daysBetween(referenceDate, customer.acquisitionDate);

        const frequency = purchases.length;

        const monetary = purchases.reduce(
            (total, event) => total + event.amount,
            0
        );

        const recentActivity = events.filter(
            event =>
                event.occurredAt <= referenceDate &&
                daysBetween(referenceDate, event.occurredAt) <= 30
        ).length;

        let segment;

        if (frequency === 0) {
            segment = 'non_purchasing';
        } else if (recency <= 30 && frequency >= 5) {
            segment = 'champions';
        } else if (recency <= 60) {
            segment = 'loyal';
        } else if (recency <= 90) {
            segment = 'at_risk';
        } else {
            segment = 'hibernating';
        }

        return Object.freeze({
            customerId: customer.id,
            recencyDays: recency,
            frequency,
            monetary: Number(monetary.toFixed(2)),
            recentActivity,
            segment
        });
    }
}


// ============================================================
// 10. CHURN POLICY ENGINE
// ============================================================

class ChurnPolicy {

    constructor({
        mediumThreshold = 0.35,
        highThreshold = 0.60
    } = {}) {
        if (
            mediumThreshold < 0 ||
            highThreshold > 1 ||
            mediumThreshold >= highThreshold
        ) {
            throw new ValidationError('Invalid churn thresholds.');
        }

        this.mediumThreshold = mediumThreshold;
        this.highThreshold = highThreshold;
    }

    evaluate(customer, events, referenceDate) {

        const purchases = events.filter(
            event =>
                event.type === 'purchase' &&
                event.occurredAt <= referenceDate
        );

        const lastPurchase = purchases.reduce(
            (latest, event) =>
                !latest || event.occurredAt > latest
                    ? event.occurredAt
                    : latest,
            null
        );

        const lastActivity = events.reduce(
            (latest, event) =>
                event.occurredAt <= referenceDate &&
                (!latest || event.occurredAt > latest)
                    ? event.occurredAt
                    : latest,
            null
        );

        const purchaseInactivity = lastPurchase
            ? daysBetween(referenceDate, lastPurchase)
            : daysBetween(referenceDate, customer.acquisitionDate);

        const generalInactivity = lastActivity
            ? daysBetween(referenceDate, lastActivity)
            : daysBetween(referenceDate, customer.acquisitionDate);

        let risk = 0.05;
        const factors = [];

        if (purchaseInactivity > 30) {
            risk += 0.20;
            factors.push('Purchase inactivity exceeds 30 days');
        }

        if (purchaseInactivity > 60) {
            risk += 0.20;
            factors.push('Purchase inactivity exceeds 60 days');
        }

        if (purchaseInactivity > 90) {
            risk += 0.20;
            factors.push('Purchase inactivity exceeds 90 days');
        }

        if (generalInactivity > 45) {
            risk += 0.15;
            factors.push('Low engagement');
        }

        if (purchases.length === 0) {
            risk += 0.15;
            factors.push('No purchase history');
        }

        const supportCount = events.filter(
            event =>
                event.type === 'support' &&
                daysBetween(referenceDate, event.occurredAt) <= 30
        ).length;

        if (supportCount >= 3) {
            risk += 0.10;
            factors.push('Repeated support interactions');
        }

        risk = Math.min(0.99, risk);

        return Object.freeze({
            customerId: customer.id,
            probability: Number(risk.toFixed(3)),
            riskLevel:
                risk >= this.highThreshold
                    ? 'high'
                    : risk >= this.mediumThreshold
                        ? 'medium'
                        : 'low',
            factors,
            assessedAt: new Date().toISOString()
        });
    }
}


// ============================================================
// 11. LOYALTY REWARDS ENGINE
// ============================================================

class LoyaltyEngine {

    constructor() {
        this.thresholds = [
            { tier: LOYALTY_TIERS.PLATINUM, amount: 10000, multiplier: 2 },
            { tier: LOYALTY_TIERS.GOLD, amount: 5000, multiplier: 1.5 },
            { tier: LOYALTY_TIERS.SILVER, amount: 2000, multiplier: 1.25 },
            { tier: LOYALTY_TIERS.BRONZE, amount: 0, multiplier: 1 }
        ];
    }

    calculateSpend(events) {
        return events
            .filter(event => event.type === 'purchase')
            .reduce((total, event) => total + event.amount, 0);
    }

    update(customer, events) {
        const spend = this.calculateSpend(events);

        const level = this.thresholds.find(
            item => spend >= item.amount
        );

        customer.loyaltyTier = level.tier;

        return {
            tier: level.tier,
            lifetimeSpend: Number(spend.toFixed(2)),
            multiplier: level.multiplier
        };
    }

    awardPoints(customer, purchaseAmount, events) {
        requireFiniteNumber(purchaseAmount, 'Purchase amount');

        const loyalty = this.update(customer, events);

        const points = Math.floor(
            purchaseAmount * loyalty.multiplier
        );

        customer.loyaltyPoints += points;

        return points;
    }
}


// ============================================================
// 12. COHORT ANALYTICS
// ============================================================

class CohortAnalytics {

    calculate(customers, events) {

        const cohortMembers = new Map();
        const activity = new Map();
        const customerIndex = new Map(
            customers.map(customer => [customer.id, customer])
        );

        for (const customer of customers) {
            const key = monthKey(customer.acquisitionDate);

            if (!cohortMembers.has(key)) {
                cohortMembers.set(key, new Set());
            }

            cohortMembers.get(key).add(customer.id);
        }

        for (const event of events) {

            if (!['purchase', 'login'].includes(event.type)) {
                continue;
            }

            const customer = customerIndex.get(event.customerId);

            if (!customer) continue;

            const cohort = monthKey(customer.acquisitionDate);

            const period = monthDifference(
                customer.acquisitionDate,
                event.occurredAt
            );

            if (period < 0) continue;

            const key = `${cohort}:${period}`;

            if (!activity.has(key)) {
                activity.set(key, new Set());
            }

            activity.get(key).add(customer.id);
        }

        const output = {};

        for (const [cohort, members] of cohortMembers) {

            const periods = {};

            for (const [key, activeCustomers] of activity) {
                const [currentCohort, period] = key.split(':');

                if (currentCohort !== cohort) continue;

                periods[period] = Number(
                    (
                        activeCustomers.size /
                        members.size * 100
                    ).toFixed(2)
                );
            }

            output[cohort] = {
                cohortSize: members.size,
                retention: periods
            };
        }

        return output;
    }
}


// ============================================================
// 13. CAMPAIGN STATE MACHINE
// ============================================================

class RetentionCampaign {

    constructor({
        id,
        name,
        type,
        budget,
        contactCost,
        targetStatus
    }) {
        this.id = requireString(id, 'Campaign ID');
        this.name = requireString(name, 'Campaign name');

        this.type = requireString(type, 'Campaign type');

        this.budget = requireFiniteNumber(budget, 'Budget');
        this.contactCost = requireFiniteNumber(
            contactCost,
            'Contact cost'
        );

        this.targetStatus = targetStatus;
        this.state = CAMPAIGN_STATES.DRAFT;

        this.assignments = new Set();
        this.conversions = new Set();
    }

    activate() {
        if (this.state !== CAMPAIGN_STATES.DRAFT) {
            throw new ConflictError('Campaign cannot be activated.');
        }

        this.state = CAMPAIGN_STATES.ACTIVE;
    }

    pause() {
        if (this.state !== CAMPAIGN_STATES.ACTIVE) {
            throw new ConflictError('Only active campaigns can pause.');
        }

        this.state = CAMPAIGN_STATES.PAUSED;
    }

    assign(customer) {
        if (this.state !== CAMPAIGN_STATES.ACTIVE) {
            throw new ConflictError('Campaign is not active.');
        }

        if (customer.status !== this.targetStatus) {
            throw new ConflictError('Customer does not match target.');
        }

        if (this.assignments.has(customer.id)) {
            throw new ConflictError('Duplicate campaign assignment.');
        }

        const nextCost =
            (this.assignments.size + 1) * this.contactCost;

        if (nextCost > this.budget) {
            throw new BudgetExceededError('Campaign budget exceeded.');
        }

        this.assignments.add(customer.id);
    }

    convert(customerId) {
        if (!this.assignments.has(customerId)) {
            throw new ConflictError('Customer was not assigned.');
        }

        this.conversions.add(customerId);
    }

    report(revenuePerConversion) {
        requireFiniteNumber(
            revenuePerConversion,
            'Revenue per conversion'
        );

        const contacted = this.assignments.size;
        const converted = this.conversions.size;

        const cost = contacted * this.contactCost;
        const revenue = converted * revenuePerConversion;

        return {
            campaignId: this.id,
            contacted,
            converted,
            conversionRate: contacted
                ? Number((converted / contacted * 100).toFixed(2))
                : 0,
            cost,
            revenue,
            roi: cost
                ? Number(((revenue - cost) / cost * 100).toFixed(2))
                : 0
        };
    }
}


// ============================================================
// 14. ASYNCHRONOUS ANALYTICS SERVICE
// ============================================================

class RetentionAnalyticsService {

    constructor() {
        this.customers = new CustomerStore();
        this.eventBus = new CustomerEventBus();

        this.events = new CustomerEventStore(
            this.customers,
            this.eventBus
        );

        this.segmenter = new BehavioralSegmenter();
        this.churnPolicy = new ChurnPolicy();
        this.loyalty = new LoyaltyEngine();
        this.cohorts = new CohortAnalytics();

        this.eventBus.on('purchase', event => {
            this.eventBus.emit('revenue.recorded', {
                customerId: event.customerId,
                amount: event.amount
            });
        });
    }

    addCustomer(customer) {
        this.customers.add(customer);
    }

    recordEvent(event) {
        this.events.record(event);
    }

    analyze(customerId, referenceDate) {

        const customer = this.customers.get(customerId);
        const events = this.events.forCustomer(customerId);

        const churn = this.churnPolicy.evaluate(
            customer,
            events,
            referenceDate
        );

        const segment = this.segmenter.evaluate(
            customer,
            events,
            referenceDate
        );

        const loyalty = this.loyalty.update(
            customer,
            events
        );

        let nextStatus = customer.status;

        if (churn.riskLevel === 'high') {
            nextStatus = CUSTOMER_STATUS.AT_RISK;
        } else if (
            customer.status === CUSTOMER_STATUS.AT_RISK
        ) {
            nextStatus = CUSTOMER_STATUS.ACTIVE;
        }

        if (nextStatus !== customer.status) {
            customer.transition(nextStatus);
        }

        return {
            customerId,
            status: customer.status,
            churn,
            segment,
            loyalty
        };
    }

    async analyzeAll(referenceDate) {

        const customers = this.customers.values();

        // Bounded concurrency prevents large batches from exhausting
        // the event loop or downstream resources.
        const concurrency = 20;
        const results = [];

        for (let index = 0; index < customers.length;
             index += concurrency) {

            const batch = customers.slice(
                index,
                index + concurrency
            );

            const batchResults = await Promise.all(
                batch.map(async customer => {
                    await Promise.resolve();

                    return this.analyze(
                        customer.id,
                        referenceDate
                    );
                })
            );

            results.push(...batchResults);
        }

        return results;
    }

    report(results) {

        const distribution = {
            low: 0,
            medium: 0,
            high: 0
        };

        for (const item of results) {
            distribution[item.churn.riskLevel]++;
        }

        const averageScore = results.length
            ? results.reduce(
                (sum, item) => sum + item.segment.recentActivity,
                0
            ) / results.length
            : 0;

        return {
            generatedAt: new Date().toISOString(),
            customerCount: results.length,
            riskDistribution: distribution,
            highRiskPercentage: results.length
                ? Number(
                    (
                        distribution.high /
                        results.length * 100
                    ).toFixed(2)
                )
                : 0,
            averageRecentActivity: Number(
                averageScore.toFixed(2)
            ),
            customers: results
        };
    }
}


// ============================================================
// 15. CLV CALCULATOR
// ============================================================

function calculateCLV({
    monthlyRevenue,
    grossMargin,
    monthlyChurnRate
}) {
    requireFiniteNumber(monthlyRevenue, 'Monthly revenue');

    if (grossMargin < 0 || grossMargin > 1) {
        throw new ValidationError('Invalid gross margin.');
    }

    if (
        monthlyChurnRate <= 0 ||
        monthlyChurnRate > 1
    ) {
        throw new ValidationError('Invalid churn rate.');
    }

    return Number(
        (
            monthlyRevenue *
            grossMargin /
            monthlyChurnRate
        ).toFixed(2)
    );
}


// ============================================================
// 16. REPORT EXPORT
// ============================================================

async function exportReport(filename, data) {

    const directory = path.dirname(filename);

    await fs.mkdir(directory, { recursive: true });

    const temporary = `${filename}.tmp`;

    try {
        await fs.writeFile(
            temporary,
            JSON.stringify(data, null, 2),
            {
                encoding: 'utf8',
                flag: 'wx',
                mode: 0o600
            }
        );

        await fs.rename(temporary, filename);

    } catch (error) {
        await fs.rm(temporary, { force: true }).catch(() => {});
        throw error;
    }
}


// ============================================================
// 17. SAMPLE APPLICATION
// ============================================================

async function main() {

    const service = new RetentionAnalyticsService();

    const referenceDate = new Date('2026-11-27T00:00:00Z');

    const customers = [
        new Customer({
            id: 'C001',
            name: 'Aarav Sharma',
            email: 'aarav@example.com',
            acquisitionDate: '2026-01-10',
            region: 'North',
            monthlyRevenue: 999
        }),
        new Customer({
            id: 'C002',
            name: 'Priya Verma',
            email: 'priya@example.com',
            acquisitionDate: '2026-02-15',
            region: 'South',
            monthlyRevenue: 1499
        }),
        new Customer({
            id: 'C003',
            name: 'Rahul Singh',
            email: 'rahul@example.com',
            acquisitionDate: '2026-03-20',
            region: 'West',
            monthlyRevenue: 799
        }),
        new Customer({
            id: 'C004',
            name: 'Ananya Gupta',
            email: 'ananya@example.com',
            acquisitionDate: '2026-04-05',
            region: 'East',
            monthlyRevenue: 1999
        })
    ];

    customers.forEach(customer => service.addCustomer(customer));

    const events = [
        ['E001', 'C001', 'purchase', 5, 3000],
        ['E002', 'C001', 'purchase', 35, 2500],
        ['E003', 'C001', 'login', 1, 0],
        ['E004', 'C002', 'purchase', 15, 1500],
        ['E005', 'C002', 'login', 2, 0],
        ['E006', 'C003', 'purchase', 110, 700],
        ['E007', 'C004', 'purchase', 80, 8000],
        ['E008', 'C004', 'support', 10, 0],
        ['E009', 'C004', 'support', 8, 0],
        ['E010', 'C004', 'support', 5, 0]
    ];

    for (const [id, customerId, type, daysAgo, amount] of events) {

        const occurredAt = new Date(
            referenceDate.getTime() - daysAgo * 86400000
        );

        service.recordEvent(
            new CustomerEvent({
                id,
                customerId,
                type,
                occurredAt,
                amount
            })
        );
    }

    const results = await service.analyzeAll(referenceDate);

    const retentionReport = service.report(results);

    const cohortReport = service.cohorts.calculate(
        customers,
        service.events.all()
    );

    const campaign = new RetentionCampaign({
        id: 'CMP001',
        name: 'November Reactivation',
        type: 'reactivation',
        budget: 1000,
        contactCost: 50,
        targetStatus: CUSTOMER_STATUS.AT_RISK
    });

    campaign.activate();

    for (const customer of customers) {
        if (customer.status === CUSTOMER_STATUS.AT_RISK) {
            campaign.assign(customer);
        }
    }

    const firstAssignment = [...campaign.assignments][0];

    if (firstAssignment) {
        campaign.convert(firstAssignment);
    }

    const campaignReport = campaign.report(1500);

    const clv = calculateCLV({
        monthlyRevenue: 1500,
        grossMargin: 0.65,
        monthlyChurnRate: 0.04
    });

    await exportReport(
        'output/retention-report.json',
        retentionReport
    );

    await exportReport(
        'output/cohort-report.json',
        cohortReport
    );

    await exportReport(
        'output/campaign-report.json',
        campaignReport
    );

    console.log('\nRETENTION ANALYTICS');
    console.log(JSON.stringify(retentionReport, null, 2));

    console.log('\nCOHORT RETENTION');
    console.log(JSON.stringify(cohortReport, null, 2));

    console.log('\nCAMPAIGN PERFORMANCE');
    console.log(JSON.stringify(campaignReport, null, 2));

    console.log('\nESTIMATED CUSTOMER LIFETIME VALUE');
    console.log(clv);
}


// ============================================================
// 18. APPLICATION EXECUTION
// ============================================================

main().catch(error => {
    console.error('Application failure:', error.message);
    process.exitCode = 1;
});
