"use strict";

/*
 * Funnel Analysis
 *
 * This implementation uses an event-driven customer journey model.
 * The browser-independent Node.js program records funnel events,
 * validates stage progression, emits lifecycle events, evaluates
 * segment performance, and identifies the stage responsible for
 * the largest conversion loss.
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

const FUNNEL_STAGES = Object.freeze([
    "landing",
    "product",
    "cart",
    "checkout",
    "purchase"
]);

const STAGE_LABELS = Object.freeze({
    landing: "Visited Landing Page",
    product: "Viewed Product",
    cart: "Added to Cart",
    checkout: "Started Checkout",
    purchase: "Purchased"
});

const STAGE_INDEX = Object.freeze(
    Object.fromEntries(FUNNEL_STAGES.map((stage, index) => [stage, index]))
);

class FunnelValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "FunnelValidationError";
    }
}

class CustomerJourney {
    constructor({ customerId, segment, revenue = 0 }) {
        if (!customerId || typeof customerId !== "string") {
            throw new FunnelValidationError("customerId must be a non-empty string.");
        }

        if (!segment || typeof segment !== "string") {
            throw new FunnelValidationError("segment must be a non-empty string.");
        }

        if (!Number.isFinite(revenue) || revenue < 0) {
            throw new FunnelValidationError(
                "Revenue must be a finite non-negative number."
            );
        }

        this.customerId = customerId;
        this.segment = segment;
        this.revenue = revenue;
        this.events = new Map();
    }

    recordEvent(stage, timestamp = new Date()) {
        if (!(stage in STAGE_INDEX)) {
            throw new FunnelValidationError(`Unknown funnel stage: ${stage}`);
        }

        const date = timestamp instanceof Date
            ? timestamp
            : new Date(timestamp);

        if (Number.isNaN(date.getTime())) {
            throw new FunnelValidationError("Invalid event timestamp.");
        }

        const existingStages = [...this.events.keys()];

        if (existingStages.length > 0) {
            const lastStage = existingStages[existingStages.length - 1];

            if (STAGE_INDEX[stage] < STAGE_INDEX[lastStage]) {
                throw new FunnelValidationError(
                    `Stage ${stage} cannot occur after ${lastStage}.`
                );
            }

            if (STAGE_INDEX[stage] === STAGE_INDEX[lastStage]) {
                throw new FunnelValidationError(
                    `Stage ${stage} has already been recorded.`
                );
            }

            const lastTime = this.events.get(lastStage);

            if (date < lastTime) {
                throw new FunnelValidationError(
                    "A funnel event cannot occur before the previous event."
                );
            }
        }

        this.events.set(stage, date);
    }

    hasReached(stage) {
        return this.events.has(stage);
    }

    completed() {
        return this.hasReached("purchase");
    }

    conversionDurationMinutes() {
        if (!this.hasReached("landing") || !this.hasReached("purchase")) {
            return null;
        }

        const start = this.events.get("landing");
        const end = this.events.get("purchase");

        return (end.getTime() - start.getTime()) / 60000;
    }

    path() {
        return [...this.events.keys()]
            .map(stage => STAGE_LABELS[stage])
            .join(" → ");
    }
}

class FunnelAnalyzer extends EventEmitter {
    constructor(stages = FUNNEL_STAGES) {
        super();

        if (!Array.isArray(stages) || stages.length === 0) {
            throw new FunnelValidationError("At least one funnel stage is required.");
        }

        this.stages = [...stages];
        this.journeys = [];
    }

    addJourney(journey) {
        if (!(journey instanceof CustomerJourney)) {
            throw new FunnelValidationError(
                "Only CustomerJourney instances can be added."
            );
        }

        if (this.journeys.some(item => item.customerId === journey.customerId)) {
            throw new FunnelValidationError(
                `Duplicate customer ID: ${journey.customerId}`
            );
        }

        this.journeys.push(journey);

        this.emit("journeyAdded", {
            customerId: journey.customerId,
            path: journey.path()
        });
    }

    stageUsers(stage) {
        return this.journeys.filter(journey => journey.hasReached(stage));
    }

    stageMetrics() {
        const entryUsers = this.journeys.length;
        let previousCount = null;

        return this.stages.map((stage, index) => {
            const currentCount = this.stageUsers(stage).length;

            const conversionFromPrevious =
                index === 0 || previousCount === 0
                    ? null
                    : currentCount / previousCount;

            const dropOff =
                conversionFromPrevious === null
                    ? null
                    : 1 - conversionFromPrevious;

            const conversionFromEntry =
                entryUsers === 0 ? 0 : currentCount / entryUsers;

            previousCount = currentCount;

            return {
                stage,
                label: STAGE_LABELS[stage],
                users: currentCount,
                conversionFromPrevious,
                conversionFromEntry,
                dropOff
            };
        });
    }

    segmentMetrics() {
        const segments = new Map();

        for (const journey of this.journeys) {
            if (!segments.has(journey.segment)) {
                segments.set(journey.segment, []);
            }

            segments.get(journey.segment).push(journey);
        }

        return [...segments.entries()].map(([segment, journeys]) => {
            const converters = journeys.filter(journey => journey.completed());

            return {
                segment,
                users: journeys.length,
                converters: converters.length,
                conversionRate:
                    journeys.length === 0
                        ? 0
                        : converters.length / journeys.length,
                revenue: converters.reduce(
                    (total, journey) => total + journey.revenue,
                    0
                )
            };
        });
    }

    largestDropOff() {
        const metrics = this.stageMetrics()
            .filter(metric => metric.dropOff !== null);

        if (metrics.length === 0) {
            return null;
        }

        return metrics.reduce((largest, current) =>
            current.dropOff > largest.dropOff ? current : largest
        );
    }

    medianTimeToConversion() {
        const durations = this.journeys
            .map(journey => journey.conversionDurationMinutes())
            .filter(duration => duration !== null)
            .sort((a, b) => a - b);

        if (durations.length === 0) {
            return null;
        }

        const middle = Math.floor(durations.length / 2);

        return durations.length % 2 === 0
            ? (durations[middle - 1] + durations[middle]) / 2
            : durations[middle];
    }

    async writeReport(filePath) {
        const report = {
            generatedAt: new Date().toISOString(),
            totalUsers: this.journeys.length,
            overallConversion:
                this.journeys.length === 0
                    ? 0
                    : this.journeys.filter(journey => journey.completed()).length /
                      this.journeys.length,
            stages: this.stageMetrics(),
            segments: this.segmentMetrics(),
            largestDropOff: this.largestDropOff(),
            medianTimeToConversionMinutes: this.medianTimeToConversion(),
            customerPaths: this.journeys.reduce((result, journey) => {
                const path = journey.path();
                result[path] = (result[path] || 0) + 1;
                return result;
            }, {})
        };

        await fs.writeFile(
            filePath,
            JSON.stringify(report, null, 2),
            "utf8"
        );

        this.emit("reportWritten", { filePath });
    }
}

function buildDemoJourneys() {
    const base = new Date("2026-10-01T09:00:00Z");

    const at = minutes => new Date(base.getTime() + minutes * 60 * 1000);

    const journey = (config, events) => {
        const result = new CustomerJourney(config);

        for (const [stage, minute] of events) {
            result.recordEvent(stage, at(minute));
        }

        return result;
    };

    return [
        journey(
            { customerId: "C001", segment: "mobile", revenue: 129 },
            [
                ["landing", 0],
                ["product", 4],
                ["cart", 9],
                ["checkout", 15],
                ["purchase", 23]
            ]
        ),
        journey(
            { customerId: "C002", segment: "mobile" },
            [
                ["landing", 1],
                ["product", 6],
                ["cart", 12],
                ["checkout", 21]
            ]
        ),
        journey(
            { customerId: "C003", segment: "desktop", revenue: 249 },
            [
                ["landing", 2],
                ["product", 5],
                ["cart", 14],
                ["checkout", 20],
                ["purchase", 32]
            ]
        ),
        journey(
            { customerId: "C004", segment: "desktop" },
            [
                ["landing", 3],
                ["product", 8]
            ]
        ),
        journey(
            { customerId: "C005", segment: "mobile" },
            [
                ["landing", 10],
                ["product", 14],
                ["cart", 19]
            ]
        ),
        journey(
            { customerId: "C006", segment: "desktop", revenue: 89 },
            [
                ["landing", 11],
                ["product", 16],
                ["cart", 22],
                ["checkout", 30],
                ["purchase", 41]
            ]
        ),
        journey(
            { customerId: "C007", segment: "tablet" },
            [
                ["landing", 13],
                ["product", 18],
                ["cart", 26],
                ["checkout", 40]
            ]
        ),
        journey(
            { customerId: "C008", segment: "tablet" },
            [
                ["landing", 15],
                ["product", 21]
            ]
        ),
        journey(
            { customerId: "C009", segment: "mobile", revenue: 159 },
            [
                ["landing", 18],
                ["product", 23],
                ["cart", 31],
                ["checkout", 37],
                ["purchase", 48]
            ]
        ),
        journey(
            { customerId: "C010", segment: "desktop" },
            [
                ["landing", 20],
                ["product", 24],
                ["cart", 30]
            ]
        )
    ];
}

function printReport(analyzer) {
    console.log("\nFUNNEL ANALYSIS");
    console.log("=".repeat(78));

    for (const metric of analyzer.stageMetrics()) {
        const previous =
            metric.conversionFromPrevious === null
                ? "n/a"
                : `${(metric.conversionFromPrevious * 100).toFixed(1)}%`;

        const dropOff =
            metric.dropOff === null
                ? "n/a"
                : `${(metric.dropOff * 100).toFixed(1)}%`;

        console.log(
            `${metric.label.padEnd(24)} ` +
            `users=${String(metric.users).padEnd(3)} ` +
            `previous=${previous.padEnd(7)} ` +
            `entry=${(metric.conversionFromEntry * 100).toFixed(1)}% ` +
            `dropOff=${dropOff}`
        );
    }

    const largest = analyzer.largestDropOff();

    if (largest) {
        console.log(
            `\nLargest drop-off: ${largest.label} ` +
            `(${(largest.dropOff * 100).toFixed(1)}%)`
        );
    }

    console.log("\nSEGMENT PERFORMANCE");
    console.log("-".repeat(78));

    for (const segment of analyzer.segmentMetrics()) {
        console.log(
            `${segment.segment.padEnd(10)} ` +
            `users=${String(segment.users).padEnd(3)} ` +
            `converters=${String(segment.converters).padEnd(3)} ` +
            `conversion=${(segment.conversionRate * 100).toFixed(1)}% ` +
            `revenue=$${segment.revenue.toFixed(2)}`
        );
    }

    console.log(
        `\nMedian time to conversion: ` +
        `${analyzer.medianTimeToConversion()?.toFixed(1) ?? "n/a"} minutes`
    );
}

async function main() {
    const analyzer = new FunnelAnalyzer();

    analyzer.on("journeyAdded", event => {
        console.log(
            `Recorded ${event.customerId}: ${event.path}`
        );
    });

    analyzer.on("reportWritten", event => {
        console.log(`Report written to ${event.filePath}`);
    });

    for (const journey of buildDemoJourneys()) {
        analyzer.addJourney(journey);
    }

    printReport(analyzer);

    await analyzer.writeReport("./funnel-report.json");

    console.log("\nEVENT VALIDATION");
    console.log("=".repeat(78));

    try {
        const invalid = new CustomerJourney({
            customerId: "INVALID",
            segment: "mobile"
        });

        invalid.recordEvent("product", new Date("2026-10-01T10:00:00Z"));
        invalid.recordEvent("landing", new Date("2026-10-01T10:05:00Z"));
    } catch (error) {
        if (error instanceof FunnelValidationError) {
            console.log(`Rejected invalid journey: ${error.message}`);
        } else {
            throw error;
        }
    }
}

main().catch(error => {
    console.error("Funnel analysis failed:", error.message);
    process.exitCode = 1;
});
