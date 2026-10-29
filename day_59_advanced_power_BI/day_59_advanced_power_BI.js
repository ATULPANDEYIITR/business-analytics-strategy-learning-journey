"use strict";

/*
 * Advanced Power BI analytical calculations model.
 *
 * This Node.js program focuses on event-driven measure evaluation and
 * explicit filter-context objects. It models concepts commonly expressed
 * through DAX measures without attempting to reproduce the Power BI engine.
 */

const Channel = Object.freeze({
    ONLINE: "Online",
    RETAIL: "Retail",
    PARTNER: "Partner"
});

class ValidationError extends Error {}

class Sale {
    constructor({
        id,
        date,
        region,
        product,
        channel,
        customerId,
        quantity,
        unitPrice,
        unitCost
    }) {
        if (!Number.isInteger(id) || id <= 0) {
            throw new ValidationError("Sale id must be a positive integer.");
        }
        if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
            throw new ValidationError(`Invalid ISO date: ${date}`);
        }
        if (!Object.values(Channel).includes(channel)) {
            throw new ValidationError(`Invalid channel: ${channel}`);
        }
        if (!Number.isInteger(quantity) || quantity <= 0) {
            throw new ValidationError("Quantity must be positive.");
        }
        if (unitPrice < 0 || unitCost < 0) {
            throw new ValidationError("Prices cannot be negative.");
        }

        Object.assign(this, {
            id,
            date,
            region,
            product,
            channel,
            customerId,
            quantity,
            unitPrice,
            unitCost
        });
    }

    get revenue() {
        return this.quantity * this.unitPrice;
    }

    get cost() {
        return this.quantity * this.unitCost;
    }

    get margin() {
        return this.revenue - this.cost;
    }
}

class InventorySnapshot {
    constructor({ date, region, product, units }) {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
            throw new ValidationError(`Invalid snapshot date: ${date}`);
        }
        if (!Number.isInteger(units) || units < 0) {
            throw new ValidationError("Inventory units cannot be negative.");
        }
        Object.assign(this, { date, region, product, units });
    }
}

class FilterContext {
    constructor({
        dates = null,
        regions = null,
        products = null,
        channels = null,
        customers = null
    } = {}) {
        this.dates = dates ? new Set(dates) : null;
        this.regions = regions ? new Set(regions) : null;
        this.products = products ? new Set(products) : null;
        this.channels = channels ? new Set(channels) : null;
        this.customers = customers ? new Set(customers) : null;
    }

    with(overrides) {
        return new FilterContext({
            dates: overrides.dates === undefined ? this.dates : overrides.dates,
            regions: overrides.regions === undefined ? this.regions : overrides.regions,
            products: overrides.products === undefined ? this.products : overrides.products,
            channels: overrides.channels === undefined ? this.channels : overrides.channels,
            customers: overrides.customers === undefined ? this.customers : overrides.customers
        });
    }
}

class AnalyticsEngine {
    constructor(sales, inventory) {
        this.sales = Object.freeze([...sales]);
        this.inventory = Object.freeze([...inventory]);
    }

    filterSales(context) {
        return this.sales.filter((sale) => {
            if (context.dates && !context.dates.has(sale.date)) return false;
            if (context.regions && !context.regions.has(sale.region)) return false;
            if (context.products && !context.products.has(sale.product)) return false;
            if (context.channels && !context.channels.has(sale.channel)) return false;
            if (context.customers && !context.customers.has(sale.customerId)) return false;
            return true;
        });
    }

    filterInventory(context) {
        return this.inventory.filter((row) => {
            if (context.dates && !context.dates.has(row.date)) return false;
            if (context.regions && !context.regions.has(row.region)) return false;
            if (context.products && !context.products.has(row.product)) return false;
            return true;
        });
    }

    static round(value) {
        return Math.round((value + Number.EPSILON) * 100) / 100;
    }

    revenue(context) {
        return AnalyticsEngine.round(
            this.filterSales(context).reduce((sum, sale) => sum + sale.revenue, 0)
        );
    }

    cost(context) {
        return AnalyticsEngine.round(
            this.filterSales(context).reduce((sum, sale) => sum + sale.cost, 0)
        );
    }

    margin(context) {
        return AnalyticsEngine.round(this.revenue(context) - this.cost(context));
    }

    marginPercent(context) {
        const revenue = this.revenue(context);
        return revenue === 0
            ? 0
            : AnalyticsEngine.round(this.margin(context) * 100 / revenue);
    }

    distinctCustomers(context) {
        return new Set(
            this.filterSales(context).map((sale) => sale.customerId)
        ).size;
    }

    averageOrderValue(context) {
        const grouped = new Map();

        for (const sale of this.filterSales(context)) {
            grouped.set(
                sale.id,
                (grouped.get(sale.id) || 0) + sale.revenue
            );
        }

        if (grouped.size === 0) return 0;

        const total = [...grouped.values()]
            .reduce((sum, value) => sum + value, 0);

        return AnalyticsEngine.round(total / grouped.size);
    }

    static monthStart(isoDate) {
        return `${isoDate.slice(0, 7)}-01`;
    }

    static dateObject(isoDate) {
        return new Date(`${isoDate}T00:00:00Z`);
    }

    static isoDate(date) {
        return date.toISOString().slice(0, 10);
    }

    static monthDates(year, month) {
        const start = new Date(Date.UTC(year, month - 1, 1));
        const next = new Date(Date.UTC(year, month, 1));
        const result = [];

        for (
            let current = start;
            current < next;
            current = new Date(current.getTime() + 86400000)
        ) {
            result.push(AnalyticsEngine.isoDate(current));
        }

        return result;
    }

    previousMonthDates(context) {
        if (!context.dates || context.dates.size === 0) return [];

        const first = [...context.dates].sort()[0];
        const current = AnalyticsEngine.dateObject(
            AnalyticsEngine.monthStart(first)
        );

        current.setUTCMonth(current.getUTCMonth() - 1);

        return AnalyticsEngine.monthDates(
            current.getUTCFullYear(),
            current.getUTCMonth() + 1
        );
    }

    previousMonthRevenue(context) {
        const dates = this.previousMonthDates(context);
        return this.revenue(context.with({ dates }));
    }

    monthOverMonthPercent(context) {
        const current = this.revenue(context);
        const previous = this.previousMonthRevenue(context);

        return previous === 0
            ? 0
            : AnalyticsEngine.round((current - previous) * 100 / previous);
    }

    ytdRevenue(anchorDate, context) {
        const anchor = AnalyticsEngine.dateObject(anchorDate);
        const start = new Date(Date.UTC(anchor.getUTCFullYear(), 0, 1));
        const dates = [];

        for (
            let current = start;
            current <= anchor;
            current = new Date(current.getTime() + 86400000)
        ) {
            dates.push(AnalyticsEngine.isoDate(current));
        }

        return this.revenue(context.with({ dates }));
    }

    rollingRevenue(anchorDate, days, context) {
        if (!Number.isInteger(days) || days <= 0) {
            throw new ValidationError("Rolling period must be positive.");
        }

        const anchor = AnalyticsEngine.dateObject(anchorDate);
        const start = new Date(anchor.getTime());
        start.setUTCDate(start.getUTCDate() - days + 1);

        const dates = [];

        for (
            let current = start;
            current <= anchor;
            current = new Date(current.getTime() + 86400000)
        ) {
            dates.push(AnalyticsEngine.isoDate(current));
        }

        return this.revenue(context.with({ dates }));
    }

    percentOfTotal(context, removedDimensions) {
        const numerator = this.revenue(context);

        const totalContext = context.with({
            dates: removedDimensions.has("date") ? null : context.dates,
            regions: removedDimensions.has("region") ? null : context.regions,
            products: removedDimensions.has("product") ? null : context.products,
            channels: removedDimensions.has("channel") ? null : context.channels,
            customers: removedDimensions.has("customer") ? null : context.customers
        });

        const denominator = this.revenue(totalContext);

        return denominator === 0
            ? 0
            : AnalyticsEngine.round(numerator * 100 / denominator);
    }

    rankProducts(context) {
        const productSet = new Set(
            this.filterSales(
                context.with({ products: null })
            ).map((sale) => sale.product)
        );

        const scores = [...productSet].map((product) => {
            const productContext = context.with({
                products: [product]
            });

            return {
                product,
                revenue: this.revenue(productContext)
            };
        });

        scores.sort((a, b) =>
            b.revenue - a.revenue || a.product.localeCompare(b.product)
        );

        let previous = null;
        let rank = 0;

        return scores.map((row, index) => {
            if (previous !== row.revenue) {
                rank = index + 1;
            }
            previous = row.revenue;
            return { ...row, rank };
        });
    }

    latestInventory(context) {
        const rows = this.filterInventory(context);
        if (rows.length === 0) return 0;

        const latest = rows.reduce(
            (max, row) => row.date > max ? row.date : max,
            rows[0].date
        );

        return rows
            .filter((row) => row.date === latest)
            .reduce((sum, row) => sum + row.units, 0);
    }

    evaluate(context, anchorDate) {
        const result = {
            revenue: this.revenue(context),
            cost: this.cost(context),
            margin: this.margin(context),
            marginPercent: this.marginPercent(context),
            distinctCustomers: this.distinctCustomers(context),
            averageOrderValue: this.averageOrderValue(context),
            previousMonthRevenue: this.previousMonthRevenue(context),
            monthOverMonthPercent: this.monthOverMonthPercent(context),
            ytdRevenue: this.ytdRevenue(anchorDate, context),
            rolling7DayRevenue: this.rollingRevenue(anchorDate, 7, context),
            percentOfTotal: this.percentOfTotal(
                context,
                new Set(["region", "product", "channel", "customer"])
            ),
            latestInventory: this.latestInventory(context),
            productRank: this.rankProducts(context)
        };

        return Object.freeze(result);
    }
}

class MeasureEventBus {
    constructor() {
        this.handlers = new Map();
    }

    on(eventName, handler) {
        if (!this.handlers.has(eventName)) {
            this.handlers.set(eventName, new Set());
        }
        this.handlers.get(eventName).add(handler);

        return () => this.handlers.get(eventName)?.delete(handler);
    }

    async emit(eventName, payload) {
        const handlers = this.handlers.get(eventName) || new Set();

        // Promise.all makes independent measure listeners execute concurrently.
        await Promise.all(
            [...handlers].map((handler) => Promise.resolve(handler(payload)))
        );
    }
}

function sampleSales() {
    return [
        { id: 1001, date: "2026-01-02", region: "North", product: "Laptop", channel: Channel.ONLINE, customerId: 501, quantity: 2, unitPrice: 1200, unitCost: 800 },
        { id: 1002, date: "2026-01-04", region: "North", product: "Monitor", channel: Channel.RETAIL, customerId: 502, quantity: 4, unitPrice: 300, unitCost: 180 },
        { id: 1003, date: "2026-01-08", region: "South", product: "Laptop", channel: Channel.PARTNER, customerId: 503, quantity: 1, unitPrice: 1250, unitCost: 800 },
        { id: 1004, date: "2026-01-12", region: "North", product: "Keyboard", channel: Channel.ONLINE, customerId: 501, quantity: 5, unitPrice: 80, unitCost: 35 },
        { id: 1005, date: "2026-01-18", region: "South", product: "Monitor", channel: Channel.RETAIL, customerId: 504, quantity: 3, unitPrice: 310, unitCost: 180 },
        { id: 1006, date: "2026-01-23", region: "West", product: "Laptop", channel: Channel.ONLINE, customerId: 505, quantity: 1, unitPrice: 1190, unitCost: 800 },
        { id: 1007, date: "2026-01-28", region: "North", product: "Laptop", channel: Channel.ONLINE, customerId: 506, quantity: 1, unitPrice: 1210, unitCost: 800 },
        { id: 1008, date: "2026-02-02", region: "North", product: "Monitor", channel: Channel.RETAIL, customerId: 507, quantity: 5, unitPrice: 305, unitCost: 180 },
        { id: 1009, date: "2026-02-07", region: "South", product: "Laptop", channel: Channel.ONLINE, customerId: 503, quantity: 2, unitPrice: 1240, unitCost: 800 },
        { id: 1010, date: "2026-02-11", region: "West", product: "Keyboard", channel: Channel.PARTNER, customerId: 508, quantity: 8, unitPrice: 82, unitCost: 35 },
        { id: 1011, date: "2026-02-16", region: "North", product: "Laptop", channel: Channel.ONLINE, customerId: 509, quantity: 1, unitPrice: 1230, unitCost: 800 },
        { id: 1012, date: "2026-02-20", region: "South", product: "Monitor", channel: Channel.RETAIL, customerId: 510, quantity: 4, unitPrice: 315, unitCost: 180 },
        { id: 1013, date: "2026-02-24", region: "West", product: "Laptop", channel: Channel.PARTNER, customerId: 511, quantity: 2, unitPrice: 1180, unitCost: 800 },
        { id: 1014, date: "2026-02-27", region: "North", product: "Keyboard", channel: Channel.ONLINE, customerId: 512, quantity: 10, unitPrice: 78, unitCost: 35 },
        { id: 1015, date: "2026-03-02", region: "South", product: "Laptop", channel: Channel.ONLINE, customerId: 513, quantity: 2, unitPrice: 1260, unitCost: 800 },
        { id: 1016, date: "2026-03-05", region: "North", product: "Monitor", channel: Channel.RETAIL, customerId: 514, quantity: 6, unitPrice: 310, unitCost: 180 },
        { id: 1017, date: "2026-03-10", region: "West", product: "Keyboard", channel: Channel.PARTNER, customerId: 515, quantity: 7, unitPrice: 85, unitCost: 35 },
        { id: 1018, date: "2026-03-14", region: "South", product: "Laptop", channel: Channel.ONLINE, customerId: 516, quantity: 1, unitPrice: 1270, unitCost: 800 }
    ].map((row) => new Sale(row));
}

function sampleInventory() {
    return [
        { date: "2026-01-31", region: "North", product: "Laptop", units: 42 },
        { date: "2026-01-31", region: "North", product: "Monitor", units: 70 },
        { date: "2026-01-31", region: "South", product: "Laptop", units: 31 },
        { date: "2026-02-28", region: "North", product: "Laptop", units: 37 },
        { date: "2026-02-28", region: "North", product: "Monitor", units: 64 },
        { date: "2026-02-28", region: "South", product: "Laptop", units: 26 },
        { date: "2026-02-28", region: "West", product: "Keyboard", units: 90 },
        { date: "2026-03-15", region: "North", product: "Laptop", units: 34 },
        { date: "2026-03-15", region: "North", product: "Monitor", units: 58 },
        { date: "2026-03-15", region: "South", product: "Laptop", units: 24 },
        { date: "2026-03-15", region: "West", product: "Keyboard", units: 82 }
    ].map((row) => new InventorySnapshot(row));
}

async function main() {
    const engine = new AnalyticsEngine(sampleSales(), sampleInventory());

    const februaryContext = new FilterContext({
        dates: AnalyticsEngine.monthDates(2026, 2),
        regions: ["North", "South"]
    });

    const eventBus = new MeasureEventBus();

    eventBus.on("measureEvaluated", (result) => {
        console.log(
            `Revenue=${result.revenue}, Margin=${result.margin}, ` +
            `MoM=${result.monthOverMonthPercent}%`
        );
    });

    const result = engine.evaluate(
        februaryContext,
        "2026-02-28"
    );

    if (result.revenue <= 0) {
        throw new Error("Analytical validation failed: revenue must be positive.");
    }

    await eventBus.emit("measureEvaluated", result);

    console.log("\nAdvanced measure evaluation");
    console.log(JSON.stringify(result, null, 2));

    // Explicit edge-case validation.
    const empty = new FilterContext({ products: ["Unknown Product"] });
    if (engine.revenue(empty) !== 0) {
        throw new Error("Empty filter context should produce zero revenue.");
    }

    console.log("\nValidation: passed.");
    console.log(
        "Performance: Set-based filter membership is O(1) average for dimensions; " +
        "measure evaluation still scans the fact rows."
    );
    console.log(
        "Security: input is validated before entering the analytical model; " +
        "no dynamic code execution or external credentials are used."
    );
}

main().catch((error) => {
    console.error(`Execution failed: ${error.message}`);
    process.exitCode = 1;
});
