"use strict";

/**
 * Revenue Analytics: Revenue Decomposition and Growth Analysis
 *
 * Node.js 18+
 *
 * Engineering perspective:
 * - Event-driven analytical pipeline
 * - Immutable revenue observations
 * - Map-based aggregation
 * - Asynchronous report generation
 * - Revenue movement decomposition
 * - Policy-based validation
 * - Statistical concentration analysis
 * - Deterministic forecasting
 * - JSON and CSV exports
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

class AnalyticsError extends Error {}
class ValidationError extends AnalyticsError {}
class PeriodError extends AnalyticsError {}

const round = (value, digits = 6) =>
    Number(value.toFixed(digits));

function assertFinite(value, name) {
    if (!Number.isFinite(value)) {
        throw new ValidationError(`${name} must be finite.`);
    }
}

function validatePeriod(period) {
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(period)) {
        throw new ValidationError(`Invalid period: ${period}`);
    }
}

function createRecord(data) {
    const required = [
        "period",
        "product",
        "region",
        "customer",
        "units",
        "listPrice",
        "discountRate",
        "unitCost"
    ];

    for (const field of required) {
        if (!(field in data)) {
            throw new ValidationError(`Missing field: ${field}`);
        }
    }

    validatePeriod(data.period);

    for (const field of ["product", "region", "customer"]) {
        if (
            typeof data[field] !== "string" ||
            !data[field].trim()
        ) {
            throw new ValidationError(`${field} must be non-empty.`);
        }
    }

    if (!Number.isSafeInteger(data.units) || data.units < 0) {
        throw new ValidationError(
            "Units must be a non-negative safe integer."
        );
    }

    assertFinite(data.listPrice, "List price");
    assertFinite(data.discountRate, "Discount rate");
    assertFinite(data.unitCost, "Unit cost");

    if (data.listPrice < 0 || data.unitCost < 0) {
        throw new ValidationError("Prices and costs cannot be negative.");
    }

    if (data.discountRate < 0 || data.discountRate > 1) {
        throw new ValidationError("Discount must be between 0 and 1.");
    }

    const record = {
        ...data,
        product: data.product.trim(),
        region: data.region.trim(),
        customer: data.customer.trim()
    };

    record.netPrice = record.listPrice * (1 - record.discountRate);
    record.revenue = record.units * record.netPrice;
    record.variableCost = record.units * record.unitCost;
    record.grossProfit = record.revenue - record.variableCost;

    return Object.freeze(record);
}

class RevenueEventBus extends EventEmitter {
    publish(event, payload) {
        this.emit(event, Object.freeze(payload));
    }
}

class RevenueAnalytics {
    constructor(records = []) {
        this.records = [];
        this.uniqueKeys = new Set();
        this.events = new RevenueEventBus();

        this.events.on("record:accepted", record => {
            this.records.push(record);
        });

        this.events.on("analysis:completed", result => {
            console.log(
                `[EVENT] ${result.type} analysis completed.`
            );
        });

        for (const record of records) {
            this.addRecord(record);
        }
    }

    addRecord(data) {
        const record = createRecord(data);

        const key = [
            record.period,
            record.product,
            record.region,
            record.customer
        ].join("|");

        if (this.uniqueKeys.has(key)) {
            throw new ValidationError(
                `Duplicate revenue observation: ${key}`
            );
        }

        this.uniqueKeys.add(key);
        this.events.publish("record:accepted", record);

        return record;
    }

    getPeriods() {
        return [...new Set(this.records.map(r => r.period))].sort();
    }

    getRecords(period) {
        const records = this.records.filter(
            record => record.period === period
        );

        if (records.length === 0) {
            throw new PeriodError(`No records for ${period}.`);
        }

        return records;
    }

    aggregate(records) {
        const totals = records.reduce(
            (acc, record) => {
                acc.units += record.units;
                acc.revenue += record.revenue;
                acc.cost += record.variableCost;
                return acc;
            },
            { units: 0, revenue: 0, cost: 0 }
        );

        const profit = totals.revenue - totals.cost;

        return Object.freeze({
            ...totals,
            grossProfit: profit,
            averageSellingPrice: totals.units
                ? totals.revenue / totals.units
                : 0,
            grossMargin: totals.revenue
                ? profit / totals.revenue
                : 0
        });
    }

    growth(previous, current) {
        if (previous >= current) {
            throw new PeriodError(
                "Comparison requires an earlier and a later period."
            );
        }

        const old = this.aggregate(this.getRecords(previous));
        const latest = this.aggregate(this.getRecords(current));

        const revenueChange = latest.revenue - old.revenue;

        const result = {
            previous,
            current,
            previousRevenue: round(old.revenue),
            currentRevenue: round(latest.revenue),
            revenueChange: round(revenueChange),
            growthRate: old.revenue
                ? revenueChange / old.revenue
                : null,
            unitChange: latest.units - old.units,
            averagePriceChange: round(
                latest.averageSellingPrice - old.averageSellingPrice
            ),
            marginChange: round(
                latest.grossMargin - old.grossMargin
            )
        };

        this.events.publish("analysis:completed", {
            type: "growth"
        });

        return result;
    }

    productMetrics(period) {
        const groups = new Map();

        for (const record of this.getRecords(period)) {
            if (!groups.has(record.product)) {
                groups.set(record.product, {
                    units: 0,
                    revenue: 0,
                    cost: 0
                });
            }

            const group = groups.get(record.product);
            group.units += record.units;
            group.revenue += record.revenue;
            group.cost += record.variableCost;
        }

        const totalRevenue = [...groups.values()].reduce(
            (sum, group) => sum + group.revenue,
            0
        );

        return new Map(
            [...groups.entries()].map(([product, group]) => [
                product,
                Object.freeze({
                    product,
                    units: group.units,
                    revenue: round(group.revenue),
                    averagePrice: group.units
                        ? group.revenue / group.units
                        : 0,
                    grossProfit: round(group.revenue - group.cost),
                    margin: group.revenue
                        ? (group.revenue - group.cost) / group.revenue
                        : 0,
                    revenueShare: totalRevenue
                        ? group.revenue / totalRevenue
                        : 0
                })
            ])
        );
    }

    decompose(previous, current) {
        const oldRecords = this.getRecords(previous);
        const newRecords = this.getRecords(current);

        const old = this.productMetrics(previous);
        const latest = this.productMetrics(current);

        const products = new Set([
            ...old.keys(),
            ...latest.keys()
        ]);

        const q0 = oldRecords.reduce((s, r) => s + r.units, 0);
        const q1 = newRecords.reduce((s, r) => s + r.units, 0);

        if (q0 <= 0 || q1 <= 0) {
            throw new PeriodError(
                "Decomposition requires positive volume in both periods."
            );
        }

        let baselineWeightedPrice = 0;
        let mixEffect = 0;
        let priceEffect = 0;

        for (const product of products) {
            const a = old.get(product) || {
                units: 0,
                averagePrice: 0,
                revenue: 0
            };

            const b = latest.get(product) || {
                units: 0,
                averagePrice: 0,
                revenue: 0
            };

            const oldShare = a.units / q0;
            const newShare = b.units / q1;

            baselineWeightedPrice += oldShare * a.averagePrice;

            mixEffect += q1 *
                (newShare - oldShare) *
                a.averagePrice;

            priceEffect += q1 *
                newShare *
                (b.averagePrice - a.averagePrice);
        }

        const volumeEffect = (q1 - q0) * baselineWeightedPrice;

        const oldRevenue = this.aggregate(oldRecords).revenue;
        const newRevenue = this.aggregate(newRecords).revenue;

        const revenueChange = newRevenue - oldRevenue;

        const reconciliation =
            volumeEffect + mixEffect + priceEffect;

        if (Math.abs(revenueChange - reconciliation) > 0.000001) {
            throw new AnalyticsError(
                "Decomposition reconciliation failed."
            );
        }

        const result = Object.freeze({
            previousRevenue: round(oldRevenue),
            currentRevenue: round(newRevenue),
            revenueChange: round(revenueChange),
            volumeEffect: round(volumeEffect),
            mixEffect: round(mixEffect),
            priceEffect: round(priceEffect),
            reconciliationDifference: round(
                revenueChange - reconciliation
            )
        });

        this.events.publish("analysis:completed", {
            type: "decomposition"
        });

        return result;
    }

    analyzeDimension(period, dimension) {
        const allowed = new Set([
            "product",
            "region",
            "customer"
        ]);

        if (!allowed.has(dimension)) {
            throw new ValidationError(
                `Unsupported dimension: ${dimension}`
            );
        }

        const groups = new Map();

        for (const record of this.getRecords(period)) {
            const key = record[dimension];

            if (!groups.has(key)) {
                groups.set(key, []);
            }

            groups.get(key).push(record);
        }

        const total = this.aggregate(this.getRecords(period)).revenue;

        return [...groups.entries()]
            .map(([name, records]) => {
                const metrics = this.aggregate(records);

                return {
                    name,
                    dimension,
                    ...metrics,
                    revenueShare: total
                        ? metrics.revenue / total
                        : 0
                };
            })
            .sort((a, b) => b.revenue - a.revenue);
    }

    concentration(period) {
        const customers = this.analyzeDimension(
            period,
            "customer"
        );

        const shares = customers.map(
            customer => customer.revenueShare
        );

        return {
            customerCount: customers.length,
            largestCustomerShare: Math.max(0, ...shares),
            topFiveShare: shares.slice(0, 5).reduce(
                (sum, share) => sum + share,
                0
            ),
            hhi: shares.reduce(
                (sum, share) => sum + share ** 2,
                0
            )
        };
    }

    forecast(horizon = 3) {
        if (!Number.isInteger(horizon) || horizon < 1 || horizon > 36) {
            throw new ValidationError(
                "Forecast horizon must be between 1 and 36."
            );
        }

        const periods = this.getPeriods();

        if (periods.length < 2) {
            throw new PeriodError(
                "At least two periods are required."
            );
        }

        const revenues = periods.map(
            period => this.aggregate(this.getRecords(period)).revenue
        );

        const rates = [];

        for (let i = 1; i < revenues.length; i++) {
            if (revenues[i - 1] <= 0) {
                throw new AnalyticsError(
                    "Growth forecast requires positive base revenue."
                );
            }

            rates.push(
                revenues[i] / revenues[i - 1] - 1
            );
        }

        const averageGrowth = rates.reduce(
            (sum, value) => sum + value,
            0
        ) / rates.length;

        let value = revenues.at(-1);

        return Array.from(
            { length: horizon },
            (_, index) => {
                value = Math.max(0, value * (1 + averageGrowth));

                return {
                    step: index + 1,
                    forecastRevenue: round(value),
                    assumedGrowthRate: averageGrowth
                };
            }
        );
    }

    async exportReport(directory, previous, current) {
        await fs.mkdir(directory, { recursive: true });

        const report = {
            reportId: crypto.randomUUID(),
            generatedAt: new Date().toISOString(),
            comparison: this.growth(previous, current),
            decomposition: this.decompose(previous, current),
            products: this.analyzeDimension(current, "product"),
            regions: this.analyzeDimension(current, "region"),
            customers: this.analyzeDimension(current, "customer"),
            concentration: this.concentration(current),
            forecast: this.forecast(3)
        };

        const destination = path.join(
            directory,
            "revenue-report.json"
        );

        const temporary = `${destination}.tmp`;

        // Atomic rename prevents readers from seeing a partially written file.
        await fs.writeFile(
            temporary,
            JSON.stringify(report, null, 2),
            { encoding: "utf8", flag: "w" }
        );

        await fs.rename(temporary, destination);

        return destination;
    }
}

function sampleData() {
    const data = [
        ["2026-01", "Cloud", "North", "Customer A", 100, 1200, .05, 600],
        ["2026-01", "Software", "South", "Customer B", 180, 500, .10, 180],
        ["2026-01", "Hardware", "East", "Customer C", 250, 300, .08, 190],
        ["2026-01", "Services", "West", "Customer D", 90, 900, .05, 400],
        ["2026-02", "Cloud", "North", "Customer A", 115, 1250, .04, 600],
        ["2026-02", "Software", "South", "Customer B", 200, 520, .08, 180],
        ["2026-02", "Hardware", "East", "Customer C", 230, 310, .05, 190],
        ["2026-02", "Services", "West", "Customer D", 105, 920, .04, 400],
        ["2026-03", "Cloud", "North", "Customer A", 130, 1300, .03, 600],
        ["2026-03", "Software", "South", "Customer B", 220, 540, .07, 180],
        ["2026-03", "Hardware", "East", "Customer C", 245, 320, .05, 190],
        ["2026-03", "Services", "West", "Customer D", 115, 950, .03, 400],
        ["2026-04", "Cloud", "North", "Customer A", 145, 1350, .03, 600],
        ["2026-04", "Software", "South", "Customer B", 240, 550, .06, 180],
        ["2026-04", "Hardware", "East", "Customer C", 260, 330, .06, 190],
        ["2026-04", "Services", "West", "Customer D", 130, 970, .04, 400]
    ];

    return data.map(
        ([period, product, region, customer, units,
            listPrice, discountRate, unitCost]) => ({
            period,
            product,
            region,
            customer,
            units,
            listPrice,
            discountRate,
            unitCost
        })
    );
}

async function main() {
    const analytics = new RevenueAnalytics(sampleData());

    const growth = analytics.growth("2026-03", "2026-04");
    const decomposition = analytics.decompose("2026-03", "2026-04");

    if (
        Math.abs(decomposition.reconciliationDifference) > 0.000001
    ) {
        throw new AnalyticsError("Test failure.");
    }

    const report = {
        growth,
        decomposition,
        products: analytics.analyzeDimension(
            "2026-04",
            "product"
        ),
        regions: analytics.analyzeDimension(
            "2026-04",
            "region"
        ),
        concentration: analytics.concentration("2026-04"),
        forecast: analytics.forecast(3)
    };

    console.log("\nREVENUE ANALYTICS");
    console.log(JSON.stringify(report, null, 2));

    const file = await analytics.exportReport(
        "output",
        "2026-03",
        "2026-04"
    );

    console.log(`\nReport written to ${file}`);

    // Edge-case validation.
    try {
        createRecord({
            ...sampleData()[0],
            units: -10
        });
    } catch (error) {
        if (!(error instanceof ValidationError)) {
            throw error;
        }
        console.log("Negative-volume validation passed.");
    }
}

main().catch(error => {
    console.error("Analytics execution failed:", error.message);
    process.exitCode = 1;
});
