/*
 * Pivot Charts | Visualizing Business Performance
 *
 * A self-contained JavaScript study file demonstrating:
 * - raw business transactions
 * - dimensions and measures
 * - pivot-style aggregation
 * - filters
 * - grouping
 * - KPI calculations
 * - business-performance charts in terminal form
 * - growth analysis
 * - ranking
 * - Pareto analysis
 * - rolling averages
 * - validation
 * - dashboard data structures
 * - asynchronous report generation
 * - performance and error-handling concepts
 *
 * Runtime:
 *   Node.js 18+ recommended.
 *
 * No external npm packages are required.
 */

"use strict";

// ============================================================================
// 1. FUNDAMENTAL BUSINESS DATA MODEL
// ============================================================================

class Transaction {
    constructor({
        transactionId,
        transactionDate,
        region,
        segment,
        category,
        product,
        channel,
        salesperson,
        quantity,
        sales,
        cost
    }) {
        this.transactionId = transactionId;
        this.transactionDate = new Date(`${transactionDate}T00:00:00Z`);
        this.region = region;
        this.segment = segment;
        this.category = category;
        this.product = product;
        this.channel = channel;
        this.salesperson = salesperson;
        this.quantity = quantity;
        this.sales = sales;
        this.cost = cost;
    }

    get profit() {
        return this.sales - this.cost;
    }

    get margin() {
        return this.sales === 0 ? null : this.profit / this.sales;
    }
}


// ============================================================================
// 2. SAMPLE BUSINESS DATA
// ============================================================================

function createTransactions() {
    const rows = [
        ["T001", "2026-01-05", "North", "Enterprise", "Technology", "Laptop", "Online", "Asha", 4, 4800, 3400],
        ["T002", "2026-01-08", "South", "Consumer", "Technology", "Phone", "Retail", "Ravi", 8, 6400, 5000],
        ["T003", "2026-01-12", "West", "SMB", "Office", "Chair", "Partner", "Neha", 12, 3600, 2280],
        ["T004", "2026-01-19", "East", "Enterprise", "Software", "Analytics", "Online", "Arjun", 3, 7500, 3300],
        ["T005", "2026-02-03", "North", "Consumer", "Technology", "Phone", "Retail", "Asha", 10, 8000, 6200],
        ["T006", "2026-02-10", "South", "SMB", "Office", "Desk", "Partner", "Ravi", 7, 3500, 2380],
        ["T007", "2026-02-15", "West", "Enterprise", "Software", "Analytics", "Online", "Neha", 4, 10000, 4400],
        ["T008", "2026-02-21", "East", "Consumer", "Technology", "Laptop", "Retail", "Arjun", 3, 3600, 2550],
        ["T009", "2026-03-04", "North", "SMB", "Office", "Chair", "Partner", "Asha", 15, 4500, 2850],
        ["T010", "2026-03-09", "South", "Enterprise", "Technology", "Laptop", "Online", "Ravi", 5, 6000, 4250],
        ["T011", "2026-03-16", "West", "Consumer", "Technology", "Phone", "Retail", "Neha", 14, 11200, 8680],
        ["T012", "2026-03-22", "East", "SMB", "Software", "Analytics", "Partner", "Arjun", 2, 5000, 2200],
        ["T013", "2026-04-02", "North", "Enterprise", "Software", "Analytics", "Online", "Asha", 5, 12500, 5500],
        ["T014", "2026-04-11", "South", "Consumer", "Office", "Desk", "Retail", "Ravi", 9, 4500, 3060],
        ["T015", "2026-04-17", "West", "SMB", "Technology", "Laptop", "Partner", "Neha", 6, 7200, 5100],
        ["T016", "2026-04-26", "East", "Enterprise", "Technology", "Phone", "Online", "Arjun", 7, 5600, 4340],
        ["T017", "2026-05-03", "North", "Consumer", "Technology", "Phone", "Retail", "Asha", 18, 14400, 11160],
        ["T018", "2026-05-08", "South", "SMB", "Office", "Chair", "Partner", "Ravi", 20, 6000, 3800],
        ["T019", "2026-05-15", "West", "Enterprise", "Software", "Analytics", "Online", "Neha", 6, 15000, 6600],
        ["T020", "2026-05-23", "East", "Consumer", "Technology", "Laptop", "Retail", "Arjun", 5, 6000, 4250],
        ["T021", "2026-06-04", "North", "SMB", "Office", "Desk", "Partner", "Asha", 11, 5500, 3740],
        ["T022", "2026-06-10", "South", "Enterprise", "Technology", "Laptop", "Online", "Ravi", 8, 9600, 6800],
        ["T023", "2026-06-16", "West", "Consumer", "Technology", "Phone", "Retail", "Neha", 20, 16000, 12400],
        ["T024", "2026-06-24", "East", "SMB", "Software", "Analytics", "Partner", "Arjun", 4, 10000, 4400],
        ["T025", "2026-07-03", "North", "Enterprise", "Technology", "Laptop", "Online", "Asha", 9, 10800, 7650],
        ["T026", "2026-07-09", "South", "Consumer", "Office", "Desk", "Retail", "Ravi", 13, 6500, 4420],
        ["T027", "2026-07-15", "West", "SMB", "Software", "Analytics", "Partner", "Neha", 5, 12500, 5500],
        ["T028", "2026-07-23", "East", "Enterprise", "Technology", "Phone", "Online", "Arjun", 10, 8000, 6200],
        ["T029", "2026-08-04", "North", "Consumer", "Technology", "Phone", "Retail", "Asha", 22, 17600, 13640],
        ["T030", "2026-08-12", "South", "SMB", "Office", "Chair", "Partner", "Ravi", 18, 5400, 3420],
        ["T031", "2026-08-18", "West", "Enterprise", "Software", "Analytics", "Online", "Neha", 8, 20000, 8800],
        ["T032", "2026-08-25", "East", "Consumer", "Technology", "Laptop", "Retail", "Arjun", 7, 8400, 5950],
        ["T033", "2026-09-02", "North", "SMB", "Office", "Desk", "Partner", "Asha", 14, 7000, 4760],
        ["T034", "2026-09-08", "South", "Enterprise", "Technology", "Laptop", "Online", "Ravi", 10, 12000, 8500],
        ["T035", "2026-09-16", "West", "Consumer", "Technology", "Phone", "Retail", "Neha", 25, 20000, 15500],
        ["T036", "2026-09-24", "East", "SMB", "Software", "Analytics", "Partner", "Arjun", 6, 15000, 6600],
        ["T037", "2026-09-27", "North", "Consumer", "Office", "Chair", "Retail", "Asha", 0, 0, 0]
    ];

    return rows.map(row => new Transaction({
        transactionId: row[0],
        transactionDate: row[1],
        region: row[2],
        segment: row[3],
        category: row[4],
        product: row[5],
        channel: row[6],
        salesperson: row[7],
        quantity: row[8],
        sales: row[9],
        cost: row[10]
    }));
}

const transactions = createTransactions();


// ============================================================================
// 3. FORMATTING HELPERS
// ============================================================================

const currencyFormatter = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2
});

function currency(value) {
    return currencyFormatter.format(value);
}

function percent(value) {
    return `${(value * 100).toFixed(2)}%`;
}

function printSection(title) {
    console.log(`\n${"=".repeat(78)}`);
    console.log(title);
    console.log("=".repeat(78));
}


// ============================================================================
// 4. CORE AGGREGATION
// ============================================================================

function sumBy(rows, field) {
    return rows.reduce((total, row) => total + Number(row[field]), 0);
}

function aggregateBy(rows, dimension, measures = ["sales"]) {
    const result = new Map();

    for (const row of rows) {
        const key = String(row[dimension]);

        if (!result.has(key)) {
            result.set(key, {
                sales: 0,
                cost: 0,
                profit: 0,
                quantity: 0
            });
        }

        const bucket = result.get(key);
        bucket.sales += row.sales;
        bucket.cost += row.cost;
        bucket.profit += row.profit;
        bucket.quantity += row.quantity;
    }

    return result;
}

function mapToObject(map) {
    return Object.fromEntries(map.entries());
}


// ============================================================================
// 5. BEGINNER PIVOT: SALES BY REGION
// ============================================================================

const salesByRegion = aggregateBy(transactions, "region");

printSection("SALES BY REGION");

for (const [region, metrics] of [...salesByRegion.entries()]
    .sort((a, b) => b[1].sales - a[1].sales)) {
    console.log(
        `${region.padEnd(12)} ${currency(metrics.sales).padStart(15)}`
    );
}


// ============================================================================
// 6. TWO-DIMENSIONAL PIVOT
// ============================================================================

function pivot2D(rows, rowDimension, columnDimension, measure) {
    const matrix = new Map();

    for (const row of rows) {
        const rowKey = String(row[rowDimension]);
        const columnKey = String(row[columnDimension]);

        if (!matrix.has(rowKey)) {
            matrix.set(rowKey, new Map());
        }

        const rowMap = matrix.get(rowKey);

        if (!rowMap.has(columnKey)) {
            rowMap.set(columnKey, 0);
        }

        rowMap.set(
            columnKey,
            rowMap.get(columnKey) + Number(row[measure])
        );
    }

    return matrix;
}

const regionSegmentPivot = pivot2D(
    transactions,
    "region",
    "segment",
    "sales"
);

printSection("REGION × SEGMENT PIVOT");

const segmentNames = [...new Set(transactions.map(row => row.segment))].sort();

console.log(
    "Region".padEnd(15) +
    segmentNames.map(segment => segment.padStart(16)).join("")
);

for (const region of [...regionSegmentPivot.keys()].sort()) {
    const values = segmentNames.map(segment => {
        return currency(
            regionSegmentPivot.get(region)?.get(segment) ?? 0
        ).padStart(16);
    });

    console.log(region.padEnd(15) + values.join(""));
}


// ============================================================================
// 7. TEXTUAL PIVOT CHART
// ============================================================================

function bar(value, maximum, width = 42) {
    if (maximum <= 0) {
        return "";
    }

    const count = Math.round((value / maximum) * width);
    return "#".repeat(count);
}

function printBarChart(title, data) {
    printSection(title);

    const entries = Object.entries(data)
        .sort((a, b) => b[1] - a[1]);

    const maximum = Math.max(...entries.map(([, value]) => value));

    for (const [label, value] of entries) {
        console.log(
            `${label.padEnd(15)} | ${bar(value, maximum).padEnd(42)} ${currency(value)}`
        );
    }
}

printBarChart(
    "PIVOT CHART: SALES BY REGION",
    Object.fromEntries(
        [...salesByRegion.entries()].map(([key, metrics]) => [key, metrics.sales])
    )
);


// ============================================================================
// 8. TIME GROUPING
// ============================================================================

function monthKey(dateObject) {
    const year = dateObject.getUTCFullYear();
    const month = String(dateObject.getUTCMonth() + 1).padStart(2, "0");
    return `${year}-${month}`;
}

function aggregateByMonth(rows) {
    const result = new Map();

    for (const row of rows) {
        const key = monthKey(row.transactionDate);

        if (!result.has(key)) {
            result.set(key, {
                sales: 0,
                cost: 0,
                profit: 0,
                quantity: 0
            });
        }

        const month = result.get(key);
        month.sales += row.sales;
        month.cost += row.cost;
        month.profit += row.profit;
        month.quantity += row.quantity;
    }

    return result;
}

const monthly = aggregateByMonth(transactions);

printBarChart(
    "PIVOT CHART: MONTHLY SALES",
    Object.fromEntries(
        [...monthly.entries()].map(([month, metrics]) => [month, metrics.sales])
    )
);


// ============================================================================
// 9. KPI CALCULATIONS
// ============================================================================

function calculateKPIs(rows) {
    const sales = sumBy(rows, "sales");
    const cost = sumBy(rows, "cost");
    const quantity = sumBy(rows, "quantity");
    const profit = sales - cost;

    return {
        revenue: sales,
        cost,
        profit,
        quantity,
        margin: sales === 0 ? null : profit / sales
    };
}

const kpis = calculateKPIs(transactions);

printSection("BUSINESS KPI CARDS");
console.log(`Revenue:       ${currency(kpis.revenue)}`);
console.log(`Cost:          ${currency(kpis.cost)}`);
console.log(`Profit:        ${currency(kpis.profit)}`);
console.log(`Units:         ${kpis.quantity.toLocaleString()}`);
console.log(`Profit Margin: ${kpis.margin === null ? "N/A" : percent(kpis.margin)}`);


// ============================================================================
// 10. FILTERING
// ============================================================================

function filterRows(rows, predicate) {
    return rows.filter(predicate);
}

const enterpriseRows = filterRows(
    transactions,
    row => row.segment === "Enterprise"
);

const enterpriseRegionSales = aggregateBy(
    enterpriseRows,
    "region"
);

printBarChart(
    "ENTERPRISE SALES BY REGION",
    Object.fromEntries(
        [...enterpriseRegionSales.entries()]
            .map(([key, value]) => [key, value.sales])
    )
);


// ============================================================================
// 11. GROUPING BY PRODUCT
// ============================================================================

const productMetrics = aggregateBy(transactions, "product");

printSection("PRODUCT PERFORMANCE");

for (const [product, metrics] of [...productMetrics.entries()]
    .sort((a, b) => b[1].sales - a[1].sales)) {
    const margin = metrics.sales === 0
        ? null
        : metrics.profit / metrics.sales;

    console.log(
        `${product.padEnd(12)} ` +
        `Sales=${currency(metrics.sales).padStart(14)} ` +
        `Profit=${currency(metrics.profit).padStart(14)} ` +
        `Margin=${margin === null ? "N/A" : percent(margin)}`
    );
}


// ============================================================================
// 12. TOP-N ANALYSIS
// ============================================================================

function topN(map, n, metric = "sales") {
    return [...map.entries()]
        .sort((a, b) => b[1][metric] - a[1][metric])
        .slice(0, n);
}

printSection("TOP 3 PRODUCTS");

topN(productMetrics, 3).forEach(([product, metrics], index) => {
    console.log(`${index + 1}. ${product}: ${currency(metrics.sales)}`);
});


// ============================================================================
// 13. PARETO ANALYSIS
// ============================================================================

function pareto(rows, dimension, measure) {
    const aggregated = aggregateBy(rows, dimension);
    const total = [...aggregated.values()]
        .reduce((sum, item) => sum + item[measure], 0);

    let cumulative = 0;

    return [...aggregated.entries()]
        .sort((a, b) => b[1][measure] - a[1][measure])
        .map(([key, metrics]) => {
            const value = metrics[measure];
            cumulative += value;

            return {
                key,
                value,
                share: total === 0 ? 0 : value / total,
                cumulativeShare: total === 0 ? 0 : cumulative / total
            };
        });
}

printSection("PRODUCT PARETO ANALYSIS");

for (const item of pareto(transactions, "product", "sales")) {
    console.log(
        `${item.key.padEnd(12)} ` +
        `Share=${percent(item.share).padStart(8)} ` +
        `Cumulative=${percent(item.cumulativeShare).padStart(10)}`
    );
}


// ============================================================================
// 14. GROWTH ANALYSIS
// ============================================================================

function growthRate(current, previous) {
    if (previous === 0) {
        return null;
    }

    return (current - previous) / previous;
}

function calculateSequentialGrowth(values) {
    return values.map((value, index) => {
        if (index === 0) {
            return null;
        }

        return growthRate(value, values[index - 1]);
    });
}

const monthlyEntries = [...monthly.entries()];
const monthlySalesValues = monthlyEntries.map(([, metrics]) => metrics.sales);
const monthlyGrowth = calculateSequentialGrowth(monthlySalesValues);

printSection("MONTH-OVER-MONTH SALES GROWTH");

monthlyEntries.forEach(([month], index) => {
    const growth = monthlyGrowth[index];

    console.log(
        `${month}: ${growth === null ? "N/A" : percent(growth)}`
    );
});


// ============================================================================
// 15. ROLLING AVERAGE
// ============================================================================

function rollingAverage(values, windowSize) {
    if (!Number.isInteger(windowSize) || windowSize <= 0) {
        throw new Error("windowSize must be a positive integer.");
    }

    return values.map((_, index) => {
        const start = Math.max(0, index - windowSize + 1);
        const window = values.slice(start, index + 1);

        return window.reduce((sum, value) => sum + value, 0) / window.length;
    });
}

const rollingSales = rollingAverage(monthlySalesValues, 3);

printSection("3-MONTH ROLLING SALES AVERAGE");

monthlyEntries.forEach(([month], index) => {
    console.log(`${month}: ${currency(rollingSales[index])}`);
});


// ============================================================================
// 16. RANKING
// ============================================================================

function denseRank(entries) {
    const sorted = [...entries].sort((a, b) => b[1] - a[1]);
    const ranking = new Map();

    let rank = 0;
    let previousValue = null;

    for (const [key, value] of sorted) {
        if (previousValue === null || value !== previousValue) {
            rank += 1;
        }

        ranking.set(key, rank);
        previousValue = value;
    }

    return ranking;
}

const salespersonSales = aggregateBy(transactions, "salesperson");
const salespersonValues = new Map(
    [...salespersonSales.entries()]
        .map(([name, metrics]) => [name, metrics.sales])
);

const salespersonRanks = denseRank(salespersonValues);

printSection("SALESPERSON RANKING");

for (const [name, sales] of [...salespersonValues.entries()]
    .sort((a, b) => b[1] - a[1])) {
    console.log(
        `Rank ${salespersonRanks.get(name)} ` +
        `${name.padEnd(10)} ${currency(sales)}`
    );
}


// ============================================================================
// 17. VALIDATION
// ============================================================================

function validateTransactions(rows) {
    const errors = [];
    const ids = new Set();

    for (const row of rows) {
        if (ids.has(row.transactionId)) {
            errors.push(`Duplicate transaction ID: ${row.transactionId}`);
        }

        ids.add(row.transactionId);

        if (row.quantity < 0) {
            errors.push(`Negative quantity: ${row.transactionId}`);
        }

        if (row.sales < 0) {
            errors.push(`Negative sales: ${row.transactionId}`);
        }

        if (row.cost < 0) {
            errors.push(`Negative cost: ${row.transactionId}`);
        }

        if (!row.region || !row.region.trim()) {
            errors.push(`Missing region: ${row.transactionId}`);
        }

        if (!row.product || !row.product.trim()) {
            errors.push(`Missing product: ${row.transactionId}`);
        }

        if (Number.isNaN(row.sales)) {
            errors.push(`Invalid sales: ${row.transactionId}`);
        }
    }

    return errors;
}

printSection("DATA VALIDATION");

const validationErrors = validateTransactions(transactions);

if (validationErrors.length === 0) {
    console.log("All sample records passed validation.");
} else {
    validationErrors.forEach(error => console.log(`ERROR: ${error}`));
}


// ============================================================================
// 18. EDGE CASES
// ============================================================================

function safeDivide(numerator, denominator) {
    return denominator === 0 ? null : numerator / denominator;
}

const zeroSales = transactions[transactions.length - 1];

printSection("ZERO-VALUE EDGE CASE");

console.log(
    `Transaction ${zeroSales.transactionId} margin:`,
    safeDivide(zeroSales.profit, zeroSales.sales)
);


// ============================================================================
// 19. EXECUTIVE DASHBOARD MODEL
// ============================================================================

function buildDashboardModel(rows) {
    const summary = calculateKPIs(rows);

    return {
        generatedAt: new Date().toISOString(),
        kpis: {
            revenue: summary.revenue,
            cost: summary.cost,
            profit: summary.profit,
            margin: summary.margin,
            quantity: summary.quantity
        },
        charts: {
            regionSales: mapToObject(
                new Map(
                    [...aggregateBy(rows, "region").entries()]
                        .map(([key, value]) => [key, value.sales])
                )
            ),
            productSales: mapToObject(
                new Map(
                    [...aggregateBy(rows, "product").entries()]
                        .map(([key, value]) => [key, value.sales])
                )
            ),
            monthlySales: mapToObject(
                new Map(
                    [...aggregateByMonth(rows).entries()]
                        .map(([key, value]) => [key, value.sales])
                )
            )
        }
    };
}

const dashboard = buildDashboardModel(transactions);

printSection("DASHBOARD JSON MODEL");
console.log(JSON.stringify(dashboard, null, 2));


// ============================================================================
// 20. ASYNCHRONOUS REPORT GENERATION
// ============================================================================

function delay(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}

async function generateAsyncReport(rows) {
    // In a real application, asynchronous operations could represent
    // database queries, API requests, or file reads.
    await delay(10);

    const model = buildDashboardModel(rows);

    return {
        status: "ready",
        generatedAt: model.generatedAt,
        revenue: model.kpis.revenue,
        profit: model.kpis.profit
    };
}


// ============================================================================
// 21. ERROR-HANDLING EXAMPLE
// ============================================================================

function requireNonEmpty(value, fieldName) {
    if (typeof value !== "string" || value.trim() === "") {
        throw new TypeError(`${fieldName} must be a non-empty string.`);
    }

    return value.trim();
}

function createValidatedDimension(value) {
    return requireNonEmpty(value, "dimension");
}

printSection("ERROR HANDLING");

try {
    console.log(createValidatedDimension("region"));
    console.log(createValidatedDimension(""));
} catch (error) {
    console.log(`Validation error: ${error.message}`);
}


// ============================================================================
// 22. PERFORMANCE DISCUSSION THROUGH MEASUREMENT
// ============================================================================

function measureAggregation(rows) {
    const start = process.hrtime.bigint();

    aggregateBy(rows, "region");

    const end = process.hrtime.bigint();

    return Number(end - start) / 1_000_000;
}

printSection("PERFORMANCE CHECK");
console.log(
    `One region aggregation completed in approximately ${measureAggregation(transactions).toFixed(4)} ms.`
);
console.log(
    "The result is hardware- and workload-dependent; production benchmarking should use representative datasets and repeated trials."
);


// ============================================================================
// 23. EXECUTIVE INSIGHTS
// ============================================================================

function generateInsights(rows) {
    const insights = [];

    const regionData = aggregateBy(rows, "region");
    const productData = aggregateBy(rows, "product");

    const bestRegion = [...regionData.entries()]
        .sort((a, b) => b[1].sales - a[1].sales)[0];

    const bestProduct = [...productData.entries()]
        .sort((a, b) => b[1].sales - a[1].sales)[0];

    if (bestRegion) {
        insights.push(
            `${bestRegion[0]} has the highest regional sales at ${currency(bestRegion[1].sales)}.`
        );
    }

    if (bestProduct) {
        insights.push(
            `${bestProduct[0]} has the highest product sales at ${currency(bestProduct[1].sales)}.`
        );
    }

    return insights;
}

printSection("EXECUTIVE INSIGHTS");

for (const insight of generateInsights(transactions)) {
    console.log(`- ${insight}`);
}


// ============================================================================
// 24. TESTS
// ============================================================================

function runTests(rows) {
    if (rows.length === 0) {
        throw new Error("Dataset must not be empty.");
    }

    const summary = calculateKPIs(rows);

    if (summary.revenue < 0) {
        throw new Error("Revenue cannot be negative.");
    }

    if (summary.cost < 0) {
        throw new Error("Cost cannot be negative.");
    }

    const regionData = aggregateBy(rows, "region");
    const regionSalesTotal = [...regionData.values()]
        .reduce((sum, value) => sum + value.sales, 0);

    if (Math.abs(regionSalesTotal - summary.revenue) > 0.000001) {
        throw new Error("Region aggregation does not reconcile with revenue.");
    }

    return true;
}

printSection("INTERNAL TESTS");

try {
    runTests(transactions);
    console.log("All internal tests passed.");
} catch (error) {
    console.error(`Test failure: ${error.message}`);
}


// ============================================================================
// 25. MAIN ASYNC ENTRY POINT
// ============================================================================

async function main() {
    const report = await generateAsyncReport(transactions);

    printSection("ASYNC REPORT");

    console.log(`Status:  ${report.status}`);
    console.log(`Revenue: ${currency(report.revenue)}`);
    console.log(`Profit:  ${currency(report.profit)}`);

    printSection("PIVOT CHART STUDY COMPLETE");
    console.log(
        "The program demonstrated dimensions, measures, aggregation, filtering, time grouping, ranking, growth, KPI construction, and dashboard data modeling."
    );
}

main().catch(error => {
    console.error(`Application failure: ${error.message}`);
    process.exitCode = 1;
});
