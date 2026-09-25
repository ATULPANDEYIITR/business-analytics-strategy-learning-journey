/*
 * Pivot Tables: Aggregating and Analyzing Business Data
 *
 * Self-contained JavaScript study file.
 *
 * Demonstrates:
 * - Dimensions and measures
 * - Grouping
 * - SUM, COUNT, AVG, MIN, MAX
 * - Two-dimensional pivots
 * - Filtering
 * - Calculated fields
 * - Percentage of total
 * - Time grouping
 * - Ranking
 * - Conditional aggregation
 * - Drill-down
 * - Validation
 * - Functional programming
 * - Map-based aggregation
 * - Async processing
 * - Performance considerations
 * - Browser-compatible data presentation concepts
 */

"use strict";

// -----------------------------------------------------------------------------
// 1. SAMPLE DATA
// -----------------------------------------------------------------------------

const sales = [
    {
        orderId: "O1001",
        orderDate: "2026-01-05",
        region: "North",
        category: "Electronics",
        product: "Laptop",
        salesperson: "Asha",
        channel: "Online",
        units: 5,
        unitPrice: 900,
        discount: 0.05,
        costPerUnit: 650
    },
    {
        orderId: "O1002",
        orderDate: "2026-01-08",
        region: "North",
        category: "Electronics",
        product: "Monitor",
        salesperson: "Ravi",
        channel: "Retail",
        units: 8,
        unitPrice: 300,
        discount: 0.02,
        costPerUnit: 210
    },
    {
        orderId: "O1003",
        orderDate: "2026-01-15",
        region: "South",
        category: "Furniture",
        product: "Desk",
        salesperson: "Meera",
        channel: "Online",
        units: 4,
        unitPrice: 450,
        discount: 0.10,
        costPerUnit: 300
    },
    {
        orderId: "O1004",
        orderDate: "2026-01-21",
        region: "West",
        category: "Office",
        product: "Chair",
        salesperson: "Arjun",
        channel: "Retail",
        units: 12,
        unitPrice: 180,
        discount: 0.05,
        costPerUnit: 110
    },
    {
        orderId: "O1005",
        orderDate: "2026-02-02",
        region: "East",
        category: "Electronics",
        product: "Laptop",
        salesperson: "Asha",
        channel: "Online",
        units: 3,
        unitPrice: 950,
        discount: 0,
        costPerUnit: 680
    },
    {
        orderId: "O1006",
        orderDate: "2026-02-06",
        region: "North",
        category: "Furniture",
        product: "Desk",
        salesperson: "Ravi",
        channel: "Online",
        units: 7,
        unitPrice: 425,
        discount: 0.08,
        costPerUnit: 295
    },
    {
        orderId: "O1007",
        orderDate: "2026-02-13",
        region: "South",
        category: "Office",
        product: "Chair",
        salesperson: "Meera",
        channel: "Retail",
        units: 15,
        unitPrice: 175,
        discount: 0.03,
        costPerUnit: 108
    },
    {
        orderId: "O1008",
        orderDate: "2026-02-20",
        region: "West",
        category: "Electronics",
        product: "Monitor",
        salesperson: "Arjun",
        channel: "Online",
        units: 10,
        unitPrice: 290,
        discount: 0.04,
        costPerUnit: 205
    },
    {
        orderId: "O1009",
        orderDate: "2026-03-03",
        region: "East",
        category: "Furniture",
        product: "Desk",
        salesperson: "Asha",
        channel: "Retail",
        units: 6,
        unitPrice: 470,
        discount: 0.06,
        costPerUnit: 310
    },
    {
        orderId: "O1010",
        orderDate: "2026-03-09",
        region: "North",
        category: "Office",
        product: "Chair",
        salesperson: "Ravi",
        channel: "Online",
        units: 20,
        unitPrice: 165,
        discount: 0.02,
        costPerUnit: 105
    },
    {
        orderId: "O1011",
        orderDate: "2026-03-18",
        region: "South",
        category: "Electronics",
        product: "Laptop",
        salesperson: "Meera",
        channel: "Retail",
        units: 4,
        unitPrice: 920,
        discount: 0.07,
        costPerUnit: 655
    },
    {
        orderId: "O1012",
        orderDate: "2026-03-25",
        region: "West",
        category: "Furniture",
        product: "Desk",
        salesperson: "Arjun",
        channel: "Online",
        units: 5,
        unitPrice: 460,
        discount: 0.05,
        costPerUnit: 305
    }
];


// -----------------------------------------------------------------------------
// 2. DERIVED BUSINESS MEASURES
// -----------------------------------------------------------------------------

function grossSales(record) {
    return record.units * record.unitPrice;
}

function discountAmount(record) {
    return grossSales(record) * record.discount;
}

function netSales(record) {
    return grossSales(record) - discountAmount(record);
}

function totalCost(record) {
    return record.units * record.costPerUnit;
}

function profit(record) {
    return netSales(record) - totalCost(record);
}

function marginPercent(record) {
    const sales = netSales(record);
    return sales === 0 ? 0 : profit(record) / sales * 100;
}

function money(value) {
    return value.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}


// -----------------------------------------------------------------------------
// 3. BASIC AGGREGATION
// -----------------------------------------------------------------------------

function sum(records, selector) {
    return records.reduce((total, record) => total + selector(record), 0);
}

function count(records) {
    return records.length;
}

function average(records, selector) {
    return records.length === 0 ? 0 : sum(records, selector) / records.length;
}

function minimum(records, selector) {
    if (records.length === 0) return 0;
    return Math.min(...records.map(selector));
}

function maximum(records, selector) {
    if (records.length === 0) return 0;
    return Math.max(...records.map(selector));
}

function distinctCount(records, selector) {
    return new Set(records.map(selector)).size;
}

console.log("=== BASIC AGGREGATION ===");
console.log("Orders:", count(sales));
console.log("Units:", sum(sales, r => r.units));
console.log("Net sales:", money(sum(sales, netSales)));
console.log("Average order:", money(average(sales, netSales)));
console.log("Minimum order:", money(minimum(sales, netSales)));
console.log("Maximum order:", money(maximum(sales, netSales)));
console.log("Distinct products:", distinctCount(sales, r => r.product));


// -----------------------------------------------------------------------------
// 4. GENERIC GROUPING
// -----------------------------------------------------------------------------

function groupBy(records, keySelector) {
    const groups = new Map();

    for (const record of records) {
        const key = keySelector(record);
        if (!groups.has(key)) {
            groups.set(key, []);
        }
        groups.get(key).push(record);
    }

    return groups;
}

function aggregateGroups(records, keySelector, valueSelector, aggregator) {
    const groups = groupBy(records, keySelector);
    const result = new Map();

    for (const [key, group] of groups) {
        result.set(key, aggregator(group.map(valueSelector)));
    }

    return result;
}

function mapToObject(map) {
    return Object.fromEntries(map.entries());
}

console.log("\n=== SALES BY REGION ===");

const regionalSales = aggregateGroups(
    sales,
    r => r.region,
    netSales,
    values => values.reduce((a, b) => a + b, 0)
);

console.log(mapToObject(regionalSales));


// -----------------------------------------------------------------------------
// 5. MULTIPLE AGGREGATORS
// -----------------------------------------------------------------------------

function aggregateGroupMetrics(records, keySelector) {
    const groups = groupBy(records, keySelector);
    const result = new Map();

    for (const [key, group] of groups) {
        result.set(key, {
            orders: group.length,
            units: sum(group, r => r.units),
            sales: sum(group, netSales),
            profit: sum(group, profit),
            averageOrder: average(group, netSales),
            averageMargin: average(group, marginPercent),
            distinctProducts: distinctCount(group, r => r.product)
        });
    }

    return result;
}

console.log("\n=== MULTI-METRIC REGION PIVOT ===");

for (const [region, metrics] of aggregateGroupMetrics(sales, r => r.region)) {
    console.log(region, {
        orders: metrics.orders,
        units: metrics.units,
        sales: money(metrics.sales),
        profit: money(metrics.profit),
        averageOrder: money(metrics.averageOrder),
        averageMargin: `${metrics.averageMargin.toFixed(2)}%`,
        distinctProducts: metrics.distinctProducts
    });
}


// -----------------------------------------------------------------------------
// 6. TWO-DIMENSIONAL PIVOT
// -----------------------------------------------------------------------------

function pivot2D(records, rowSelector, columnSelector, valueSelector) {
    const result = new Map();

    for (const record of records) {
        const row = rowSelector(record);
        const column = columnSelector(record);

        if (!result.has(row)) {
            result.set(row, new Map());
        }

        const rowMap = result.get(row);

        if (!rowMap.has(column)) {
            rowMap.set(column, 0);
        }

        rowMap.set(
            column,
            rowMap.get(column) + valueSelector(record)
        );
    }

    return result;
}

const regionCategorySales = pivot2D(
    sales,
    r => r.region,
    r => r.category,
    netSales
);

console.log("\n=== REGION X CATEGORY ===");

for (const [region, columns] of regionCategorySales) {
    console.log(region, mapToObject(columns));
}


// -----------------------------------------------------------------------------
// 7. FILTERS AND SLICERS
// -----------------------------------------------------------------------------

function filter(records, predicate) {
    return records.filter(predicate);
}

const onlineSales = filter(sales, r => r.channel === "Online");
const northSales = filter(sales, r => r.region === "North");
const highValueOrders = filter(sales, r => netSales(r) >= 1000);

console.log("\n=== FILTERED ANALYSIS ===");
console.log("Online sales:", money(sum(onlineSales, netSales)));
console.log("North sales:", money(sum(northSales, netSales)));
console.log("Orders >= 1000:", highValueOrders.length);


// -----------------------------------------------------------------------------
// 8. PERCENTAGE OF TOTAL
// -----------------------------------------------------------------------------

function percentageOfTotal(map) {
    const total = [...map.values()].reduce((a, b) => a + b, 0);
    const result = new Map();

    for (const [key, value] of map) {
        result.set(key, total === 0 ? 0 : value / total * 100);
    }

    return result;
}

console.log("\n=== PERCENTAGE OF TOTAL ===");

const categorySales = aggregateGroups(
    sales,
    r => r.category,
    netSales,
    values => values.reduce((a, b) => a + b, 0)
);

const categoryShare = percentageOfTotal(categorySales);

for (const [category, share] of categoryShare) {
    console.log(category, `${share.toFixed(2)}%`);
}


// -----------------------------------------------------------------------------
// 9. CALCULATED FIELDS
// -----------------------------------------------------------------------------

const calculatedOrders = sales.map(record => ({
    orderId: record.orderId,
    region: record.region,
    category: record.category,
    netSales: netSales(record),
    profit: profit(record),
    marginPercent: marginPercent(record),
    revenuePerUnit: record.units === 0
        ? 0
        : netSales(record) / record.units
}));

console.log("\n=== CALCULATED FIELDS ===");

for (const order of calculatedOrders.slice(0, 4)) {
    console.log(order.orderId, {
        sales: money(order.netSales),
        profit: money(order.profit),
        margin: `${order.marginPercent.toFixed(2)}%`,
        revenuePerUnit: money(order.revenuePerUnit)
    });
}


// -----------------------------------------------------------------------------
// 10. TIME GROUPING
// -----------------------------------------------------------------------------

function monthKey(record) {
    return record.orderDate.slice(0, 7);
}

function quarterKey(record) {
    const month = Number(record.orderDate.slice(5, 7));
    const quarter = Math.floor((month - 1) / 3) + 1;
    return `${record.orderDate.slice(0, 4)}-Q${quarter}`;
}

const monthlySales = aggregateGroups(
    sales,
    monthKey,
    netSales,
    values => values.reduce((a, b) => a + b, 0)
);

const quarterlySales = aggregateGroups(
    sales,
    quarterKey,
    netSales,
    values => values.reduce((a, b) => a + b, 0)
);

console.log("\n=== TIME PIVOTS ===");
console.log("Monthly:", mapToObject(monthlySales));
console.log("Quarterly:", mapToObject(quarterlySales));


// -----------------------------------------------------------------------------
// 11. RANKING
// -----------------------------------------------------------------------------

function rankMap(map) {
    return [...map.entries()]
        .sort((a, b) => b[1] - a[1])
        .map(([key, value], index) => ({
            rank: index + 1,
            key,
            value
        }));
}

const productSales = aggregateGroups(
    sales,
    r => r.product,
    netSales,
    values => values.reduce((a, b) => a + b, 0)
);

console.log("\n=== PRODUCT RANKING ===");

for (const item of rankMap(productSales)) {
    console.log(
        `${item.rank}. ${item.key}: ${money(item.value)}`
    );
}


// -----------------------------------------------------------------------------
// 12. PARETO ANALYSIS
// -----------------------------------------------------------------------------

function pareto(map) {
    const ranked = rankMap(map);
    const total = ranked.reduce((sumValue, item) => sumValue + item.value, 0);
    let cumulative = 0;

    return ranked.map(item => {
        cumulative += item.value;

        return {
            ...item,
            sharePercent: total === 0 ? 0 : item.value / total * 100,
            cumulativePercent: total === 0 ? 0 : cumulative / total * 100
        };
    });
}

console.log("\n=== PARETO ANALYSIS ===");

for (const item of pareto(productSales)) {
    console.log(
        item.key,
        `share=${item.sharePercent.toFixed(2)}%`,
        `cumulative=${item.cumulativePercent.toFixed(2)}%`
    );
}


// -----------------------------------------------------------------------------
// 13. DRILL-DOWN
// -----------------------------------------------------------------------------

function drillDown(records, selector, selectedValue) {
    return records.filter(record => selector(record) === selectedValue);
}

console.log("\n=== DRILL-DOWN: NORTH ===");

for (const record of drillDown(sales, r => r.region, "North")) {
    console.log(
        record.orderId,
        record.product,
        money(netSales(record))
    );
}


// -----------------------------------------------------------------------------
// 14. VALIDATION
// -----------------------------------------------------------------------------

function validateRecord(record) {
    const errors = [];

    if (!record.orderId) {
        errors.push("Missing order ID.");
    }

    if (!Number.isInteger(record.units) || record.units <= 0) {
        errors.push("Units must be a positive integer.");
    }

    if (!Number.isFinite(record.unitPrice) || record.unitPrice < 0) {
        errors.push("Unit price must be non-negative.");
    }

    if (!Number.isFinite(record.discount) ||
        record.discount < 0 ||
        record.discount > 1) {
        errors.push("Discount must be between 0 and 1.");
    }

    if (!Number.isFinite(record.costPerUnit) || record.costPerUnit < 0) {
        errors.push("Cost per unit must be non-negative.");
    }

    if (Number.isNaN(Date.parse(record.orderDate))) {
        errors.push("Invalid order date.");
    }

    return errors;
}

function validateDataset(records) {
    const errors = [];
    const orderIds = new Set();

    records.forEach((record, index) => {
        const recordErrors = validateRecord(record);

        if (recordErrors.length > 0) {
            errors.push({
                index,
                orderId: record.orderId,
                errors: recordErrors
            });
        }

        if (orderIds.has(record.orderId)) {
            errors.push({
                index,
                orderId: record.orderId,
                errors: ["Duplicate order ID."]
            });
        }

        orderIds.add(record.orderId);
    });

    return errors;
}

console.log("\n=== VALIDATION ===");
console.log(validateDataset(sales).length === 0
    ? "Dataset validation passed."
    : validateDataset(sales));


// -----------------------------------------------------------------------------
// 15. CONDITIONAL AGGREGATION
// -----------------------------------------------------------------------------

function conditionalSum(records, predicate, valueSelector) {
    return sum(
        records.filter(predicate),
        valueSelector
    );
}

const profitableOrderProfit = conditionalSum(
    sales,
    r => profit(r) > 500,
    profit
);

const onlineHighValueSales = conditionalSum(
    sales,
    r => r.channel === "Online" && netSales(r) >= 1000,
    netSales
);

console.log("\n=== CONDITIONAL AGGREGATION ===");
console.log("Profit from orders with profit > 500:", money(profitableOrderProfit));
console.log("Online sales from orders >= 1000:", money(onlineHighValueSales));


// -----------------------------------------------------------------------------
// 16. WEIGHTED AVERAGE
// -----------------------------------------------------------------------------

function weightedAverage(records, valueSelector, weightSelector) {
    let weightedTotal = 0;
    let totalWeight = 0;

    for (const record of records) {
        const weight = weightSelector(record);
        weightedTotal += valueSelector(record) * weight;
        totalWeight += weight;
    }

    return totalWeight === 0 ? 0 : weightedTotal / totalWeight;
}

const averageSellingPrice = weightedAverage(
    sales,
    r => r.unitPrice * (1 - r.discount),
    r => r.units
);

console.log("\n=== WEIGHTED AVERAGE ===");
console.log("Weighted average selling price:", money(averageSellingPrice));


// -----------------------------------------------------------------------------
// 17. SINGLE-PASS MULTI-METRIC AGGREGATION
// -----------------------------------------------------------------------------

function efficientRegionAggregation(records) {
    const result = new Map();

    for (const record of records) {
        if (!result.has(record.region)) {
            result.set(record.region, {
                orders: 0,
                units: 0,
                sales: 0,
                profit: 0
            });
        }

        const bucket = result.get(record.region);

        bucket.orders += 1;
        bucket.units += record.units;
        bucket.sales += netSales(record);
        bucket.profit += profit(record);
    }

    return result;
}

console.log("\n=== SINGLE-PASS AGGREGATION ===");

for (const [region, metrics] of efficientRegionAggregation(sales)) {
    console.log(region, {
        ...metrics,
        sales: money(metrics.sales),
        profit: money(metrics.profit)
    });
}


// -----------------------------------------------------------------------------
// 18. ASYNCHRONOUS DATA PIPELINE
// -----------------------------------------------------------------------------

function loadSalesAsync() {
    // In production, this function could fetch CSV, JSON, or an API.
    // The demonstration remains self-contained by resolving local data.
    return Promise.resolve(sales);
}

async function runAsyncAnalysis() {
    const records = await loadSalesAsync();

    const result = aggregateGroups(
        records,
        r => r.category,
        netSales,
        values => values.reduce((a, b) => a + b, 0)
    );

    return mapToObject(result);
}

runAsyncAnalysis().then(result => {
    console.log("\n=== ASYNC PIPELINE ===");
    console.log(result);
});


// -----------------------------------------------------------------------------
// 19. SIMPLE HTML TABLE GENERATION
// -----------------------------------------------------------------------------

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function pivotToHtmlTable(pivotMap) {
    const columns = new Set();

    for (const row of pivotMap.values()) {
        for (const column of row.keys()) {
            columns.add(column);
        }
    }

    const sortedColumns = [...columns].sort();

    let html = "<table><thead><tr><th>Row</th>";

    for (const column of sortedColumns) {
        html += `<th>${escapeHtml(column)}</th>`;
    }

    html += "</tr></thead><tbody>";

    for (const [rowKey, rowValues] of pivotMap) {
        html += `<tr><th>${escapeHtml(rowKey)}</th>`;

        for (const column of sortedColumns) {
            const value = rowValues.get(column) ?? 0;
            html += `<td>${money(value)}</td>`;
        }

        html += "</tr>";
    }

    html += "</tbody></table>";

    return html;
}

console.log("\n=== HTML PIVOT TABLE REPRESENTATION ===");
console.log(pivotToHtmlTable(regionCategorySales));


// -----------------------------------------------------------------------------
// 20. TESTS
// -----------------------------------------------------------------------------

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Test failed: ${message}`);
    }
}

function runTests() {
    assert(sales.length === 12, "Dataset should contain 12 records.");

    assert(
        sum(sales, r => r.units) > 0,
        "Units should be positive."
    );

    assert(
        distinctCount(sales, r => r.region) === 4,
        "There should be four regions."
    );

    assert(
        Math.abs(
            [...percentageOfTotal(productSales).values()]
                .reduce((a, b) => a + b, 0) - 100
        ) < 0.000001,
        "Percentages should total 100."
    );

    assert(
        validateDataset(sales).length === 0,
        "Sample data should pass validation."
    );

    assert(
        filter(sales, r => r.region === "North")
            .every(r => r.region === "North"),
        "Filtering should preserve the condition."
    );

    assert(
        weightedAverage(sales, r => r.unitPrice, r => r.units) > 0,
        "Weighted average should be positive."
    );

    console.log("All JavaScript tests passed.");
}

runTests();


// -----------------------------------------------------------------------------
// 21. ANALYTICAL NOTES
// -----------------------------------------------------------------------------

console.log("\n=== PIVOT DESIGN PRINCIPLES ===");
console.log("Dimensions define grouping.");
console.log("Measures define what is calculated.");
console.log("Aggregation determines how values are summarized.");
console.log("Filters change the population being analyzed.");
console.log("Calculated fields create derived measures.");
console.log("Two-dimensional pivots expose relationships between dimensions.");
console.log("Drill-down preserves the connection between summaries and source records.");
console.log("Single-pass aggregation can reduce repeated work on large datasets.");
console.log("Weighted averages are often more meaningful than simple averages.");
console.log("Input validation is required before relying on analytical results.");
