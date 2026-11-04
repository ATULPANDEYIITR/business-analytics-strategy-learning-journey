"use strict";

/*
 * Data Aggregation Engine
 *
 * Demonstrates:
 * - Map-based grouping.
 * - Reducer-based aggregation.
 * - Conditional aggregation.
 * - Multi-dimensional grouping.
 * - Pivot and unpivot.
 * - Incremental event processing.
 * - Aggregation snapshots.
 * - Input validation and safe serialization.
 *
 * Runtime: Node.js 18+
 */

const fs = require("node:fs/promises");

class AggregationError extends Error {
    constructor(message) {
        super(message);
        this.name = "AggregationError";
    }
}

class SchemaValidator {
    static validate(record) {
        if (!record || typeof record !== "object" || Array.isArray(record)) {
            throw new AggregationError("Record must be an object.");
        }

        const required = [
            "transactionId",
            "region",
            "category",
            "product",
            "quantity",
            "unitPrice",
            "status",
        ];

        for (const field of required) {
            if (!(field in record)) {
                throw new AggregationError(`Missing field: ${field}`);
            }
        }

        for (const field of [
            "transactionId",
            "region",
            "category",
            "product",
            "status",
        ]) {
            if (
                typeof record[field] !== "string" ||
                record[field].trim() === ""
            ) {
                throw new AggregationError(
                    `${field} must be a nonempty string.`
                );
            }
        }

        if (
            !Number.isSafeInteger(record.quantity) ||
            record.quantity <= 0
        ) {
            throw new AggregationError(
                "Quantity must be a positive safe integer."
            );
        }

        if (
            typeof record.unitPrice !== "number" ||
            !Number.isFinite(record.unitPrice) ||
            record.unitPrice < 0
        ) {
            throw new AggregationError(
                "Unit price must be a finite nonnegative number."
            );
        }

        if (!Number.isFinite(record.unitPrice * 100) ||
            Math.abs(record.unitPrice * 100 -
                Math.round(record.unitPrice * 100)) > 1e-7) {
            throw new AggregationError(
                "Unit price cannot have more than two decimal places."
            );
        }

        if (!["completed", "pending", "cancelled"].includes(record.status)) {
            throw new AggregationError("Invalid transaction status.");
        }

        if (
            typeof record.transactionDate !== "string" ||
            !/^\d{4}-\d{2}-\d{2}$/.test(record.transactionDate)
        ) {
            throw new AggregationError("Invalid transaction date.");
        }

        const parsedDate = new Date(
            `${record.transactionDate}T00:00:00.000Z`
        );

        if (
            Number.isNaN(parsedDate.getTime()) ||
            parsedDate.toISOString().slice(0, 10) !== record.transactionDate
        ) {
            throw new AggregationError("Invalid calendar date.");
        }

        return Object.freeze({
            ...record,
            transactionId: record.transactionId.trim(),
            region: record.region.trim(),
            category: record.category.trim(),
            product: record.product.trim(),
        });
    }
}

class Money {
    /*
     * Integer minor units avoid binary floating-point arithmetic
     * for financial aggregation.
     */
    static toCents(amount) {
        return Math.round(amount * 100);
    }

    static format(cents) {
        return (cents / 100).toFixed(2);
    }
}

class GroupingEngine {
    static group(records, dimensions) {
        if (!Array.isArray(dimensions) || dimensions.length === 0) {
            throw new AggregationError(
                "At least one grouping dimension is required."
            );
        }

        const groups = new Map();

        for (const record of records) {
            const values = dimensions.map((field) => {
                if (!(field in record)) {
                    throw new AggregationError(
                        `Unknown grouping field: ${field}`
                    );
                }
                return record[field];
            });

            // JSON encoding preserves multi-field key boundaries.
            const key = JSON.stringify(values);

            if (!groups.has(key)) {
                groups.set(key, {
                    dimensions: values,
                    count: 0,
                    quantity: 0,
                    revenueCents: 0,
                    minimumCents: Infinity,
                    maximumCents: -Infinity,
                    products: new Set(),
                });
            }

            const state = groups.get(key);
            const revenue = Money.toCents(
                record.quantity * record.unitPrice
            );

            state.count++;
            state.quantity += record.quantity;
            state.revenueCents += revenue;
            state.minimumCents = Math.min(
                state.minimumCents,
                revenue
            );
            state.maximumCents = Math.max(
                state.maximumCents,
                revenue
            );
            state.products.add(record.product);
        }

        return groups;
    }

    static summarize(groups) {
        return [...groups.values()].map((group) => ({
            dimensions: group.dimensions,
            count: group.count,
            quantity: group.quantity,
            revenue: Money.format(group.revenueCents),
            averageRevenue: Money.format(
                Math.round(group.revenueCents / group.count)
            ),
            minimumRevenue: Money.format(group.minimumCents),
            maximumRevenue: Money.format(group.maximumCents),
            distinctProducts: group.products.size,
        }));
    }

    static conditional(records) {
        const result = new Map();

        for (const status of ["completed", "pending", "cancelled"]) {
            result.set(status, {
                count: 0,
                revenueCents: 0,
            });
        }

        for (const record of records) {
            const state = result.get(record.status);
            state.count++;
            state.revenueCents += Money.toCents(
                record.quantity * record.unitPrice
            );
        }

        return Object.fromEntries(
            [...result.entries()].map(([status, state]) => [
                status,
                {
                    count: state.count,
                    revenue: Money.format(state.revenueCents),
                },
            ])
        );
    }

    static pivot(
        records,
        rowField,
        columnField,
        valueFunction,
        operation = "sum"
    ) {
        const allowed = new Set([
            "sum",
            "count",
            "average",
            "minimum",
            "maximum",
            "distinct_count",
        ]);

        if (!allowed.has(operation)) {
            throw new AggregationError("Unsupported pivot operation.");
        }

        const groups = new Map();

        for (const record of records) {
            if (!(rowField in record) || !(columnField in record)) {
                throw new AggregationError("Unknown pivot dimension.");
            }

            const row = String(record[rowField]);
            const column = String(record[columnField]);
            const value = valueFunction(record);

            if (
                !Number.isFinite(value) &&
                operation !== "distinct_count"
            ) {
                throw new AggregationError("Pivot value must be finite.");
            }

            const key = JSON.stringify([row, column]);

            if (!groups.has(key)) {
                groups.set(key, {
                    row,
                    column,
                    values: [],
                });
            }

            groups.get(key).values.push(value);
        }

        const output = {};

        for (const group of groups.values()) {
            const values = group.values;
            let result;

            switch (operation) {
                case "sum":
                    result = values.reduce((a, b) => a + b, 0);
                    break;
                case "count":
                    result = values.length;
                    break;
                case "average":
                    result = values.reduce((a, b) => a + b, 0) /
                        values.length;
                    break;
                case "minimum":
                    result = Math.min(...values);
                    break;
                case "maximum":
                    result = Math.max(...values);
                    break;
                case "distinct_count":
                    result = new Set(values).size;
                    break;
            }

            output[group.row] ??= {};
            output[group.row][group.column] = result;
        }

        return output;
    }

    static unpivot(table) {
        const result = [];

        for (const [row, columns] of Object.entries(table)) {
            for (const [column, value] of Object.entries(columns)) {
                result.push({ row, column, value });
            }
        }

        return result;
    }
}

class AggregationStream {
    constructor(dimensions) {
        this.dimensions = dimensions;
        this.state = new Map();
        this.processedIds = new Set();
        this.version = 0;
    }

    process(rawRecord) {
        const record = SchemaValidator.validate(rawRecord);

        if (this.processedIds.has(record.transactionId)) {
            throw new AggregationError(
                `Duplicate event: ${record.transactionId}`
            );
        }

        const key = JSON.stringify(
            this.dimensions.map((field) => record[field])
        );

        if (!this.state.has(key)) {
            this.state.set(key, {
                dimensions: this.dimensions.map(
                    (field) => record[field]
                ),
                count: 0,
                quantity: 0,
                revenueCents: 0,
            });
        }

        const current = this.state.get(key);
        const revenue = Money.toCents(
            record.quantity * record.unitPrice
        );

        current.count++;
        current.quantity += record.quantity;
        current.revenueCents += revenue;

        this.processedIds.add(record.transactionId);
        this.version++;
    }

    snapshot() {
        return {
            version: this.version,
            processedEvents: this.processedIds.size,
            groups: [...this.state.values()].map((item) => ({
                ...item,
                revenue: Money.format(item.revenueCents),
            })),
        };
    }
}

class AggregationPipeline {
    constructor(records) {
        this.records = records.map(
            (record) => SchemaValidator.validate(record)
        );

        const identifiers = new Set();

        for (const record of this.records) {
            if (identifiers.has(record.transactionId)) {
                throw new AggregationError(
                    "Transaction identifiers must be unique."
                );
            }
            identifiers.add(record.transactionId);
        }
    }

    execute() {
        const regional = GroupingEngine.summarize(
            GroupingEngine.group(this.records, ["region"])
        );

        const regionalCategory = GroupingEngine.summarize(
            GroupingEngine.group(
                this.records,
                ["region", "category"]
            )
        );

        const pivot = GroupingEngine.pivot(
            this.records,
            "region",
            "category",
            (record) => Money.toCents(
                record.quantity * record.unitPrice
            ),
            "sum"
        );

        return {
            totalRecords: this.records.length,
            regional,
            regionalCategory,
            conditional: GroupingEngine.conditional(this.records),
            pivot,
            normalizedPivot: GroupingEngine.unpivot(pivot),
        };
    }
}

function createSampleData() {
    return [
        ["T001", "North", "Electronics", "Laptop", 2, 65000, "completed"],
        ["T002", "North", "Electronics", "Phone", 3, 25000, "completed"],
        ["T003", "South", "Furniture", "Chair", 5, 3000, "completed"],
        ["T004", "South", "Electronics", "Laptop", 1, 65000, "pending"],
        ["T005", "East", "Furniture", "Table", 2, 12000, "completed"],
        ["T006", "East", "Electronics", "Phone", 4, 25000, "cancelled"],
        ["T007", "West", "Furniture", "Chair", 3, 3000, "completed"],
        ["T008", "West", "Electronics", "Laptop", 2, 65000, "completed"],
        ["T009", "North", "Furniture", "Table", 1, 12000, "pending"],
        ["T010", "South", "Furniture", "Chair", 2, 3000, "completed"],
    ].map((row, index) => ({
        transactionId: row[0],
        region: row[1],
        category: row[2],
        product: row[3],
        quantity: row[4],
        unitPrice: row[5],
        status: row[6],
        transactionDate: `2026-10-${String(index + 1).padStart(2, "0")}`,
    }));
}

async function main() {
    const records = createSampleData();
    const pipeline = new AggregationPipeline(records);
    const report = pipeline.execute();

    console.log("\n1. Regional aggregation");
    console.table(report.regional);

    console.log("\n2. Region and category aggregation");
    console.table(report.regionalCategory);

    console.log("\n3. Conditional aggregation");
    console.log(report.conditional);

    console.log("\n4. Pivot table");
    console.log(report.pivot);

    console.log("\n5. Unpivoted table");
    console.table(report.normalizedPivot);

    console.log("\n6. Event-driven aggregation");

    const stream = new AggregationStream(["region"]);

    for (const record of records) {
        stream.process(record);
    }

    console.log(stream.snapshot());

    try {
        stream.process(records[0]);
    } catch (error) {
        console.log("Duplicate rejected:", error.message);
    }

    console.log("\n7. Data reconciliation");

    const total = records.reduce(
        (sum, record) => sum + Money.toCents(
            record.quantity * record.unitPrice
        ),
        0
    );

    const groupedTotal = report.regional.reduce(
        (sum, group) => sum + Money.toCents(
            Number(group.revenue)
        ),
        0
    );

    if (total !== groupedTotal) {
        throw new AggregationError("Revenue reconciliation failed.");
    }

    if (report.totalRecords !== 10) {
        throw new AggregationError("Unexpected transaction count.");
    }

    console.log("Revenue reconciliation passed.");

    const outputPath = "aggregation-report.json";

    await fs.writeFile(
        outputPath,
        JSON.stringify(report, null, 2),
        { encoding: "utf8", mode: 0o600 }
    );

    console.log(`Report written to ${outputPath}`);

    console.log("\n8. Invalid input handling");

    try {
        SchemaValidator.validate({
            transactionId: "INVALID",
            region: "North",
            category: "Electronics",
            product: "Laptop",
            quantity: -2,
            unitPrice: 500,
            status: "completed",
            transactionDate: "2026-10-01",
        });
    } catch (error) {
        console.log(error.message);
    }
}

main().catch((error) => {
    console.error("Aggregation pipeline failed:", error.message);
    process.exitCode = 1;
});
