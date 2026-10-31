"use strict";

const fs = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class SalesRecord {
    constructor(data) {
        Object.assign(this, data);
        this.orderDate = new Date(`${data.orderDate}T00:00:00Z`);
        this.validate();
    }

    validate() {
        if (!this.orderId || !this.orderId.trim()) {
            throw new ValidationError("Order ID is required.");
        }
        if (!Number.isInteger(this.units) || this.units <= 0) {
            throw new ValidationError(`${this.orderId}: units must be positive.`);
        }
        if (this.unitPrice < 0 || this.costPerUnit < 0) {
            throw new ValidationError(`${this.orderId}: prices cannot be negative.`);
        }
        if (this.discountRate < 0 || this.discountRate > 1) {
            throw new ValidationError(`${this.orderId}: invalid discount rate.`);
        }
        if (this.costPerUnit > this.unitPrice) {
            throw new ValidationError(`${this.orderId}: cost exceeds list price.`);
        }
        if (Number.isNaN(this.orderDate.getTime())) {
            throw new ValidationError(`${this.orderId}: invalid date.`);
        }
    }

    get grossSales() {
        return this.units * this.unitPrice;
    }

    get netSales() {
        return this.grossSales * (1 - this.discountRate);
    }

    get profit() {
        return this.netSales - this.units * this.costPerUnit;
    }

    get margin() {
        return this.netSales === 0 ? 0 : this.profit / this.netSales;
    }
}

function createRecords() {
    const data = [
        ["O1001", "2026-01-05", "North", "Asha", "Acme", "Analytics", 12, 850, .05, 510],
        ["O1002", "2026-01-09", "South", "Ravi", "Beta", "Automation", 8, 1200, .10, 720],
        ["O1003", "2026-01-15", "North", "Asha", "Delta", "Analytics", 5, 850, 0, 510],
        ["O1004", "2026-02-03", "West", "Neha", "Acme", "Security", 15, 700, .08, 420],
        ["O1005", "2026-02-11", "South", "Ravi", "Gamma", "Analytics", 20, 850, .12, 510],
        ["O1006", "2026-02-19", "West", "Neha", "Delta", "Automation", 7, 1200, .05, 720],
        ["O1007", "2026-03-02", "North", "Asha", "Beta", "Security", 10, 700, .03, 420],
        ["O1008", "2026-03-12", "South", "Ravi", "Acme", "Analytics", 16, 850, .07, 510],
        ["O1009", "2026-03-20", "West", "Neha", "Gamma", "Security", 6, 700, .15, 420],
        ["O1010", "2026-03-25", "North", "Asha", "Delta", "Automation", 11, 1200, .06, 720]
    ];

    return data.map(
        ([orderId, orderDate, region, salesperson, customer, product,
          units, unitPrice, discountRate, costPerUnit]) =>
            new SalesRecord({
                orderId,
                orderDate,
                region,
                salesperson,
                customer,
                product,
                units,
                unitPrice,
                discountRate,
                costPerUnit
            })
    );
}

function groupBy(records, key) {
    const result = new Map();

    for (const record of records) {
        const value = key(record);
        if (!result.has(value)) {
            result.set(value, []);
        }
        result.get(value).push(record);
    }

    return result;
}

function aggregate(records, key, value) {
    const result = new Map();

    for (const record of records) {
        const group = key(record);
        result.set(group, (result.get(group) || 0) + value(record));
    }

    return result;
}

function customerSegments(records) {
    const groups = groupBy(records, r => r.customer);
    const result = new Map();

    for (const [customer, rows] of groups) {
        const revenue = rows.reduce((sum, r) => sum + r.netSales, 0);
        const profit = rows.reduce((sum, r) => sum + r.profit, 0);
        const margin = revenue === 0 ? 0 : profit / revenue;

        let segment;
        if (revenue >= 15000 && margin >= 0.30) {
            segment = "High Value";
        } else if (revenue >= 10000) {
            segment = "Growth";
        } else if (margin < 0.25) {
            segment = "At Risk";
        } else {
            segment = "Standard";
        }

        result.set(customer, segment);
    }

    return result;
}

function correlation(x, y) {
    if (x.length !== y.length || x.length < 2) {
        throw new RangeError("Correlation requires equal arrays of length >= 2.");
    }

    const xMean = x.reduce((a, b) => a + b, 0) / x.length;
    const yMean = y.reduce((a, b) => a + b, 0) / y.length;

    let numerator = 0;
    let xVariance = 0;
    let yVariance = 0;

    for (let i = 0; i < x.length; i++) {
        const dx = x[i] - xMean;
        const dy = y[i] - yMean;
        numerator += dx * dy;
        xVariance += dx * dx;
        yVariance += dy * dy;
    }

    const denominator = Math.sqrt(xVariance * yVariance);
    return denominator === 0 ? 0 : numerator / denominator;
}

function buildReport(records) {
    const sales = records.reduce((sum, r) => sum + r.netSales, 0);
    const profit = records.reduce((sum, r) => sum + r.profit, 0);

    const byRegion = aggregate(records, r => r.region, r => r.netSales);
    const byProduct = aggregate(records, r => r.product, r => r.profit);

    const byMonth = aggregate(
        records,
        r => r.orderDate.toISOString().slice(0, 7),
        r => r.netSales
    );

    const report = {
        orderCount: records.length,
        totalUnits: records.reduce((sum, r) => sum + r.units, 0),
        totalSales: Number(sales.toFixed(2)),
        totalProfit: Number(profit.toFixed(2)),
        margin: Number((profit / sales).toFixed(4)),
        salesByRegion: Object.fromEntries(byRegion),
        profitByProduct: Object.fromEntries(byProduct),
        salesByMonth: Object.fromEntries(byMonth),
        customerSegments: Object.fromEntries(customerSegments(records))
    };

    const units = records.map(r => r.units);
    const orderValues = records.map(r => r.netSales);

    report.unitsSalesCorrelation = Number(
        correlation(units, orderValues).toFixed(4)
    );

    return report;
}

async function exportReport(records, report) {
    const directory = await fs.mkdtemp(
        path.join(os.tmpdir(), "business-analytics-")
    );

    const csv = [
        "order_id,order_date,region,customer,product,units,net_sales,profit,margin",
        ...records.map(r =>
            [
                r.orderId,
                r.orderDate.toISOString().slice(0, 10),
                r.region,
                r.customer,
                r.product,
                r.units,
                r.netSales.toFixed(2),
                r.profit.toFixed(2),
                r.margin.toFixed(4)
            ].join(",")
        )
    ].join("\n");

    const csvPath = path.join(directory, "sales_analysis.csv");
    const jsonPath = path.join(directory, "analytics_report.json");

    await fs.writeFile(csvPath, csv, "utf8");
    await fs.writeFile(jsonPath, JSON.stringify(report, null, 2), "utf8");

    return { directory, csvPath, jsonPath };
}

async function main() {
    const records = createRecords();
    const report = buildReport(records);

    if (report.orderCount !== 10) {
        throw new Error("Unexpected record count.");
    }

    if (report.totalSales <= 0 || report.totalProfit <= 0) {
        throw new Error("Financial validation failed.");
    }

    console.log("BUSINESS ANALYTICS REPORT");
    console.log("=========================");
    console.log(`Orders:        ${report.orderCount}`);
    console.log(`Units:         ${report.totalUnits}`);
    console.log(`Net sales:     $${report.totalSales.toLocaleString()}`);
    console.log(`Profit:        $${report.totalProfit.toLocaleString()}`);
    console.log(`Margin:        ${(report.margin * 100).toFixed(2)}%`);
    console.log(`Units/sales r: ${report.unitsSalesCorrelation}`);

    console.log("\nSales by region");
    for (const [region, value] of Object.entries(report.salesByRegion)) {
        console.log(`  ${region}: $${value.toFixed(2)}`);
    }

    console.log("\nProfit by product");
    for (const [product, value] of Object.entries(report.profitByProduct)) {
        console.log(`  ${product}: $${value.toFixed(2)}`);
    }

    console.log("\nCustomer segments");
    for (const [customer, segment] of Object.entries(report.customerSegments)) {
        console.log(`  ${customer}: ${segment}`);
    }

    const exported = await exportReport(records, report);
    console.log(`\nCSV:  ${exported.csvPath}`);
    console.log(`JSON: ${exported.jsonPath}`);
}

main().catch(error => {
    console.error(`Analytics failure: ${error.message}`);
    process.exitCode = 1;
});
