"use strict";

/*
 * Conversion Analytics and Funnel Optimization
 * Node.js 18+
 *
 * Event-driven analytics engine with:
 * - Event ingestion and deduplication
 * - Funnel state tracking
 * - Conversion measurement
 * - Channel attribution
 * - Revenue analysis
 * - Cohort reporting
 * - A/B testing
 * - Funnel bottleneck detection
 * - Asynchronous batch processing
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");


// ---------------------------------------------------------
// 1. DOMAIN CONFIGURATION
// ---------------------------------------------------------

const STAGES = Object.freeze([
    "visit",
    "product_view",
    "add_to_cart",
    "checkout",
    "purchase"
]);

const STAGE_INDEX = new Map(
    STAGES.map((stage, index) => [stage, index])
);

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class AnalyticsError extends Error {
    constructor(message) {
        super(message);
        this.name = "AnalyticsError";
    }
}


// ---------------------------------------------------------
// 2. EVENT VALIDATION
// ---------------------------------------------------------

function validateEvent(event) {
    if (!event || typeof event !== "object") {
        throw new ValidationError("Event must be an object");
    }

    const required = [
        "eventId",
        "userId",
        "type",
        "timestamp",
        "channel",
        "campaign"
    ];

    for (const field of required) {
        if (
            typeof event[field] !== "string" ||
            event[field].trim() === ""
        ) {
            throw new ValidationError(`Invalid ${field}`);
        }
    }

    if (!STAGE_INDEX.has(event.type)) {
        throw new ValidationError("Unknown funnel event type");
    }

    const timestamp = Date.parse(event.timestamp);

    if (!Number.isFinite(timestamp)) {
        throw new ValidationError("Invalid event timestamp");
    }

    if (event.revenue !== undefined) {
        if (
            typeof event.revenue !== "number" ||
            !Number.isFinite(event.revenue) ||
            event.revenue < 0
        ) {
            throw new ValidationError("Invalid revenue");
        }
    }

    const revenue = event.revenue ?? 0;

    if (event.type !== "purchase" && revenue !== 0) {
        throw new ValidationError(
            "Revenue is permitted only for purchase events"
        );
    }

    return Object.freeze({
        eventId: event.eventId,
        userId: event.userId,
        type: event.type,
        timestamp,
        channel: event.channel,
        campaign: event.campaign,
        experiment: event.experiment ?? "control",
        revenue
    });
}


// ---------------------------------------------------------
// 3. EVENT-DRIVEN INGESTION
// ---------------------------------------------------------

class ConversionEngine extends EventEmitter {
    #events = [];
    #eventIds = new Set();
    #users = new Map();

    constructor() {
        super();
        this.setMaxListeners(20);
    }

    ingest(rawEvent) {
        const event = validateEvent(rawEvent);

        if (this.#eventIds.has(event.eventId)) {
            return {
                accepted: false,
                reason: "duplicate"
            };
        }

        this.#eventIds.add(event.eventId);
        this.#events.push(event);

        if (!this.#users.has(event.userId)) {
            this.#users.set(event.userId, []);
        }

        this.#users.get(event.userId).push(event);

        this.emit("event", event);

        if (event.type === "purchase") {
            this.emit("conversion", event);
        }

        return {
            accepted: true,
            eventId: event.eventId
        };
    }

    async ingestBatch(events, concurrency = 1) {
        if (!Array.isArray(events)) {
            throw new ValidationError("Expected an event array");
        }

        if (
            !Number.isInteger(concurrency) ||
            concurrency < 1 ||
            concurrency > 100
        ) {
            throw new ValidationError("Invalid concurrency");
        }

        // Preserve deterministic ingestion order. Concurrency controls
        // the number of records validated within each batch.
        const results = [];

        for (let i = 0; i < events.length; i += concurrency) {
            const batch = events.slice(i, i + concurrency);

            const validated = await Promise.all(
                batch.map(async event => validateEvent(event))
            );

            for (const event of validated) {
                results.push(this.ingest(event));
            }
        }

        return results;
    }

    get events() {
        return [...this.#events];
    }

    get userCount() {
        return this.#users.size;
    }

    getUserEvents(userId) {
        return [...(this.#users.get(userId) ?? [])];
    }
}


// ---------------------------------------------------------
// 4. METRIC CALCULATIONS
// ---------------------------------------------------------

function calculateConversionRate(converted, eligible) {
    if (
        !Number.isInteger(converted) ||
        !Number.isInteger(eligible) ||
        converted < 0 ||
        eligible < 0 ||
        converted > eligible
    ) {
        throw new ValidationError("Invalid conversion counts");
    }

    return eligible === 0 ? 0 : converted / eligible * 100;
}

function calculateRevenuePerVisitor(revenue, visitors) {
    if (
        !Number.isFinite(revenue) ||
        revenue < 0 ||
        !Number.isInteger(visitors) ||
        visitors < 0
    ) {
        throw new ValidationError("Invalid revenue metrics");
    }

    return visitors === 0 ? 0 : revenue / visitors;
}


// ---------------------------------------------------------
// 5. USER JOURNEY RECONSTRUCTION
// ---------------------------------------------------------

function reconstructJourney(events) {
    const grouped = new Map();

    for (const event of events) {
        if (!grouped.has(event.userId)) {
            grouped.set(event.userId, []);
        }

        grouped.get(event.userId).push(event);
    }

    const journeys = new Map();

    for (const [userId, userEvents] of grouped) {
        userEvents.sort((a, b) => a.timestamp - b.timestamp);

        const completed = new Set();
        const firstTimestamp = new Map();

        for (const event of userEvents) {
            const index = STAGE_INDEX.get(event.type);

            if (!firstTimestamp.has(event.type)) {
                firstTimestamp.set(event.type, event.timestamp);
            }

            completed.add(index);
        }

        let reached = 0;
        let previousTime = -Infinity;

        for (let index = 0; index < STAGES.length; index++) {
            const stage = STAGES[index];
            const timestamp = firstTimestamp.get(stage);

            if (
                timestamp === undefined ||
                timestamp < previousTime
            ) {
                break;
            }

            previousTime = timestamp;
            reached++;
        }

        journeys.set(userId, {
            stages: completed,
            reached,
            events: userEvents
        });
    }

    return journeys;
}


// ---------------------------------------------------------
// 6. FUNNEL ANALYSIS
// ---------------------------------------------------------

function analyzeFunnel(events) {
    const journeys = reconstructJourney(events);

    const visitors = [...journeys.values()]
        .filter(journey => journey.stages.has(0));

    const total = visitors.length;

    let previous = total;

    const steps = STAGES.map((stage, index) => {
        const users = visitors.filter(
            journey => journey.reached > index
        ).length;

        const stepRate = previous === 0
            ? 0
            : users / previous * 100;

        const dropOff = previous === 0
            ? 0
            : 100 - stepRate;

        const result = {
            stage,
            users,
            previousUsers: previous,
            conversionRate: Number(stepRate.toFixed(2)),
            dropOffRate: Number(dropOff.toFixed(2))
        };

        previous = users;

        return result;
    });

    const converted = steps.at(-1)?.users ?? 0;

    return {
        visitors: total,
        conversions: converted,
        overallConversionRate: Number(
            calculateConversionRate(converted, total).toFixed(2)
        ),
        steps
    };
}


// ---------------------------------------------------------
// 7. ATTRIBUTION ANALYSIS
// ---------------------------------------------------------

function analyzeChannels(events) {
    const channels = new Map();

    for (const event of events) {
        if (!channels.has(event.channel)) {
            channels.set(event.channel, {
                visitors: new Set(),
                buyers: new Set(),
                revenue: 0
            });
        }

        const channel = channels.get(event.channel);

        if (event.type === "visit") {
            channel.visitors.add(event.userId);
        }

        if (event.type === "purchase") {
            channel.buyers.add(event.userId);
            channel.revenue += event.revenue;
        }
    }

    return Object.fromEntries(
        [...channels.entries()].map(([name, data]) => {
            const buyers = [...data.buyers].filter(
                id => data.visitors.has(id)
            );

            return [
                name,
                {
                    visitors: data.visitors.size,
                    conversions: buyers.length,
                    conversionRate: Number(
                        calculateConversionRate(
                            buyers.length,
                            data.visitors.size
                        ).toFixed(2)
                    ),
                    revenue: Number(data.revenue.toFixed(2)),
                    revenuePerVisitor: Number(
                        calculateRevenuePerVisitor(
                            data.revenue,
                            data.visitors.size
                        ).toFixed(2)
                    )
                }
            ];
        })
    );
}


// ---------------------------------------------------------
// 8. COHORT ANALYSIS
// ---------------------------------------------------------

function analyzeCohorts(events) {
    const firstVisits = new Map();
    const buyers = new Set();

    for (const event of events) {
        if (event.type === "visit") {
            const previous = firstVisits.get(event.userId);

            if (
                previous === undefined ||
                event.timestamp < previous
            ) {
                firstVisits.set(event.userId, event.timestamp);
            }
        }

        if (event.type === "purchase") {
            buyers.add(event.userId);
        }
    }

    const cohorts = new Map();

    for (const [userId, timestamp] of firstVisits) {
        const month = new Date(timestamp)
            .toISOString()
            .slice(0, 7);

        if (!cohorts.has(month)) {
            cohorts.set(month, new Set());
        }

        cohorts.get(month).add(userId);
    }

    return Object.fromEntries(
        [...cohorts.entries()]
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([month, users]) => {
                const conversions = [...users].filter(
                    id => buyers.has(id)
                ).length;

                return [
                    month,
                    {
                        visitors: users.size,
                        conversions,
                        conversionRate: Number(
                            calculateConversionRate(
                                conversions,
                                users.size
                            ).toFixed(2)
                        )
                    }
                ];
            })
    );
}


// ---------------------------------------------------------
// 9. A/B TESTING
// ---------------------------------------------------------

function normalCdf(x) {
    // Abramowitz-Stegun approximation for the normal CDF.
    const sign = x < 0 ? -1 : 1;
    const z = Math.abs(x) / Math.sqrt(2);
    const t = 1 / (1 + 0.3275911 * z);

    const erf = 1 - (
        (
            (
                (
                    1.061405429 * t -
                    1.453152027
                ) * t +
                1.421413741
            ) * t -
            0.284496736
        ) * t +
        0.254829592
    ) * t * Math.exp(-z * z);

    return 0.5 * (1 + sign * erf);
}

function evaluateExperiment(
    controlConversions,
    controlUsers,
    treatmentConversions,
    treatmentUsers
) {
    for (const [converted, users] of [
        [controlConversions, controlUsers],
        [treatmentConversions, treatmentUsers]
    ]) {
        if (
            !Number.isInteger(users) ||
            !Number.isInteger(converted) ||
            users <= 0 ||
            converted < 0 ||
            converted > users
        ) {
            throw new ValidationError("Invalid experiment sample");
        }
    }

    const p1 = controlConversions / controlUsers;
    const p2 = treatmentConversions / treatmentUsers;

    const pooled = (
        controlConversions + treatmentConversions
    ) / (controlUsers + treatmentUsers);

    const standardError = Math.sqrt(
        pooled * (1 - pooled) *
        (1 / controlUsers + 1 / treatmentUsers)
    );

    const z = standardError === 0
        ? 0
        : (p2 - p1) / standardError;

    const pValue = 2 * (1 - normalCdf(Math.abs(z)));

    return {
        controlRate: p1 * 100,
        treatmentRate: p2 * 100,
        absoluteLift: (p2 - p1) * 100,
        relativeLift: p1 === 0 ? null : (p2 - p1) / p1 * 100,
        zScore: z,
        pValue,
        significant: pValue < 0.05
    };
}


// ---------------------------------------------------------
// 10. OPTIMIZATION ENGINE
// ---------------------------------------------------------

class OptimizationEngine {
    static recommend(funnel) {
        if (!funnel.steps.length || funnel.visitors === 0) {
            return ["Insufficient visitor data for optimization."];
        }

        const bottleneck = funnel.steps.reduce(
            (worst, current) =>
                current.dropOffRate > worst.dropOffRate
                    ? current
                    : worst
        );

        const actions = [];

        if (bottleneck.dropOffRate >= 40) {
            actions.push({
                stage: bottleneck.stage,
                priority: "high",
                action: "Investigate friction at the highest-drop-off stage."
            });
        }

        if (funnel.overallConversionRate < 2) {
            actions.push({
                stage: "acquisition",
                priority: "high",
                action: "Compare acquisition intent with landing-page relevance."
            });
        }

        if (actions.length === 0) {
            actions.push({
                stage: "all",
                priority: "normal",
                action: "Run controlled experiments and monitor funnel stability."
            });
        }

        return actions;
    }
}


// ---------------------------------------------------------
// 11. REPORT EXPORT
// ---------------------------------------------------------

async function exportReport(report, filename) {
    const output = {
        generatedAt: new Date().toISOString(),
        ...report
    };

    // Exclusive creation prevents accidental replacement of existing reports.
    await fs.writeFile(
        filename,
        JSON.stringify(output, null, 2),
        {
            encoding: "utf8",
            flag: "wx",
            mode: 0o600
        }
    );
}


// ---------------------------------------------------------
// 12. SAMPLE EVENT DATA
// ---------------------------------------------------------

function sampleData() {
    const users = [
        ["u1", STAGES, "organic", "seo", 2500],
        ["u2", STAGES.slice(0, 4), "paid", "search_ads", 0],
        ["u3", STAGES.slice(0, 3).concat("purchase"), "organic", "seo", 1800],
        ["u4", STAGES.slice(0, 2), "social", "social_ads", 0],
        ["u5", STAGES, "paid", "search_ads", 3200],
        ["u6", STAGES.slice(0, 2), "social", "social_ads", 0],
        ["u7", STAGES, "organic", "seo", 1500],
        ["u8", STAGES.slice(0, 3), "paid", "search_ads", 0],
        ["u9", ["visit"], "referral", "partner", 0],
        ["u10", STAGES, "organic", "seo", 4100]
    ];

    const base = Date.UTC(2026, 10, 1, 10, 0, 0);
    const events = [];

    users.forEach((record, userIndex) => {
        const [userId, stages, channel, campaign, revenue] = record;

        stages.forEach((stage, index) => {
            events.push({
                eventId: `${userId}-${index}`,
                userId,
                type: stage,
                timestamp: new Date(
                    base + userIndex * 20 * 60000 + index * 5 * 60000
                ).toISOString(),
                channel,
                campaign,
                experiment: "control",
                revenue: stage === "purchase" ? revenue : 0
            });
        });
    });

    return events;
}


// ---------------------------------------------------------
// 13. EXECUTION
// ---------------------------------------------------------

async function main() {
    const engine = new ConversionEngine();

    let received = 0;
    let purchases = 0;

    engine.on("event", () => received++);
    engine.on("conversion", () => purchases++);

    const results = await engine.ingestBatch(sampleData(), 5);

    const accepted = results.filter(result => result.accepted).length;

    const funnel = analyzeFunnel(engine.events);

    const report = {
        ingestion: {
            accepted,
            received,
            purchaseEvents: purchases,
            users: engine.userCount
        },
        funnel,
        channels: analyzeChannels(engine.events),
        cohorts: analyzeCohorts(engine.events),
        experiment: evaluateExperiment(120, 2000, 150, 2000),
        recommendations: OptimizationEngine.recommend(funnel)
    };

    console.log(JSON.stringify(report, null, 2));

    // Core correctness checks.
    if (funnel.visitors !== 10) {
        throw new AnalyticsError("Unexpected visitor count");
    }

    if (funnel.conversions !== 4) {
        throw new AnalyticsError("Unexpected conversion count");
    }

    if (engine.ingest(sampleData()[0]).accepted) {
        throw new AnalyticsError("Deduplication failed");
    }

    try {
        validateEvent({
            eventId: "invalid",
            userId: "user",
            type: "unknown",
            timestamp: new Date().toISOString(),
            channel: "organic",
            campaign: "seo"
        });

        throw new AnalyticsError("Invalid event was accepted");
    } catch (error) {
        if (!(error instanceof ValidationError)) {
            throw error;
        }
    }

    console.log("\nAll validation checks passed.");
}

main().catch(error => {
    console.error("Analytics execution failed:", error.message);
    process.exitCode = 1;
});
