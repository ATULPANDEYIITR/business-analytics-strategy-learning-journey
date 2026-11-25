'use strict';

/**
 * Campaign Analytics Engine
 *
 * Event-driven campaign monitoring and performance evaluation.
 * Runtime: Node.js 18+
 *
 * Features:
 * - Campaign lifecycle management
 * - ROI, ROAS and funnel metrics
 * - Event-driven updates
 * - Channel aggregation
 * - Budget monitoring
 * - Campaign eligibility policies
 * - Attribution consistency checks
 * - Asynchronous reporting
 * - JSON export
 */

const fs = require('node:fs/promises');
const EventEmitter = require('node:events');

const Channel = Object.freeze({
    SEARCH: 'SEARCH',
    SOCIAL: 'SOCIAL',
    EMAIL: 'EMAIL',
    DISPLAY: 'DISPLAY',
    AFFILIATE: 'AFFILIATE',
    VIDEO: 'VIDEO'
});

const Status = Object.freeze({
    ACTIVE: 'ACTIVE',
    PAUSED: 'PAUSED',
    COMPLETED: 'COMPLETED'
});

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}

class CampaignNotFoundError extends Error {
    constructor(id) {
        super(`Campaign not found: ${id}`);
        this.name = 'CampaignNotFoundError';
    }
}

class Campaign {
    constructor(data) {
        this.id = String(data.id || '').trim();
        this.name = String(data.name || '').trim();
        this.channel = data.channel;
        this.status = data.status || Status.ACTIVE;

        this.budget = data.budget;
        this.spend = data.spend;
        this.impressions = data.impressions;
        this.clicks = data.clicks;
        this.conversions = data.conversions;
        this.revenue = data.revenue;

        this.validate();
    }

    validate() {
        if (!this.id || !this.name) {
            throw new ValidationError(
                'Campaign ID and name are required.'
            );
        }

        if (!Object.values(Channel).includes(this.channel)) {
            throw new ValidationError('Invalid campaign channel.');
        }

        if (!Object.values(Status).includes(this.status)) {
            throw new ValidationError('Invalid campaign status.');
        }

        for (const field of [
            'budget',
            'spend',
            'impressions',
            'clicks',
            'conversions',
            'revenue'
        ]) {
            if (
                typeof this[field] !== 'number' ||
                !Number.isFinite(this[field]) ||
                this[field] < 0
            ) {
                throw new ValidationError(
                    `${field} must be a non-negative finite number.`
                );
            }
        }

        if (this.budget <= 0) {
            throw new ValidationError(
                'Campaign budget must be positive.'
            );
        }

        if (this.clicks > this.impressions) {
            throw new ValidationError(
                'Clicks cannot exceed impressions.'
            );
        }

        if (this.conversions > this.clicks) {
            throw new ValidationError(
                'Conversions cannot exceed clicks.'
            );
        }
    }

    snapshot() {
        return Object.freeze({ ...this });
    }
}

class MetricCalculator {
    static calculate(campaign) {
        const {
            id,
            name,
            channel,
            spend,
            revenue,
            impressions,
            clicks,
            conversions,
            budget
        } = campaign;

        const profit = revenue - spend;

        const safeDivide = (a, b) => b === 0 ? 0 : a / b;

        return Object.freeze({
            id,
            name,
            channel,
            spend,
            revenue,
            profit,

            roi: safeDivide(profit, spend) * 100,
            roas: safeDivide(revenue, spend),

            ctr: safeDivide(clicks, impressions) * 100,
            conversionRate: safeDivide(conversions, clicks) * 100,

            cpc: safeDivide(spend, clicks),
            cpa: safeDivide(spend, conversions),
            cpm: safeDivide(spend * 1000, impressions),

            budgetUtilization: safeDivide(spend, budget) * 100
        });
    }
}

class CampaignStore extends EventEmitter {
    #campaigns = new Map();

    add(data) {
        const campaign = new Campaign(data);

        if (this.#campaigns.has(campaign.id)) {
            throw new ValidationError(
                `Duplicate campaign: ${campaign.id}`
            );
        }

        this.#campaigns.set(campaign.id, campaign);

        this.emit('campaign:created', campaign.snapshot());

        return campaign.snapshot();
    }

    get(id) {
        const campaign = this.#campaigns.get(id);

        if (!campaign) {
            throw new CampaignNotFoundError(id);
        }

        return campaign;
    }

    list() {
        return Array.from(
            this.#campaigns.values(),
            campaign => campaign.snapshot()
        );
    }

    update(id, changes) {
        const current = this.get(id);

        // Reconstruct the entire object before committing an update.
        // Failed validation leaves the original state unchanged.
        const updated = new Campaign({
            ...current,
            ...changes,
            id
        });

        this.#campaigns.set(id, updated);

        this.emit('campaign:updated', updated.snapshot());

        return updated.snapshot();
    }

    recordActivity(id, activity) {
        const current = this.get(id);

        const updated = new Campaign({
            ...current,
            impressions: current.impressions + activity.impressions,
            clicks: current.clicks + activity.clicks,
            conversions: current.conversions + activity.conversions,
            revenue: current.revenue + activity.revenue,
            spend: current.spend + activity.spend
        });

        this.#campaigns.set(id, updated);

        this.emit('campaign:activity', {
            id,
            metrics: MetricCalculator.calculate(updated)
        });

        return updated.snapshot();
    }

    remove(id) {
        if (!this.#campaigns.has(id)) {
            throw new CampaignNotFoundError(id);
        }

        const removed = this.#campaigns.get(id);

        this.#campaigns.delete(id);

        this.emit('campaign:deleted', removed.snapshot());
    }
}

class PerformanceService {
    constructor(store) {
        this.store = store;
    }

    evaluate() {
        return this.store.list().map(campaign => ({
            ...MetricCalculator.calculate(campaign),
            status: campaign.status
        }));
    }

    portfolio() {
        const campaigns = this.evaluate();

        const spend = campaigns.reduce(
            (sum, item) => sum + item.spend,
            0
        );

        const revenue = campaigns.reduce(
            (sum, item) => sum + item.revenue,
            0
        );

        return {
            campaignCount: campaigns.length,
            spend,
            revenue,
            profit: revenue - spend,
            roi: spend ? (revenue - spend) / spend * 100 : 0,
            roas: spend ? revenue / spend : 0
        };
    }

    channels() {
        const result = new Map();

        for (const item of this.evaluate()) {
            if (!result.has(item.channel)) {
                result.set(item.channel, {
                    channel: item.channel,
                    spend: 0,
                    revenue: 0,
                    campaigns: 0
                });
            }

            const entry = result.get(item.channel);

            entry.spend += item.spend;
            entry.revenue += item.revenue;
            entry.campaigns++;
        }

        return Array.from(result.values()).map(entry => ({
            ...entry,
            profit: entry.revenue - entry.spend,
            roi: entry.spend
                ? (entry.revenue - entry.spend) / entry.spend * 100
                : 0,
            roas: entry.spend
                ? entry.revenue / entry.spend
                : 0
        }));
    }

    ranking() {
        return this.evaluate().sort(
            (a, b) =>
                b.profit - a.profit ||
                b.roi - a.roi ||
                b.roas - a.roas
        );
    }
}

class BudgetPolicy {
    constructor({
        minimumRoas = 1.5,
        maximumUtilization = 120,
        reservePercentage = 0
    } = {}) {
        if (
            minimumRoas < 0 ||
            maximumUtilization <= 0 ||
            reservePercentage < 0 ||
            reservePercentage >= 100
        ) {
            throw new ValidationError(
                'Invalid budget policy.'
            );
        }

        this.minimumRoas = minimumRoas;
        this.maximumUtilization = maximumUtilization;
        this.reservePercentage = reservePercentage;
    }

    evaluate(metrics, additionalBudget) {
        if (
            !Number.isFinite(additionalBudget) ||
            additionalBudget < 0
        ) {
            throw new ValidationError(
                'Additional budget must be non-negative.'
            );
        }

        const eligible = metrics.filter(item =>
            item.status === Status.ACTIVE &&
            item.roas >= this.minimumRoas &&
            item.budgetUtilization < this.maximumUtilization
        );

        const available = additionalBudget *
            (1 - this.reservePercentage / 100);

        const totalSpend = eligible.reduce(
            (sum, item) => sum + item.spend,
            0
        );

        const allocations = eligible.map(item => ({
            campaignId: item.id,
            allocation: totalSpend
                ? available * item.spend / totalSpend
                : available / eligible.length
        }));

        return {
            availableBudget: available,
            eligibleCampaigns: eligible.length,
            allocations
        };
    }
}

class CampaignMonitor {
    constructor(store) {
        this.store = store;
        this.service = new PerformanceService(store);

        store.on('campaign:activity', event => {
            const metric = event.metrics;

            if (metric.budgetUtilization > 100) {
                process.emitWarning(
                    `Campaign ${event.id} exceeded its budget.`
                );
            }

            if (metric.roas < 1 && metric.spend > 0) {
                process.emitWarning(
                    `Campaign ${event.id} is generating a loss.`
                );
            }
        });
    }
}

class AttributionService {
    /**
     * Applies last-touch attribution to conversion events.
     *
     * The function expects one campaign ID per conversion.
     * It does not infer causality from clicks or impressions.
     */
    static lastTouch(conversions) {
        const attribution = new Map();

        for (const conversion of conversions) {
            if (
                !conversion.campaignId ||
                !Number.isFinite(conversion.revenue) ||
                conversion.revenue < 0
            ) {
                throw new ValidationError(
                    'Invalid attribution record.'
                );
            }

            const id = conversion.campaignId;

            attribution.set(
                id,
                (attribution.get(id) || 0) + conversion.revenue
            );
        }

        return Object.fromEntries(attribution);
    }
}

async function exportReport(report, filename) {
    const absolutePath = require('node:path').resolve(filename);

    await fs.writeFile(
        absolutePath,
        JSON.stringify(report, null, 2),
        {
            encoding: 'utf8',
            mode: 0o600
        }
    );

    return absolutePath;
}

function runTests() {
    const campaign = new Campaign({
        id: 'TEST',
        name: 'Validation Campaign',
        channel: Channel.SEARCH,
        budget: 1000,
        spend: 500,
        impressions: 10000,
        clicks: 1000,
        conversions: 100,
        revenue: 1500
    });

    const metrics = MetricCalculator.calculate(campaign);

    console.assert(metrics.roas === 3);
    console.assert(metrics.roi === 200);
    console.assert(metrics.ctr === 10);
    console.assert(metrics.cpa === 5);

    let rejected = false;

    try {
        new Campaign({
            ...campaign,
            id: 'BAD',
            clicks: 20000
        });
    } catch (error) {
        rejected = error instanceof ValidationError;
    }

    console.assert(rejected, 'Invalid campaign was accepted.');

    const store = new CampaignStore();

    store.add(campaign);

    const original = store.get('TEST').spend;

    try {
        store.update('TEST', { clicks: 20000 });
    } catch (error) {
        console.assert(error instanceof ValidationError);
    }

    console.assert(
        store.get('TEST').spend === original,
        'Failed update modified stored state.'
    );

    console.log('JavaScript validation tests passed.');
}

async function main() {
    runTests();

    const store = new CampaignStore();

    const monitor = new CampaignMonitor(store);

    const demoCampaigns = [
        {
            id: 'C001',
            name: 'Search Conversion',
            channel: Channel.SEARCH,
            budget: 50000,
            spend: 35000,
            impressions: 500000,
            clicks: 25000,
            conversions: 1500,
            revenue: 140000
        },
        {
            id: 'C002',
            name: 'Social Awareness',
            channel: Channel.SOCIAL,
            budget: 40000,
            spend: 30000,
            impressions: 800000,
            clicks: 16000,
            conversions: 400,
            revenue: 45000
        },
        {
            id: 'C003',
            name: 'Email Retention',
            channel: Channel.EMAIL,
            budget: 20000,
            spend: 12000,
            impressions: 200000,
            clicks: 30000,
            conversions: 2400,
            revenue: 96000
        },
        {
            id: 'C004',
            name: 'Display Remarketing',
            channel: Channel.DISPLAY,
            budget: 30000,
            spend: 25000,
            impressions: 1000000,
            clicks: 10000,
            conversions: 250,
            revenue: 18000
        },
        {
            id: 'C005',
            name: 'Affiliate Acquisition',
            channel: Channel.AFFILIATE,
            budget: 25000,
            spend: 15000,
            impressions: 300000,
            clicks: 12000,
            conversions: 900,
            revenue: 75000
        }
    ];

    for (const data of demoCampaigns) {
        store.add(data);
    }

    const service = new PerformanceService(store);

    const policy = new BudgetPolicy({
        minimumRoas: 1.5,
        maximumUtilization: 120,
        reservePercentage: 10
    });

    const report = {
        generatedAt: new Date().toISOString(),
        portfolio: service.portfolio(),
        channels: service.channels(),
        ranking: service.ranking(),
        budgetRecommendations: policy.evaluate(
            service.evaluate(),
            100000
        ),
        attribution: AttributionService.lastTouch([
            { campaignId: 'C001', revenue: 5000 },
            { campaignId: 'C001', revenue: 3000 },
            { campaignId: 'C003', revenue: 2000 }
        ])
    };

    console.log('\nPORTFOLIO');
    console.table([report.portfolio]);

    console.log('\nCAMPAIGN RANKING');
    console.table(report.ranking);

    console.log('\nCHANNEL ANALYSIS');
    console.table(report.channels);

    console.log('\nBUDGET ALLOCATION');
    console.table(report.budgetRecommendations.allocations);

    const output = await exportReport(
        report,
        'campaign_analytics_report.json'
    );

    console.log(`\nReport saved: ${output}`);

    // Keep the event monitor active for the application lifecycle.
    void monitor;
}

main().catch(error => {
    console.error('Campaign analytics failed:', error.message);
    process.exitCode = 1;
});
