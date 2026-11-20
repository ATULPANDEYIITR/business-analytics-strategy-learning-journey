"use strict";

/*
 * MARKETING ANALYTICS
 * Event-driven campaign measurement and performance monitoring.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

class ValidationError extends Error {}
class CampaignNotFoundError extends Error {}
class ProcessingError extends Error {}

const AttributionModel = Object.freeze({
    FIRST_TOUCH: "first_touch",
    LAST_TOUCH: "last_touch",
    LINEAR: "linear"
});

function requireNonNegative(value, field) {
    if (!Number.isFinite(value) || value < 0) {
        throw new ValidationError(`${field} must be non-negative.`);
    }
}

function divide(numerator, denominator) {
    return denominator === 0 ? 0 : numerator / denominator;
}

function round(value, decimals = 2) {
    return Number(value.toFixed(decimals));
}

class Campaign {
    constructor({
        id,
        name,
        channel,
        budget,
        objective,
        startDate,
        endDate
    }) {
        if (!id || !name || !channel || !objective) {
            throw new ValidationError("Missing campaign information.");
        }

        requireNonNegative(budget, "Budget");

        if (
            !Number.isFinite(Date.parse(startDate)) ||
            !Number.isFinite(Date.parse(endDate)) ||
            Date.parse(endDate) < Date.parse(startDate)
        ) {
            throw new ValidationError("Invalid campaign dates.");
        }

        Object.assign(this, {
            id,
            name,
            channel,
            budget,
            objective,
            startDate,
            endDate
        });
    }
}

class MarketingEvent {
    constructor({
        eventId,
        customerId,
        campaignId,
        type,
        timestamp,
        revenue = 0
    }) {
        if (!eventId || !customerId || !campaignId || !type) {
            throw new ValidationError("Incomplete event.");
        }

        if (!Number.isFinite(Date.parse(timestamp))) {
            throw new ValidationError("Invalid event timestamp.");
        }

        requireNonNegative(revenue, "Revenue");

        this.eventId = eventId;
        this.customerId = customerId;
        this.campaignId = campaignId;
        this.type = type;
        this.timestamp = new Date(timestamp).toISOString();
        this.revenue = revenue;

        Object.freeze(this);
    }
}

class MarketingEngine extends EventEmitter {
    constructor() {
        super();

        this.campaigns = new Map();
        this.metrics = new Map();
        this.customers = new Map();
        this.events = new Map();

        this.processing = false;
    }

    registerCampaign(campaign) {
        if (!(campaign instanceof Campaign)) {
            throw new ValidationError("Invalid campaign object.");
        }

        if (this.campaigns.has(campaign.id)) {
            throw new ValidationError("Duplicate campaign.");
        }

        this.campaigns.set(campaign.id, campaign);

        this.metrics.set(campaign.id, {
            impressions: 0,
            clicks: 0,
            conversions: 0,
            spend: 0,
            revenue: 0
        });

        this.emit("campaign:registered", campaign);
    }

    registerCustomer(customer) {
        const { id, acquisitionCost, lifetimeRevenue } = customer;

        if (!id || this.customers.has(id)) {
            throw new ValidationError("Invalid or duplicate customer.");
        }

        requireNonNegative(acquisitionCost, "Acquisition cost");
        requireNonNegative(lifetimeRevenue, "Lifetime revenue");

        this.customers.set(id, Object.freeze({
            id,
            acquisitionCost,
            lifetimeRevenue
        }));
    }

    async processEvent(event) {
        if (!(event instanceof MarketingEvent)) {
            throw new ValidationError("Invalid marketing event.");
        }

        if (this.events.has(event.eventId)) {
            // Event IDs provide idempotency for retried deliveries.
            return { accepted: false, reason: "duplicate" };
        }

        const metrics = this.metrics.get(event.campaignId);

        if (!metrics) {
            throw new CampaignNotFoundError("Campaign does not exist.");
        }

        if (!this.customers.has(event.customerId)) {
            throw new ValidationError("Unknown customer.");
        }

        const next = { ...metrics };

        switch (event.type) {
            case "impression":
                next.impressions++;
                break;

            case "click":
                if (next.clicks >= next.impressions) {
                    throw new ValidationError(
                        "Click cannot exceed recorded impressions."
                    );
                }
                next.clicks++;
                break;

            case "conversion":
                if (next.conversions >= next.clicks) {
                    throw new ValidationError(
                        "Conversion requires a recorded click."
                    );
                }
                next.conversions++;
                next.revenue += event.revenue;
                break;

            default:
                throw new ValidationError("Unsupported event type.");
        }

        this.metrics.set(event.campaignId, next);
        this.events.set(event.eventId, event);

        this.emit("event:processed", {
            event,
            metrics: { ...next }
        });

        return { accepted: true };
    }

    recordSpend(campaignId, amount) {
        requireNonNegative(amount, "Spend");

        const campaign = this.campaigns.get(campaignId);
        const metrics = this.metrics.get(campaignId);

        if (!campaign || !metrics) {
            throw new CampaignNotFoundError("Campaign does not exist.");
        }

        if (metrics.spend + amount > campaign.budget) {
            throw new ValidationError("Budget limit exceeded.");
        }

        metrics.spend += amount;

        this.emit("spend:recorded", {
            campaignId,
            amount,
            totalSpend: metrics.spend
        });
    }

    calculateMetrics(campaignId) {
        const metrics = this.metrics.get(campaignId);

        if (!metrics) {
            throw new CampaignNotFoundError("Campaign not found.");
        }

        const {
            impressions,
            clicks,
            conversions,
            spend,
            revenue
        } = metrics;

        return Object.freeze({
            campaignId,
            impressions,
            clicks,
            conversions,
            spend,
            revenue,
            ctr: round(divide(clicks, impressions) * 100),
            conversionRate: round(
                divide(conversions, clicks) * 100
            ),
            cpc: round(divide(spend, clicks)),
            cpa: round(divide(spend, conversions)),
            roas: round(divide(revenue, spend)),
            roi: round(
                divide(revenue - spend, spend) * 100
            )
        });
    }

    calculateFunnel() {
        const totals = {
            impressions: 0,
            clicks: 0,
            conversions: 0
        };

        for (const metrics of this.metrics.values()) {
            totals.impressions += metrics.impressions;
            totals.clicks += metrics.clicks;
            totals.conversions += metrics.conversions;
        }

        return {
            ...totals,
            clickThroughRate: round(
                divide(totals.clicks, totals.impressions) * 100
            ),
            clickConversionRate: round(
                divide(totals.conversions, totals.clicks) * 100
            )
        };
    }

    attributeCustomer(customerId, model) {
        const customer = this.customers.get(customerId);

        if (!customer) {
            throw new ValidationError("Customer not found.");
        }

        if (!Object.values(AttributionModel).includes(model)) {
            throw new ValidationError("Unknown attribution model.");
        }

        const events = [...this.events.values()]
            .filter(event =>
                event.customerId === customerId &&
                event.type === "conversion" ||
                event.customerId === customerId &&
                event.type === "click"
            )
            .sort((a, b) =>
                Date.parse(a.timestamp) - Date.parse(b.timestamp)
            );

        if (events.length === 0) {
            return {};
        }

        const allocations = new Map();

        if (model === AttributionModel.FIRST_TOUCH) {
            allocations.set(
                events[0].campaignId,
                customer.lifetimeRevenue
            );
        } else if (model === AttributionModel.LAST_TOUCH) {
            allocations.set(
                events[events.length - 1].campaignId,
                customer.lifetimeRevenue
            );
        } else {
            const share = customer.lifetimeRevenue / events.length;

            for (const event of events) {
                allocations.set(
                    event.campaignId,
                    (allocations.get(event.campaignId) || 0) + share
                );
            }
        }

        return Object.fromEntries(allocations);
    }

    getChannelReport() {
        const channels = new Map();

        for (const [campaignId, metrics] of this.metrics) {
            const campaign = this.campaigns.get(campaignId);

            if (!channels.has(campaign.channel)) {
                channels.set(campaign.channel, {
                    spend: 0,
                    revenue: 0,
                    clicks: 0,
                    conversions: 0
                });
            }

            const row = channels.get(campaign.channel);

            row.spend += metrics.spend;
            row.revenue += metrics.revenue;
            row.clicks += metrics.clicks;
            row.conversions += metrics.conversions;
        }

        return Object.fromEntries(
            [...channels.entries()].map(([channel, values]) => [
                channel,
                {
                    ...values,
                    roas: round(divide(values.revenue, values.spend)),
                    cpa: round(
                        divide(values.spend, values.conversions)
                    )
                }
            ])
        );
    }

    getCustomerAcquisitionReport() {
        const customers = [...this.customers.values()];

        if (!customers.length) {
            return { customers: 0, cac: 0, averageLtv: 0 };
        }

        const acquisitionCost = customers.reduce(
            (sum, customer) => sum + customer.acquisitionCost,
            0
        );

        const lifetimeRevenue = customers.reduce(
            (sum, customer) => sum + customer.lifetimeRevenue,
            0
        );

        const cac = acquisitionCost / customers.length;
        const averageLtv = lifetimeRevenue / customers.length;

        return {
            customers: customers.length,
            cac: round(cac),
            averageLtv: round(averageLtv),
            ltvToCac: round(divide(averageLtv, cac))
        };
    }

    getDashboard() {
        return {
            generatedAt: new Date().toISOString(),
            funnel: this.calculateFunnel(),
            channels: this.getChannelReport(),
            customerAcquisition: this.getCustomerAcquisitionReport(),
            campaigns: [...this.metrics.keys()].map(
                id => this.calculateMetrics(id)
            )
        };
    }

    async exportDashboard(filename) {
        const destination = path.resolve(filename);
        const directory = path.dirname(destination);

        await fs.mkdir(directory, { recursive: true });

        const temporary = `${destination}.${crypto.randomUUID()}.tmp`;

        try {
            await fs.writeFile(
                temporary,
                JSON.stringify(this.getDashboard(), null, 2),
                { encoding: "utf8", flag: "wx" }
            );

            await fs.rename(temporary, destination);
        } catch (error) {
            await fs.rm(temporary, { force: true });
            throw new ProcessingError(
                `Dashboard export failed: ${error.message}`
            );
        }
    }
}

async function main() {
    const engine = new MarketingEngine();

    engine.on("campaign:registered", campaign => {
        console.log(`Registered: ${campaign.name}`);
    });

    engine.on("event:processed", ({ event }) => {
        console.log(`Processed event: ${event.eventId}`);
    });

    engine.on("spend:recorded", event => {
        console.log(
            `Spend recorded: ${event.campaignId} = ${event.totalSpend}`
        );
    });

    const campaigns = [
        new Campaign({
            id: "C001",
            name: "Search Acquisition",
            channel: "Search",
            budget: 50000,
            objective: "Acquisition",
            startDate: "2026-01-01",
            endDate: "2026-12-31"
        }),
        new Campaign({
            id: "C002",
            name: "Social Awareness",
            channel: "Social",
            budget: 40000,
            objective: "Awareness",
            startDate: "2026-01-01",
            endDate: "2026-12-31"
        })
    ];

    campaigns.forEach(campaign => engine.registerCampaign(campaign));

    engine.registerCustomer({
        id: "U001",
        acquisitionCost: 500,
        lifetimeRevenue: 3000
    });

    const events = [
        new MarketingEvent({
            eventId: "E001",
            customerId: "U001",
            campaignId: "C002",
            type: "impression",
            timestamp: "2026-02-01T10:00:00Z"
        }),
        new MarketingEvent({
            eventId: "E002",
            customerId: "U001",
            campaignId: "C002",
            type: "click",
            timestamp: "2026-02-01T10:05:00Z"
        }),
        new MarketingEvent({
            eventId: "E003",
            customerId: "U001",
            campaignId: "C001",
            type: "impression",
            timestamp: "2026-02-02T10:00:00Z"
        }),
        new MarketingEvent({
            eventId: "E004",
            customerId: "U001",
            campaignId: "C001",
            type: "click",
            timestamp: "2026-02-02T10:05:00Z"
        }),
        new MarketingEvent({
            eventId: "E005",
            customerId: "U001",
            campaignId: "C001",
            type: "conversion",
            timestamp: "2026-02-02T11:00:00Z",
            revenue: 3000
        })
    ];

    for (const event of events) {
        await engine.processEvent(event);
    }

    // Duplicate delivery is safely ignored.
    const duplicate = await engine.processEvent(events[0]);
    console.log("Duplicate event:", duplicate);

    engine.recordSpend("C001", 1000);
    engine.recordSpend("C002", 500);

    console.log("\nCAMPAIGN REPORT");
    console.log(engine.calculateMetrics("C001"));

    console.log("\nCONVERSION FUNNEL");
    console.log(engine.calculateFunnel());

    console.log("\nCHANNEL REPORT");
    console.log(engine.getChannelReport());

    console.log("\nCUSTOMER ACQUISITION");
    console.log(engine.getCustomerAcquisitionReport());

    console.log("\nFIRST-TOUCH ATTRIBUTION");
    console.log(
        engine.attributeCustomer(
            "U001",
            AttributionModel.FIRST_TOUCH
        )
    );

    console.log("\nDASHBOARD");
    console.log(JSON.stringify(engine.getDashboard(), null, 2));

    await engine.exportDashboard("output/marketing-dashboard.json");

    console.log("\nDashboard exported.");
}

main().catch(error => {
    console.error("Marketing analytics failed:", error.message);
    process.exitCode = 1;
});
