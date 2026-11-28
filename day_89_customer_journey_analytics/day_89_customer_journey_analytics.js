"use strict";

/*
 * Customer Journey Analytics
 * Event-driven behavioral analytics using Node.js 18+.
 *
 * Features:
 * - Event collection and validation
 * - Consent-aware ingestion
 * - Asynchronous processing
 * - Identity resolution
 * - Session management
 * - Journey transitions
 * - Funnel conversion
 * - Multi-touch attribution
 * - Behavioral segmentation
 * - Revenue analysis
 * - Event deduplication
 */

const { EventEmitter } = require("node:events");
const { randomUUID } = require("node:crypto");
const fs = require("node:fs/promises");

// ============================================================
// 1. DOMAIN CONSTANTS
// ============================================================

const EventType = Object.freeze({
    IMPRESSION: "ad_impression",
    CLICK: "ad_click",
    PAGE_VIEW: "page_view",
    PRODUCT_VIEW: "product_view",
    SEARCH: "search",
    ADD_TO_CART: "add_to_cart",
    CHECKOUT: "checkout",
    PURCHASE: "purchase",
    SIGNUP: "signup",
    SUPPORT: "support_request"
});

const Channels = Object.freeze([
    "organic_search",
    "paid_search",
    "social",
    "email",
    "direct",
    "referral",
    "display"
]);

const JourneyStages = Object.freeze({
    awareness: ["ad_impression", "ad_click", "page_view"],
    consideration: ["search", "product_view", "add_to_cart"],
    conversion: ["checkout", "purchase"],
    retention: ["signup", "support_request"]
});

const ALLOWED_PROPERTIES = new Set([
    "device_type",
    "browser",
    "country",
    "experiment",
    "campaign_group"
]);

// ============================================================
// 2. CUSTOM ERRORS
// ============================================================

class AnalyticsError extends Error {
    constructor(message) {
        super(message);
        this.name = "AnalyticsError";
    }
}

class ValidationError extends AnalyticsError {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class ConsentError extends AnalyticsError {
    constructor(message) {
        super(message);
        this.name = "ConsentError";
    }
}

// ============================================================
// 3. EVENT VALIDATION
// ============================================================

class EventValidator {

    static validate(event) {
        if (!event || typeof event !== "object") {
            throw new ValidationError("Event must be an object.");
        }

        const required = [
            "eventId",
            "customerId",
            "sessionId",
            "type",
            "timestamp",
            "channel",
            "page"
        ];

        for (const field of required) {
            if (event[field] === undefined || event[field] === null ||
                event[field] === "") {
                throw new ValidationError(`${field} is required.`);
            }
        }

        if (!Object.values(EventType).includes(event.type)) {
            throw new ValidationError("Unsupported event type.");
        }

        if (!Channels.includes(event.channel)) {
            throw new ValidationError("Unsupported channel.");
        }

        if (!Number.isFinite(Date.parse(event.timestamp))) {
            throw new ValidationError("Invalid event timestamp.");
        }

        if (typeof event.page !== "string" || event.page.length > 500) {
            throw new ValidationError("Invalid page identifier.");
        }

        const value = event.value ?? 0;

        if (!Number.isFinite(value) || value < 0) {
            throw new ValidationError("Invalid event monetary value.");
        }

        if (event.type === EventType.PURCHASE && value <= 0) {
            throw new ValidationError("Purchase value must be positive.");
        }

        const properties = event.properties ?? {};

        if (typeof properties !== "object" || Array.isArray(properties)) {
            throw new ValidationError("Properties must be an object.");
        }

        for (const key of Object.keys(properties)) {
            if (!ALLOWED_PROPERTIES.has(key)) {
                throw new ValidationError(`Unsupported property: ${key}`);
            }
        }

        return {
            ...event,
            value,
            properties: { ...properties }
        };
    }
}

// ============================================================
// 4. CUSTOMER IDENTITY MANAGEMENT
// ============================================================

class IdentityRegistry {

    constructor() {
        this.identities = new Map();
    }

    register(customerId, identifiers = []) {
        if (!customerId) {
            throw new ValidationError("Customer ID is required.");
        }

        for (const identifier of identifiers) {
            if (!identifier || typeof identifier !== "string") {
                throw new ValidationError("Invalid identity identifier.");
            }

            const owner = this.identities.get(identifier);

            if (owner && owner !== customerId) {
                throw new AnalyticsError(
                    "Identity is already associated with another customer."
                );
            }
        }

        for (const identifier of identifiers) {
            this.identities.set(identifier, customerId);
        }
    }

    resolve(identifier) {
        return this.identities.get(identifier) ?? null;
    }

    removeCustomer(customerId) {
        for (const [identifier, owner] of this.identities) {
            if (owner === customerId) {
                this.identities.delete(identifier);
            }
        }
    }
}

// ============================================================
// 5. EVENT-DRIVEN ANALYTICS COLLECTOR
// ============================================================

class JourneyCollector extends EventEmitter {

    constructor() {
        super();

        this.customers = new Map();
        this.events = new Map();
        this.customerEvents = new Map();
        this.identities = new IdentityRegistry();

        this.processing = Promise.resolve();
        this.closed = false;

        this.setMaxListeners(50);
    }

    registerCustomer(customer) {
        if (!customer?.customerId) {
            throw new ValidationError("Customer ID is required.");
        }

        if (!["granted", "denied", "unknown"].includes(customer.consent)) {
            throw new ValidationError("Invalid consent status.");
        }

        this.customers.set(customer.customerId, {
            ...customer
        });
    }

    ingest(rawEvent) {
        if (this.closed) {
            throw new AnalyticsError("Collector is closed.");
        }

        const event = EventValidator.validate(rawEvent);

        const customer = this.customers.get(event.customerId);

        if (!customer) {
            throw new AnalyticsError("Unknown customer.");
        }

        if (customer.consent !== "granted") {
            throw new ConsentError("Analytics consent is not granted.");
        }

        if (this.events.has(event.eventId)) {
            return false;
        }

        this.events.set(event.eventId, event);

        if (!this.customerEvents.has(event.customerId)) {
            this.customerEvents.set(event.customerId, []);
        }

        this.customerEvents.get(event.customerId).push(event);

        // Event listeners receive immutable event snapshots.
        this.emit("event:received", Object.freeze({ ...event }));

        return true;
    }

    ingestAsync(event) {
        // Serialize writes to maintain predictable event ordering.
        const operation = this.processing.then(() => this.ingest(event));

        this.processing = operation.catch(() => undefined);

        return operation;
    }

    getCustomerEvents(customerId) {
        return [...(this.customerEvents.get(customerId) ?? [])]
            .sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));
    }

    getAllEvents() {
        return [...this.events.values()]
            .sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));
    }

    async flush() {
        await this.processing;
    }

    eraseCustomer(customerId) {
        const customerEventList = this.customerEvents.get(customerId) ?? [];

        for (const event of customerEventList) {
            this.events.delete(event.eventId);
        }

        this.customerEvents.delete(customerId);
        this.customers.delete(customerId);
        this.identities.removeCustomer(customerId);

        this.emit("customer:erased", customerId);
    }

    close() {
        this.closed = true;
        this.removeAllListeners();
    }
}

// ============================================================
// 6. JOURNEY STATE ENGINE
// ============================================================

class JourneyStateEngine {

    constructor() {
        this.states = new Map();
        this.transitions = new Map();
    }

    process(event) {
        const customerId = event.customerId;

        const previous = this.states.get(customerId) ?? "unknown";

        let current = previous;

        for (const [stage, eventTypes] of Object.entries(JourneyStages)) {
            if (eventTypes.includes(event.type)) {
                current = stage;
                break;
            }
        }

        const transition = {
            customerId,
            previous,
            current,
            eventType: event.type,
            timestamp: event.timestamp
        };

        this.states.set(customerId, current);

        if (!this.transitions.has(customerId)) {
            this.transitions.set(customerId, []);
        }

        this.transitions.get(customerId).push(transition);

        return transition;
    }

    getHistory(customerId) {
        return [...(this.transitions.get(customerId) ?? [])];
    }
}

// ============================================================
// 7. SESSION ANALYTICS
// ============================================================

class SessionAnalyzer {

    constructor(inactivityMilliseconds = 30 * 60 * 1000) {
        if (!Number.isFinite(inactivityMilliseconds) ||
            inactivityMilliseconds <= 0) {
            throw new ValidationError("Invalid session timeout.");
        }

        this.timeout = inactivityMilliseconds;
    }

    analyze(events) {
        const grouped = new Map();

        for (const event of events) {
            if (!grouped.has(event.customerId)) {
                grouped.set(event.customerId, []);
            }

            grouped.get(event.customerId).push(event);
        }

        const sessions = [];

        for (const [customerId, customerEvents] of grouped) {
            customerEvents.sort(
                (a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp)
            );

            let current = null;

            for (const event of customerEvents) {
                const timestamp = Date.parse(event.timestamp);

                const newSession = !current ||
                    current.sessionId !== event.sessionId ||
                    timestamp - current.lastActivity > this.timeout;

                if (newSession) {
                    current = {
                        customerId,
                        sessionId: event.sessionId,
                        start: timestamp,
                        end: timestamp,
                        lastActivity: timestamp,
                        events: []
                    };

                    sessions.push(current);
                }

                current.events.push(event);
                current.end = timestamp;
                current.lastActivity = timestamp;
            }
        }

        return sessions.map(session => ({
            customerId: session.customerId,
            sessionId: session.sessionId,
            eventCount: session.events.length,
            durationSeconds: (session.end - session.start) / 1000,
            entryChannel: session.events[0].channel,
            exitPage: session.events.at(-1).page
        }));
    }
}

// ============================================================
// 8. FUNNEL ANALYTICS
// ============================================================

class FunnelAnalyzer {

    constructor(stages = [
        EventType.PAGE_VIEW,
        EventType.PRODUCT_VIEW,
        EventType.ADD_TO_CART,
        EventType.CHECKOUT,
        EventType.PURCHASE
    ]) {
        if (!Array.isArray(stages) || stages.length === 0 ||
            new Set(stages).size !== stages.length) {
            throw new ValidationError("Funnel stages must be unique.");
        }

        this.stages = [...stages];
    }

    calculate(events) {
        const customers = new Map();

        for (const event of events) {
            if (!customers.has(event.customerId)) {
                customers.set(event.customerId, []);
            }

            customers.get(event.customerId).push(event);
        }

        const counts = new Array(this.stages.length).fill(0);

        for (const customerEvents of customers.values()) {
            customerEvents.sort(
                (a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp)
            );

            let stageIndex = 0;

            for (const event of customerEvents) {
                if (event.type === this.stages[stageIndex]) {
                    counts[stageIndex]++;

                    stageIndex++;

                    if (stageIndex === this.stages.length) {
                        break;
                    }
                }
            }
        }

        const results = this.stages.map((stage, index) => {
            const previous = index === 0 ? counts[index] : counts[index - 1];

            return {
                stage,
                customers: counts[index],
                conversionRate: previous
                    ? counts[index] / previous
                    : 0,
                dropOff: index === 0 || !previous
                    ? 0
                    : 1 - counts[index] / previous
            };
        });

        return {
            stages: results,
            overallConversion: counts[0]
                ? counts.at(-1) / counts[0]
                : 0
        };
    }
}

// ============================================================
// 9. ATTRIBUTION ENGINE
// ============================================================

class AttributionEngine {

    static calculate(events, model = "linear") {
        if (!events.length) return {};

        const ordered = [...events].sort(
            (a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp)
        );

        const credits = new Map();

        const addCredit = (channel, value) => {
            credits.set(channel, (credits.get(channel) ?? 0) + value);
        };

        if (model === "first_touch") {
            addCredit(ordered[0].channel, 1);
        } else if (model === "last_touch") {
            addCredit(ordered.at(-1).channel, 1);
        } else if (model === "linear") {
            for (const event of ordered) {
                addCredit(event.channel, 1 / ordered.length);
            }
        } else if (model === "position_based") {
            if (ordered.length === 1) {
                addCredit(ordered[0].channel, 1);
            } else {
                addCredit(ordered[0].channel, 0.4);
                addCredit(ordered.at(-1).channel, 0.4);

                const middle = ordered.slice(1, -1);

                if (middle.length) {
                    const credit = 0.2 / middle.length;

                    for (const event of middle) {
                        addCredit(event.channel, credit);
                    }
                }
            }
        } else {
            throw new ValidationError("Unsupported attribution model.");
        }

        return Object.fromEntries(credits);
    }

    static allocateRevenue(revenue, attribution) {
        if (!Number.isFinite(revenue) || revenue < 0) {
            throw new ValidationError("Invalid revenue.");
        }

        const weights = Object.values(attribution);
        const total = weights.reduce((sum, weight) => sum + weight, 0);

        if (Math.abs(total - 1) > 1e-9) {
            throw new ValidationError("Attribution must total 100%.");
        }

        return Object.fromEntries(
            Object.entries(attribution).map(([channel, weight]) => [
                channel,
                Number((revenue * weight).toFixed(2))
            ])
        );
    }
}

// ============================================================
// 10. CUSTOMER SEGMENTATION
// ============================================================

class CustomerSegmenter {

    static classify(events) {
        const profiles = new Map();

        for (const event of events) {
            if (!profiles.has(event.customerId)) {
                profiles.set(event.customerId, {
                    events: 0,
                    purchases: 0,
                    revenue: 0,
                    cartEvents: 0,
                    supportRequests: 0
                });
            }

            const profile = profiles.get(event.customerId);

            profile.events++;

            if (event.type === EventType.PURCHASE) {
                profile.purchases++;
                profile.revenue += event.value;
            }

            if (event.type === EventType.ADD_TO_CART) {
                profile.cartEvents++;
            }

            if (event.type === EventType.SUPPORT) {
                profile.supportRequests++;
            }
        }

        const segments = new Map();

        for (const [customerId, profile] of profiles) {
            let segment = "visitor";

            if (profile.purchases > 0) {
                segment = profile.purchases > 1
                    ? "repeat_customer"
                    : "converted_customer";
            } else if (profile.cartEvents > 0) {
                segment = "cart_abandoner";
            } else if (profile.events > 3) {
                segment = "engaged_visitor";
            }

            if (profile.supportRequests > 0) {
                segment = "support_engaged";
            }

            segments.set(customerId, {
                segment,
                ...profile,
                revenue: Number(profile.revenue.toFixed(2))
            });
        }

        return Object.fromEntries(segments);
    }
}

// ============================================================
// 11. COHORT RETENTION
// ============================================================

class CohortAnalyzer {

    static analyze(customers, events) {
        const month = timestamp => timestamp.slice(0, 7);

        const customerMap = new Map(
            customers.map(customer => [
                customer.customerId,
                customer
            ])
        );

        const cohorts = new Map();

        for (const customer of customers) {
            const cohortMonth = month(customer.registeredAt);

            if (!cohorts.has(cohortMonth)) {
                cohorts.set(cohortMonth, new Set());
            }

            cohorts.get(cohortMonth).add(customer.customerId);
        }

        const activity = new Map();

        for (const event of events) {
            if (!customerMap.has(event.customerId)) continue;

            const key = `${event.customerId}:${month(event.timestamp)}`;
            activity.set(key, true);
        }

        const result = [];

        for (const [cohortMonth, customerIds] of cohorts) {
            const counts = new Map();

            for (const customerId of customerIds) {
                for (const event of events) {
                    if (event.customerId !== customerId) continue;

                    const activityMonth = month(event.timestamp);

                    if (activityMonth < cohortMonth) continue;

                    counts.set(
                        activityMonth,
                        (counts.get(activityMonth) ?? 0) + 1
                    );
                }
            }

            for (const [activityMonth, activeCount] of counts) {
                const uniqueActive = [...customerIds].filter(id =>
                    activity.has(`${id}:${activityMonth}`)
                ).length;

                result.push({
                    cohortMonth,
                    activityMonth,
                    cohortSize: customerIds.size,
                    activeCustomers: uniqueActive,
                    retentionRate: uniqueActive / customerIds.size
                });
            }
        }

        return result.sort((a, b) =>
            a.cohortMonth.localeCompare(b.cohortMonth) ||
            a.activityMonth.localeCompare(b.activityMonth)
        );
    }
}

// ============================================================
// 12. REPORTING SERVICE
// ============================================================

class AnalyticsReportService {

    constructor(collector) {
        this.collector = collector;
        this.funnel = new FunnelAnalyzer();
        this.sessions = new SessionAnalyzer();
    }

    generate() {
        const events = this.collector.getAllEvents();

        const purchases = events.filter(
            event => event.type === EventType.PURCHASE
        );

        const customers = new Set(
            events.map(event => event.customerId)
        );

        const revenue = purchases.reduce(
            (sum, event) => sum + event.value,
            0
        );

        const channelMetrics = new Map();

        for (const event of events) {
            if (!channelMetrics.has(event.channel)) {
                channelMetrics.set(event.channel, {
                    events: 0,
                    customers: new Set(),
                    purchases: 0,
                    revenue: 0
                });
            }

            const metric = channelMetrics.get(event.channel);

            metric.events++;
            metric.customers.add(event.customerId);

            if (event.type === EventType.PURCHASE) {
                metric.purchases++;
                metric.revenue += event.value;
            }
        }

        const channels = [...channelMetrics.entries()].map(
            ([channel, metric]) => ({
                channel,
                events: metric.events,
                customers: metric.customers.size,
                purchases: metric.purchases,
                revenue: Number(metric.revenue.toFixed(2))
            })
        ).sort((a, b) => b.revenue - a.revenue);

        return {
            generatedAt: new Date().toISOString(),
            totalEvents: events.length,
            uniqueCustomers: customers.size,
            totalPurchases: purchases.length,
            revenue: Number(revenue.toFixed(2)),
            averageOrderValue: purchases.length
                ? Number((revenue / purchases.length).toFixed(2))
                : 0,
            funnel: this.funnel.calculate(events),
            sessions: this.sessions.analyze(events),
            channels,
            segments: CustomerSegmenter.classify(events)
        };
    }
}

// ============================================================
// 13. ASYNCHRONOUS FILE EXPORT
// ============================================================

async function exportReport(report, filename) {
    if (!filename.endsWith(".json")) {
        throw new ValidationError("Only JSON exports are supported.");
    }

    const serialized = JSON.stringify(report, null, 2);

    await fs.writeFile(filename, serialized, {
        encoding: "utf8",
        mode: 0o600,
        flag: "w"
    });
}

// ============================================================
// 14. DEMONSTRATION DATA
// ============================================================

function createDemoData(collector) {
    const customers = [
        {
            customerId: "C001",
            consent: "granted",
            registeredAt: "2026-10-01T09:00:00.000Z"
        },
        {
            customerId: "C002",
            consent: "granted",
            registeredAt: "2026-10-02T09:00:00.000Z"
        },
        {
            customerId: "C003",
            consent: "granted",
            registeredAt: "2026-10-03T09:00:00.000Z"
        },
        {
            customerId: "C004",
            consent: "granted",
            registeredAt: "2026-10-04T09:00:00.000Z"
        },
        {
            customerId: "C005",
            consent: "denied",
            registeredAt: "2026-10-05T09:00:00.000Z"
        }
    ];

    customers.forEach(customer => collector.registerCustomer(customer));

    const definitions = {
        C001: [
            ["ad_click", "social", 0],
            ["page_view", "organic_search", 2],
            ["product_view", "organic_search", 5],
            ["add_to_cart", "organic_search", 10],
            ["checkout", "organic_search", 15],
            ["purchase", "organic_search", 20]
        ],
        C002: [
            ["ad_click", "paid_search", 0],
            ["page_view", "paid_search", 3],
            ["product_view", "paid_search", 7],
            ["add_to_cart", "paid_search", 12]
        ],
        C003: [
            ["page_view", "direct", 0],
            ["product_view", "direct", 4],
            ["checkout", "direct", 8],
            ["purchase", "direct", 12]
        ],
        C004: [
            ["ad_impression", "display", 0],
            ["page_view", "email", 3],
            ["product_view", "email", 7]
        ]
    };

    const base = Date.parse("2026-10-01T09:00:00.000Z");

    for (const [customerId, journey] of Object.entries(definitions)) {
        const dayOffset = Number(customerId.slice(-1));

        journey.forEach(([type, channel, minute], index) => {
            const event = {
                eventId: randomUUID(),
                customerId,
                sessionId: `SESSION-${customerId}`,
                type,
                timestamp: new Date(
                    base + dayOffset * 86400000 + minute * 60000
                ).toISOString(),
                channel,
                page: `/${type}`,
                campaign: "AUTUMN-2026",
                value: type === "purchase" ? 1499 : 0,
                properties: {
                    device_type: "desktop"
                }
            };

            collector.ingest(event);
        });
    }

    return customers;
}

// ============================================================
// 15. AUTOMATED TESTS
// ============================================================

async function runTests(collector) {
    const events = collector.getAllEvents();

    console.assert(events.length === 17, "Expected 17 events.");

    console.assert(
        new Set(events.map(event => event.customerId)).size === 4,
        "Expected four consented customers."
    );

    const funnel = new FunnelAnalyzer().calculate(events);

    console.assert(
        funnel.overallConversion >= 0 &&
        funnel.overallConversion <= 1,
        "Invalid funnel conversion."
    );

    const attribution = AttributionEngine.calculate(
        collector.getCustomerEvents("C001"),
        "linear"
    );

    const totalCredit = Object.values(attribution)
        .reduce((sum, value) => sum + value, 0);

    console.assert(
        Math.abs(totalCredit - 1) < 1e-9,
        "Attribution weights must total one."
    );

    const duplicate = collector.getAllEvents()[0];

    console.assert(
        collector.ingest(duplicate) === false,
        "Duplicate event should be rejected."
    );

    let consentRejected = false;

    try {
        collector.ingest({
            eventId: randomUUID(),
            customerId: "C005",
            sessionId: "SESSION-C005",
            type: EventType.PAGE_VIEW,
            timestamp: new Date().toISOString(),
            channel: "direct",
            page: "/home",
            value: 0
        });
    } catch (error) {
        consentRejected = error instanceof ConsentError;
    }

    console.assert(consentRejected, "Consent enforcement failed.");

    console.log("Automated checks completed.");
}

// ============================================================
// 16. APPLICATION ENTRY POINT
// ============================================================

async function main() {
    const collector = new JourneyCollector();

    collector.on("event:received", event => {
        if (event.type === EventType.PURCHASE) {
            console.log(
                `Purchase received: ${event.customerId}, ₹${event.value}`
            );
        }
    });

    const customers = createDemoData(collector);

    await collector.flush();

    const stateEngine = new JourneyStateEngine();

    for (const event of collector.getAllEvents()) {
        stateEngine.process(event);
    }

    const reports = new AnalyticsReportService(collector);
    const report = reports.generate();

    console.log("\nCUSTOMER JOURNEY ANALYTICS");
    console.log(JSON.stringify(report, null, 2));

    console.log("\nC001 ATTRIBUTION");

    for (const model of [
        "first_touch",
        "last_touch",
        "linear",
        "position_based"
    ]) {
        const attribution = AttributionEngine.calculate(
            collector.getCustomerEvents("C001"),
            model
        );

        console.log(model, attribution);
    }

    console.log("\nCUSTOMER JOURNEY TRANSITIONS");
    console.log(stateEngine.getHistory("C001"));

    console.log("\nCOHORT RETENTION");
    console.log(CohortAnalyzer.analyze(
        customers.filter(customer => customer.consent === "granted"),
        collector.getAllEvents()
    ));

    await runTests(collector);

    collector.close();
}

main().catch(error => {
    console.error("Analytics execution failed:", error.message);
    process.exitCode = 1;
});
