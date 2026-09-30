/**
 * Executive Business Dashboard Workflow Model
 *
 * This Node.js-compatible JavaScript file models the logic behind an
 * executive Excel dashboard. It focuses on event-driven refreshes, KPI
 * calculation, dimensional analysis, target variance, filtering, data
 * validation, and dashboard state management.
 *
 * No external npm packages are required.
 */

"use strict";

// -----------------------------------------------------------------------------
// Business source data
// -----------------------------------------------------------------------------

const VALID_REGIONS = new Set(["North", "South", "East", "West"]);
const VALID_PRODUCTS = new Set([
    "Cloud Suite",
    "Analytics Pro",
    "Security Platform",
    "Data Hub"
]);
const VALID_CHANNELS = new Set(["Direct", "Online", "Partner"]);

const regionFactor = {
    North: 1.10,
    South: 0.94,
    East: 1.04,
    West: 1.18
};

const productEconomics = {
    "Cloud Suite": { price: 4200, margin: 0.61 },
    "Analytics Pro": { price: 3600, margin: 0.56 },
    "Security Platform": { price: 5100, margin: 0.64 },
    "Data Hub": { price: 2900, margin: 0.49 }
};

const channelFactor = {
    Direct: 1.00,
    Online: 0.91,
    Partner: 0.96
};

// -----------------------------------------------------------------------------
// Deterministic pseudo-random generator
// -----------------------------------------------------------------------------

function createRandom(seed) {
    let state = seed >>> 0;

    return function random() {
        state = (state * 1664525 + 1013904223) >>> 0;
        return state / 4294967296;
    };
}

function randomChoice(random, values) {
    return values[Math.floor(random() * values.length)];
}

function randomInteger(random, minimum, maximum) {
    return Math.floor(
        random() * (maximum - minimum + 1)
    ) + minimum;
}

// -----------------------------------------------------------------------------
// Date helpers
// -----------------------------------------------------------------------------

function dateRange(start, end) {
    const result = [];
    const current = new Date(start);

    while (current <= end) {
        result.push(new Date(current));
        current.setUTCDate(current.getUTCDate() + 1);
    }

    return result;
}

function monthKey(date) {
    return date.toISOString().slice(0, 7);
}

// -----------------------------------------------------------------------------
// Validation
// -----------------------------------------------------------------------------

function validateSale(sale) {
    if (!VALID_REGIONS.has(sale.region)) {
        throw new Error(`Invalid region: ${sale.region}`);
    }

    if (!VALID_PRODUCTS.has(sale.product)) {
        throw new Error(`Invalid product: ${sale.product}`);
    }

    if (!VALID_CHANNELS.has(sale.channel)) {
        throw new Error(`Invalid channel: ${sale.channel}`);
    }

    if (!Number.isInteger(sale.units) || sale.units <= 0) {
        throw new Error("Units must be a positive integer.");
    }

    if (!Number.isFinite(sale.revenue) || sale.revenue < 0) {
        throw new Error("Revenue must be a non-negative number.");
    }

    if (!Number.isFinite(sale.cost) || sale.cost < 0) {
        throw new Error("Cost must be a non-negative number.");
    }

    if (sale.cost > sale.revenue) {
        throw new Error("Cost cannot exceed revenue.");
    }
}

function validateDataset(sales) {
    if (!Array.isArray(sales) || sales.length === 0) {
        throw new Error("Dashboard source data cannot be empty.");
    }

    sales.forEach(validateSale);
    return sales;
}

// -----------------------------------------------------------------------------
// Source generation
// -----------------------------------------------------------------------------

function generateSales(start, end, seed = 42) {
    const random = createRandom(seed);
    const sales = [];

    const regions = [...VALID_REGIONS];
    const products = [...VALID_PRODUCTS];
    const channels = [...VALID_CHANNELS];

    for (const date of dateRange(start, end)) {
        const monthEndBoost = date.getUTCDate() >= 24 ? 1.18 : 1;

        const dailyTransactions = randomInteger(random, 2, 5);

        for (let index = 0; index < dailyTransactions; index += 1) {
            const region = randomChoice(random, regions);
            const product = randomChoice(random, products);
            const channel = randomChoice(random, channels);

            const units = randomInteger(random, 2, 14);
            const economics = productEconomics[product];

            const revenue = Number(
                (
                    economics.price *
                    units *
                    regionFactor[region] *
                    channelFactor[channel] *
                    monthEndBoost *
                    (0.90 + random() * 0.22)
                ).toFixed(2)
            );

            const margin = economics.margin *
                (0.94 + random() * 0.11);

            const cost = Number(
                (revenue * (1 - margin)).toFixed(2)
            );

            const sale = {
                date: new Date(date),
                region,
                product,
                channel,
                units,
                revenue,
                cost
            };

            validateSale(sale);
            sales.push(sale);
        }
    }

    return sales;
}

// -----------------------------------------------------------------------------
// KPI engine
// -----------------------------------------------------------------------------

function calculateKPIs(sales) {
    validateDataset(sales);

    const revenue = sales.reduce(
        (total, sale) => total + sale.revenue,
        0
    );

    const cost = sales.reduce(
        (total, sale) => total + sale.cost,
        0
    );

    const units = sales.reduce(
        (total, sale) => total + sale.units,
        0
    );

    const transactions = sales.length;
    const grossProfit = revenue - cost;

    return {
        revenue,
        cost,
        grossProfit,
        margin: revenue === 0 ? 0 : grossProfit / revenue,
        units,
        transactions,
        averageTransactionValue:
            transactions === 0 ? 0 : revenue / transactions
    };
}

// -----------------------------------------------------------------------------
// Dashboard dimension engine
// -----------------------------------------------------------------------------

function aggregateBy(sales, field) {
    validateDataset(sales);

    const groups = new Map();

    for (const sale of sales) {
        const key = sale[field];

        if (!groups.has(key)) {
            groups.set(key, {
                revenue: 0,
                cost: 0,
                units: 0,
                transactions: 0
            });
        }

        const group = groups.get(key);

        group.revenue += sale.revenue;
        group.cost += sale.cost;
        group.units += sale.units;
        group.transactions += 1;
    }

    return [...groups.entries()]
        .map(([key, values]) => ({
            key,
            ...values,
            grossProfit: values.revenue - values.cost,
            margin: values.revenue === 0
                ? 0
                : (values.revenue - values.cost) / values.revenue
        }))
        .sort((a, b) => b.revenue - a.revenue);
}

// -----------------------------------------------------------------------------
// Monthly trend model
// -----------------------------------------------------------------------------

function buildMonthlyTrend(sales) {
    validateDataset(sales);

    const grouped = new Map();

    for (const sale of sales) {
        const key = monthKey(sale.date);

        if (!grouped.has(key)) {
            grouped.set(key, {
                revenue: 0,
                cost: 0,
                units: 0
            });
        }

        const month = grouped.get(key);

        month.revenue += sale.revenue;
        month.cost += sale.cost;
        month.units += sale.units;
    }

    return [...grouped.entries()]
        .sort(([monthA], [monthB]) => monthA.localeCompare(monthB))
        .map(([month, values]) => {
            const grossProfit = values.revenue - values.cost;

            return {
                month,
                revenue: values.revenue,
                cost: values.cost,
                grossProfit,
                margin: values.revenue === 0
                    ? 0
                    : grossProfit / values.revenue,
                units: values.units
            };
        });
}

// -----------------------------------------------------------------------------
// Target and variance model
// -----------------------------------------------------------------------------

function buildTargets(monthlyTrend) {
    let previousTarget = null;

    return monthlyTrend.map((month, index) => {
        let target;

        if (previousTarget === null) {
            target = month.revenue * 0.97;
        } else {
            target = previousTarget * (1 + 0.08 / 12);
        }

        if (index % 3 === 2) {
            target *= 1.03;
        }

        previousTarget = target;

        return {
            month: month.month,
            target
        };
    });
}

function calculateVariance(monthlyTrend, targets) {
    const targetMap = new Map(
        targets.map(item => [item.month, item.target])
    );

    return monthlyTrend.map(month => {
        const target = targetMap.get(month.month) ?? 0;
        const variance = month.revenue - target;

        return {
            month: month.month,
            actual: month.revenue,
            target,
            variance,
            variancePercent: target === 0
                ? 0
                : variance / target,
            status: variance >= 0
                ? "Above Target"
                : "Below Target"
        };
    });
}

// -----------------------------------------------------------------------------
// Dashboard filtering
// -----------------------------------------------------------------------------

function filterSales(sales, filters = {}) {
    validateDataset(sales);

    return sales.filter(sale => {
        if (filters.region && sale.region !== filters.region) {
            return false;
        }

        if (filters.product && sale.product !== filters.product) {
            return false;
        }

        if (filters.channel && sale.channel !== filters.channel) {
            return false;
        }

        if (filters.startDate && sale.date < filters.startDate) {
            return false;
        }

        if (filters.endDate && sale.date > filters.endDate) {
            return false;
        }

        return true;
    });
}

// -----------------------------------------------------------------------------
// Event-driven dashboard state
// -----------------------------------------------------------------------------

class DashboardModel {
    constructor(sales) {
        this.sales = validateDataset(sales);
        this.filters = {};
        this.listeners = new Set();
        this.snapshot = null;

        this.refresh();
    }

    subscribe(listener) {
        if (typeof listener !== "function") {
            throw new TypeError("Dashboard listener must be a function.");
        }

        this.listeners.add(listener);

        return () => this.listeners.delete(listener);
    }

    setFilter(name, value) {
        if (value === null || value === undefined || value === "") {
            delete this.filters[name];
        } else {
            this.filters[name] = value;
        }

        this.refresh();
    }

    refresh() {
        const filteredSales = filterSales(this.sales, this.filters);
        const kpis = calculateKPIs(filteredSales);
        const monthly = buildMonthlyTrend(filteredSales);
        const targets = buildTargets(monthly);
        const variance = calculateVariance(monthly, targets);

        this.snapshot = {
            filters: { ...this.filters },
            kpis,
            regionalPerformance: aggregateBy(filteredSales, "region"),
            productPerformance: aggregateBy(filteredSales, "product"),
            channelPerformance: aggregateBy(filteredSales, "channel"),
            monthly,
            variance,
            updatedAt: new Date()
        };

        // Event notification mirrors the way a browser dashboard can refresh
        // visual components after a slicer/filter changes.
        for (const listener of this.listeners) {
            listener(this.snapshot);
        }
    }

    getSnapshot() {
        return structuredClone(this.snapshot);
    }
}

// -----------------------------------------------------------------------------
// Executive display formatting
// -----------------------------------------------------------------------------

const currency = value =>
    new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0
    }).format(value);

const percentage = value =>
    `${(value * 100).toFixed(1)}%`;

function printTable(title, rows, formatter) {
    console.log(`\n${title}`);
    console.log("-".repeat(78));

    rows.forEach(row => console.log(formatter(row)));
}

function renderDashboard(snapshot) {
    const { kpis } = snapshot;

    console.log("\nEXECUTIVE BUSINESS DASHBOARD");
    console.log("=".repeat(78));

    console.log(`Revenue:              ${currency(kpis.revenue)}`);
    console.log(`Gross Profit:         ${currency(kpis.grossProfit)}`);
    console.log(`Gross Margin:         ${percentage(kpis.margin)}`);
    console.log(`Units:                ${kpis.units.toLocaleString()}`);
    console.log(`Transactions:         ${kpis.transactions.toLocaleString()}`);
    console.log(
        `Average Transaction:  ${currency(kpis.averageTransactionValue)}`
    );

    printTable(
        "REGIONAL PERFORMANCE",
        snapshot.regionalPerformance,
        row =>
            `${row.key.padEnd(12)} ` +
            `Revenue ${currency(row.revenue).padStart(14)} ` +
            `Margin ${percentage(row.margin).padStart(7)}`
    );

    printTable(
        "PRODUCT PERFORMANCE",
        snapshot.productPerformance,
        row =>
            `${row.key.padEnd(22)} ` +
            `Revenue ${currency(row.revenue).padStart(14)} ` +
            `Margin ${percentage(row.margin).padStart(7)}`
    );

    printTable(
        "MONTHLY VARIANCE",
        snapshot.variance,
        row =>
            `${row.month}  ` +
            `Actual ${currency(row.actual).padStart(14)}  ` +
            `Target ${currency(row.target).padStart(14)}  ` +
            `${row.status}`
    );
}

// -----------------------------------------------------------------------------
// Scenario and error demonstrations
// -----------------------------------------------------------------------------

function demonstrateInvalidData() {
    try {
        validateSale({
            date: new Date("2026-01-01"),
            region: "Central",
            product: "Cloud Suite",
            channel: "Direct",
            units: 3,
            revenue: 10000,
            cost: 4000
        });
    } catch (error) {
        console.log("\nVALIDATION TEST");
        console.log(`Rejected invalid source row: ${error.message}`);
    }
}

function demonstrateFilteredScenario(model) {
    model.setFilter("region", "West");

    const filteredSnapshot = model.getSnapshot();

    console.log("\nFILTERED SCENARIO");
    console.log("=".repeat(78));
    console.log("Active filter: Region = West");
    console.log(
        `Filtered revenue: ${currency(filteredSnapshot.kpis.revenue)}`
    );
    console.log(
        `Filtered margin: ${percentage(filteredSnapshot.kpis.margin)}`
    );

    model.setFilter("region", null);
}

// -----------------------------------------------------------------------------
// Application entry point
// -----------------------------------------------------------------------------

function main() {
    const sales = generateSales(
        new Date("2026-01-01T00:00:00Z"),
        new Date("2026-06-30T00:00:00Z")
    );

    const dashboard = new DashboardModel(sales);

    dashboard.subscribe(snapshot => {
        console.log(
            `\nDashboard state refreshed at ` +
            `${snapshot.updatedAt.toISOString()}`
        );
    });

    renderDashboard(dashboard.getSnapshot());
    demonstrateFilteredScenario(dashboard);
    demonstrateInvalidData();

    console.log("\nDASHBOARD MODEL READY");
    console.log(
        "The model separates source data, calculations, filters, and presentation."
    );
}

main();
