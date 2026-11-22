"use strict";

/*
 * Customer Acquisition Channel and CAC Analysis
 *
 * Event-driven campaign tracking, attribution, conversion analysis,
 * unit economics, budget evaluation, and acquisition policy decisions.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 */

const { EventEmitter } = require("node:events");
const { randomUUID } = require("node:crypto");
const fs = require("node:fs/promises");

class AcquisitionError extends Error {
    constructor(message, code = "ACQUISITION_ERROR") {
        super(message);
        this.name = "AcquisitionError";
        this.code = code;
    }
}

const Channel = Object.freeze({
    PAID_SEARCH: "paid_search",
    PAID_SOCIAL: "paid_social",
    ORGANIC_SEARCH: "organic_search",
    EMAIL: "email",
    REFERRAL: "referral",
    AFFILIATE: "affiliate",
    CONTENT: "content",
    EVENTS: "events",
    DIRECT: "direct"
});

const CampaignState = Object.freeze({
    DRAFT: "draft",
    ACTIVE: "active",
    PAUSED: "paused",
    COMPLETED: "completed"
});

const ReviewDecision = Object.freeze({
    SCALE: "scale",
    OPTIMIZE: "optimize",
    REDUCE: "reduce",
    INSUFFICIENT_DATA: "insufficient_data"
});

function money(value, field = "amount") {
    const amount = Number(value);

    if (!Number.isFinite(amount) || amount < 0) {
        throw new AcquisitionError(
            `${field} must be a finite non-negative number.`,
            "INVALID_MONEY"
        );
    }

    return amount;
}

function positiveInteger(value, field) {
    if (!Number.isSafeInteger(value) || value < 0) {
        throw new AcquisitionError(
            `${field} must be a non-negative safe integer.`,
            "INVALID_COUNT"
        );
    }

    return value;
}

function validateDateRange(startDate, endDate) {
    const start = Date.parse(startDate);
    const end = Date.parse(endDate);

    if (
        !Number.isFinite(start) ||
        !Number.isFinite(end) ||
        end < start
    ) {
        throw new AcquisitionError("Invalid campaign date range.");
    }
}

class Campaign {
    constructor({
        id = randomUUID(),
        name,
        channel,
        startDate,
        endDate,
        budget,
        spend = 0,
        impressions = 0,
        clicks = 0,
        leads = 0,
        customers = 0,
        revenue = 0
    }) {
        if (typeof name !== "string" || !name.trim()) {
            throw new AcquisitionError("Campaign name is required.");
        }

        if (!Object.values(Channel).includes(channel)) {
            throw new AcquisitionError("Unsupported acquisition channel.");
        }

        validateDateRange(startDate, endDate);

        this.id = id;
        this.name = name.trim();
        this.channel = channel;
        this.startDate = startDate;
        this.endDate = endDate;
        this.budget = money(budget, "budget");
        this.spend = money(spend, "spend");
        this.impressions = positiveInteger(impressions, "impressions");
        this.clicks = positiveInteger(clicks, "clicks");
        this.leads = positiveInteger(leads, "leads");
        this.customers = positiveInteger(customers, "customers");
        this.revenue = money(revenue, "revenue");
        this.state = CampaignState.DRAFT;

        this.validateMetrics();
    }

    validateMetrics() {
        if (this.spend > this.budget) {
            throw new AcquisitionError("Campaign budget exceeded.");
        }

        if (this.clicks > this.impressions) {
            throw new AcquisitionError("Clicks exceed impressions.");
        }

        if (this.leads > this.clicks) {
            throw new AcquisitionError("Leads exceed clicks.");
        }

        if (this.customers > this.leads) {
            throw new AcquisitionError("Customers exceed leads.");
        }
    }

    transition(nextState) {
        const allowed = {
            draft: ["active"],
            active: ["paused", "completed"],
            paused: ["active", "completed"],
            completed: []
        };

        if (!allowed[this.state]?.includes(nextState)) {
            throw new AcquisitionError(
                `Invalid campaign transition: ${this.state} -> ${nextState}`
            );
        }

        this.state = nextState;
    }

    get ctr() {
        return this.impressions === 0
            ? 0
            : this.clicks / this.impressions;
    }

    get leadRate() {
        return this.clicks === 0 ? 0 : this.leads / this.clicks;
    }

    get conversionRate() {
        return this.leads === 0 ? 0 : this.customers / this.leads;
    }

    get cac() {
        return this.customers === 0
            ? null
            : this.spend / this.customers;
    }

    get cpc() {
        return this.clicks === 0 ? null : this.spend / this.clicks;
    }

    get cpl() {
        return this.leads === 0 ? null : this.spend / this.leads;
    }

    get roas() {
        return this.spend === 0 ? null : this.revenue / this.spend;
    }

    recordSpend(amount) {
        const additionalSpend = money(amount, "additional spend");

        if (this.state !== CampaignState.ACTIVE) {
            throw new AcquisitionError("Only active campaigns can incur spend.");
        }

        if (this.spend + additionalSpend > this.budget) {
            throw new AcquisitionError("Spend would exceed the campaign budget.");
        }

        this.spend += additionalSpend;
    }

    recordFunnelActivity({ impressions = 0, clicks = 0, leads = 0, customers = 0 }) {
        if (this.state !== CampaignState.ACTIVE) {
            throw new AcquisitionError("Campaign is not active.");
        }

        const next = {
            impressions: this.impressions + positiveInteger(impressions, "impressions"),
            clicks: this.clicks + positiveInteger(clicks, "clicks"),
            leads: this.leads + positiveInteger(leads, "leads"),
            customers: this.customers + positiveInteger(customers, "customers")
        };

        if (next.clicks > next.impressions) {
            throw new AcquisitionError("Cumulative clicks exceed impressions.");
        }

        if (next.leads > next.clicks) {
            throw new AcquisitionError("Cumulative leads exceed clicks.");
        }

        if (next.customers > next.leads) {
            throw new AcquisitionError("Cumulative customers exceed leads.");
        }

        Object.assign(this, next);
    }
}

class Customer {
    constructor({
        id = randomUUID(),
        campaignId,
        channel,
        acquiredAt,
        firstPurchase,
        monthlyRevenue,
        grossMargin,
        retention
    }) {
        if (!campaignId || !Object.values(Channel).includes(channel)) {
            throw new AcquisitionError("Invalid customer acquisition reference.");
        }

        const timestamp = Date.parse(acquiredAt);

        if (!Number.isFinite(timestamp)) {
            throw new AcquisitionError("Invalid acquisition timestamp.");
        }

        this.id = id;
        this.campaignId = campaignId;
        this.channel = channel;
        this.acquiredAt = acquiredAt;
        this.firstPurchase = money(firstPurchase, "first purchase");
        this.monthlyRevenue = money(monthlyRevenue, "monthly revenue");

        if (
            !Number.isFinite(grossMargin) ||
            grossMargin < 0 ||
            grossMargin > 1
        ) {
            throw new AcquisitionError("Gross margin must be between 0 and 1.");
        }

        if (
            !Number.isFinite(retention) ||
            retention < 0 ||
            retention > 1
        ) {
            throw new AcquisitionError("Retention must be between 0 and 1.");
        }

        this.grossMargin = grossMargin;
        this.retention = retention;
    }

    lifetimeValue(months = 24) {
        if (!Number.isInteger(months) || months < 1) {
            throw new AcquisitionError("Invalid LTV projection period.");
        }

        const initialProfit = this.firstPurchase * this.grossMargin;
        const monthlyProfit = this.monthlyRevenue * this.grossMargin;

        let recurringProfit = 0;
        let retainedCustomers = 1;

        for (let month = 1; month <= months; month++) {
            retainedCustomers *= this.retention;
            recurringProfit += retainedCustomers * monthlyProfit;
        }

        return initialProfit + recurringProfit;
    }
}

class AttributionEngine {
    /*
     * Weighted attribution distributes conversion credit across touchpoints.
     * It does not independently establish causal marketing incrementality.
     */
    static attribute(touchpoints, model = "linear") {
        if (!Array.isArray(touchpoints) || touchpoints.length === 0) {
            throw new AcquisitionError("At least one touchpoint is required.");
        }

        const validModels = ["linear", "first_touch", "last_touch"];

        if (!validModels.includes(model)) {
            throw new AcquisitionError("Unsupported attribution model.");
        }

        for (const touchpoint of touchpoints) {
            if (!Object.values(Channel).includes(touchpoint.channel)) {
                throw new AcquisitionError("Invalid touchpoint channel.");
            }

            if (!Number.isFinite(Date.parse(touchpoint.timestamp))) {
                throw new AcquisitionError("Invalid touchpoint timestamp.");
            }
        }

        const ordered = [...touchpoints].sort(
            (a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp)
        );

        if (model === "first_touch") {
            return new Map([[ordered[0].channel, 1]]);
        }

        if (model === "last_touch") {
            return new Map([[
                ordered[ordered.length - 1].channel,
                1
            ]]);
        }

        const credits = new Map();

        for (const item of ordered) {
            credits.set(
                item.channel,
                (credits.get(item.channel) || 0) + 1 / ordered.length
            );
        }

        return credits;
    }
}

class AcquisitionAnalytics {
    static calculateChannelMetrics(campaigns, customers, months = 24) {
        const result = new Map();

        for (const channel of Object.values(Channel)) {
            result.set(channel, {
                channel,
                spend: 0,
                customerCount: 0,
                revenue: 0,
                projectedGrossProfit: 0
            });
        }

        for (const campaign of campaigns.values()) {
            result.get(campaign.channel).spend += campaign.spend;
        }

        for (const customer of customers.values()) {
            const item = result.get(customer.channel);
            item.customerCount++;
            item.projectedGrossProfit += customer.lifetimeValue(months);
            item.revenue += customer.firstPurchase;
        }

        return [...result.values()].map(item => {
            const cac = item.customerCount
                ? item.spend / item.customerCount
                : null;

            const ltv = item.customerCount
                ? item.projectedGrossProfit / item.customerCount
                : null;

            return {
                ...item,
                cac,
                ltv,
                ltvCacRatio: cac > 0 ? ltv / cac : null,
                roas: item.spend > 0 ? item.revenue / item.spend : null
            };
        });
    }

    static blendedCAC(campaigns, customers) {
        const totalSpend = [...campaigns.values()].reduce(
            (sum, campaign) => sum + campaign.spend,
            0
        );

        return customers.size === 0
            ? null
            : totalSpend / customers.size;
    }
}

class AcquisitionPolicy {
    constructor({
        minimumCustomers = 10,
        minimumLtvCac = 3,
        maximumCac = 1000
    } = {}) {
        this.minimumCustomers = positiveInteger(
            minimumCustomers,
            "minimum customers"
        );

        this.minimumLtvCac = money(minimumLtvCac);
        this.maximumCac = money(maximumCac);
    }

    evaluate(metrics) {
        if (metrics.customerCount < this.minimumCustomers) {
            return ReviewDecision.INSUFFICIENT_DATA;
        }

        if (metrics.cac === null || metrics.ltvCacRatio === null) {
            return ReviewDecision.INSUFFICIENT_DATA;
        }

        if (
            metrics.ltvCacRatio >= this.minimumLtvCac &&
            metrics.cac <= this.maximumCac
        ) {
            return ReviewDecision.SCALE;
        }

        if (metrics.ltvCacRatio >= 1) {
            return ReviewDecision.OPTIMIZE;
        }

        return ReviewDecision.REDUCE;
    }
}

class BudgetAllocator {
    static allocate(totalBudget, channelForecasts, minimumAllocation = 0) {
        money(totalBudget, "total budget");
        money(minimumAllocation, "minimum allocation");

        if (!Array.isArray(channelForecasts) || channelForecasts.length === 0) {
            throw new AcquisitionError("Forecasts cannot be empty.");
        }

        const channels = new Set();
        let totalEfficiency = 0;

        for (const forecast of channelForecasts) {
            if (!Object.values(Channel).includes(forecast.channel)) {
                throw new AcquisitionError("Invalid forecast channel.");
            }

            if (channels.has(forecast.channel)) {
                throw new AcquisitionError("Duplicate forecast channel.");
            }

            channels.add(forecast.channel);

            if (
                !Number.isFinite(forecast.expectedCac) ||
                forecast.expectedCac <= 0
            ) {
                throw new AcquisitionError("Expected CAC must be positive.");
            }

            totalEfficiency += 1 / forecast.expectedCac;
        }

        if (minimumAllocation * channels.size > totalBudget) {
            throw new AcquisitionError("Minimum allocation exceeds total budget.");
        }

        const remaining = totalBudget - minimumAllocation * channels.size;
        const allocation = new Map();

        for (const forecast of channelForecasts) {
            allocation.set(
                forecast.channel,
                minimumAllocation +
                remaining * (1 / forecast.expectedCac) / totalEfficiency
            );
        }

        return allocation;
    }
}

class AcquisitionPlatform extends EventEmitter {
    constructor(policy = new AcquisitionPolicy()) {
        super();

        this.campaigns = new Map();
        this.customers = new Map();
        this.policy = policy;
        this.events = [];
    }

    recordEvent(type, payload) {
        const event = Object.freeze({
            id: randomUUID(),
            type,
            occurredAt: new Date().toISOString(),
            payload
        });

        this.events.push(event);
        this.emit(type, event);
        return event;
    }

    addCampaign(campaign) {
        if (!(campaign instanceof Campaign)) {
            throw new AcquisitionError("Expected a Campaign instance.");
        }

        if (this.campaigns.has(campaign.id)) {
            throw new AcquisitionError("Duplicate campaign ID.");
        }

        this.campaigns.set(campaign.id, campaign);
        this.recordEvent("campaign.created", {
            campaignId: campaign.id,
            channel: campaign.channel
        });
    }

    activateCampaign(campaignId) {
        const campaign = this.requireCampaign(campaignId);
        campaign.transition(CampaignState.ACTIVE);

        this.recordEvent("campaign.activated", { campaignId });
    }

    requireCampaign(campaignId) {
        const campaign = this.campaigns.get(campaignId);

        if (!campaign) {
            throw new AcquisitionError("Campaign not found.");
        }

        return campaign;
    }

    async acquireCustomer(customer) {
        if (!(customer instanceof Customer)) {
            throw new AcquisitionError("Expected a Customer instance.");
        }

        const campaign = this.requireCampaign(customer.campaignId);

        if (campaign.channel !== customer.channel) {
            throw new AcquisitionError("Customer channel mismatch.");
        }

        if (campaign.state !== CampaignState.ACTIVE) {
            throw new AcquisitionError("Campaign is not active.");
        }

        if (this.customers.has(customer.id)) {
            throw new AcquisitionError("Duplicate customer ID.");
        }

        if (Date.parse(customer.acquiredAt) < Date.parse(campaign.startDate) ||
            Date.parse(customer.acquiredAt) > Date.parse(campaign.endDate)) {
            throw new AcquisitionError("Acquisition timestamp outside campaign.");
        }

        this.customers.set(customer.id, customer);

        try {
            this.recordEvent("customer.acquired", {
                customerId: customer.id,
                campaignId: customer.campaignId,
                channel: customer.channel
            });
        } catch (error) {
            this.customers.delete(customer.id);
            throw error;
        }

        return customer;
    }

    async generateReport(months = 24) {
        // Yield to the event loop for integration with asynchronous data sources.
        await Promise.resolve();

        const metrics = AcquisitionAnalytics.calculateChannelMetrics(
            this.campaigns,
            this.customers,
            months
        );

        return metrics.map(item => ({
            ...item,
            decision: this.policy.evaluate(item)
        }));
    }

    async exportReport(filename, months = 24) {
        const report = await this.generateReport(months);

        await fs.writeFile(
            filename,
            JSON.stringify({
                generatedAt: new Date().toISOString(),
                projectionMonths: months,
                channels: report
            }, null, 2),
            { encoding: "utf8", mode: 0o600 }
        );

        return report;
    }
}

async function demonstration() {
    const platform = new AcquisitionPlatform(
        new AcquisitionPolicy({
            minimumCustomers: 2,
            minimumLtvCac: 3,
            maximumCac: 500
        })
    );

    platform.on("customer.acquired", event => {
        console.log(
            `Event: customer ${event.payload.customerId} acquired through ${event.payload.channel}`
        );
    });

    const campaignDefinitions = [
        {
            id: "SEARCH-01",
            name: "Search Campaign",
            channel: Channel.PAID_SEARCH,
            budget: 50000,
            spend: 42000,
            startDate: "2026-01-01",
            endDate: "2026-12-31"
        },
        {
            id: "SOCIAL-01",
            name: "Social Campaign",
            channel: Channel.PAID_SOCIAL,
            budget: 40000,
            spend: 36000,
            startDate: "2026-01-01",
            endDate: "2026-12-31"
        },
        {
            id: "ORGANIC-01",
            name: "Organic Campaign",
            channel: Channel.ORGANIC_SEARCH,
            budget: 20000,
            spend: 15000,
            startDate: "2026-01-01",
            endDate: "2026-12-31"
        }
    ];

    for (const definition of campaignDefinitions) {
        const campaign = new Campaign({
            ...definition,
            impressions: 100000,
            clicks: 5000,
            leads: 1000,
            customers: 200,
            revenue: 30000
        });

        platform.addCampaign(campaign);
        platform.activateCampaign(campaign.id);
    }

    const customers = [
        ["U001", "SEARCH-01", Channel.PAID_SEARCH, 150, 0.75],
        ["U002", "SEARCH-01", Channel.PAID_SEARCH, 180, 0.75],
        ["U003", "SOCIAL-01", Channel.PAID_SOCIAL, 100, 0.65],
        ["U004", "SOCIAL-01", Channel.PAID_SOCIAL, 120, 0.65],
        ["U005", "ORGANIC-01", Channel.ORGANIC_SEARCH, 200, 0.80],
        ["U006", "ORGANIC-01", Channel.ORGANIC_SEARCH, 175, 0.80]
    ];

    for (const [id, campaignId, channel, revenue, margin] of customers) {
        await platform.acquireCustomer(new Customer({
            id,
            campaignId,
            channel,
            acquiredAt: "2026-06-15T10:00:00Z",
            firstPurchase: revenue,
            monthlyRevenue: 100,
            grossMargin: margin,
            retention: 0.92
        }));
    }

    console.log("\nCHANNEL PERFORMANCE");

    const report = await platform.generateReport(24);

    for (const item of report) {
        console.log({
            channel: item.channel,
            spend: item.spend,
            customers: item.customerCount,
            cac: item.cac?.toFixed(2) ?? "N/A",
            ltv: item.ltv?.toFixed(2) ?? "N/A",
            ltvCacRatio: item.ltvCacRatio?.toFixed(2) ?? "N/A",
            decision: item.decision
        });
    }

    console.log(
        "\nBlended CAC:",
        AcquisitionAnalytics.blendedCAC(
            platform.campaigns,
            platform.customers
        )?.toFixed(2)
    );

    const allocation = BudgetAllocator.allocate(
        100000,
        [
            { channel: Channel.PAID_SEARCH, expectedCac: 42 },
            { channel: Channel.PAID_SOCIAL, expectedCac: 60 },
            { channel: Channel.ORGANIC_SEARCH, expectedCac: 30 },
            { channel: Channel.REFERRAL, expectedCac: 25 }
        ]
    );

    console.log("\nPROPOSED BUDGET ALLOCATION");

    for (const [channel, amount] of allocation) {
        console.log(`${channel}: ${amount.toFixed(2)}`);
    }

    const attribution = AttributionEngine.attribute([
        {
            channel: Channel.PAID_SOCIAL,
            timestamp: "2026-06-01T10:00:00Z"
        },
        {
            channel: Channel.ORGANIC_SEARCH,
            timestamp: "2026-06-05T10:00:00Z"
        },
        {
            channel: Channel.PAID_SEARCH,
            timestamp: "2026-06-10T10:00:00Z"
        }
    ], "linear");

    console.log("\nLINEAR ATTRIBUTION");
    console.log(Object.fromEntries(attribution));

    console.log("\nEVENT COUNT:", platform.events.length);
}

if (require.main === module) {
    demonstration().catch(error => {
        console.error("Acquisition analysis failed:", error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    Channel,
    Campaign,
    Customer,
    AttributionEngine,
    AcquisitionAnalytics,
    AcquisitionPolicy,
    BudgetAllocator,
    AcquisitionPlatform,
    AcquisitionError
};
