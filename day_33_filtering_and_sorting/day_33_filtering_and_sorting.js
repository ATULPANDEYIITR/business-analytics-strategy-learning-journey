/**
 * Filtering & Sorting Business Data
 *
 * A Node.js-compatible implementation of business-data query behavior.
 *
 * The program uses JavaScript-specific techniques to model:
 * - WHERE-style predicates
 * - composable predicate functions
 * - null-safe comparisons
 * - ORDER BY with independent sort directions
 * - stable deterministic ordering
 * - query objects
 * - event-driven query lifecycle
 * - asynchronous business-data retrieval
 * - validation and error handling
 * - pagination
 * - operational reporting
 *
 * Run with:
 *   node filtering_sorting.js
 */

"use strict";

// -----------------------------------------------------------------------------
// Business data
// -----------------------------------------------------------------------------

const customers = [
    {
        customerId: 101,
        name: "Apex Retail",
        region: "North",
        segment: "Enterprise",
        annualRevenue: 18500000,
        creditLimit: 2000000,
        active: true,
        signupDate: "2021-04-12"
    },
    {
        customerId: 102,
        name: "Blue Horizon",
        region: "West",
        segment: "Mid-Market",
        annualRevenue: 7250000,
        creditLimit: 750000,
        active: true,
        signupDate: "2022-08-19"
    },
    {
        customerId: 103,
        name: "Cedar Foods",
        region: "South",
        segment: "SMB",
        annualRevenue: 1850000,
        creditLimit: 200000,
        active: true,
        signupDate: "2023-02-05"
    },
    {
        customerId: 104,
        name: "Delta Manufacturing",
        region: "East",
        segment: "Enterprise",
        annualRevenue: 12400000,
        creditLimit: 1500000,
        active: false,
        signupDate: "2020-11-23"
    },
    {
        customerId: 105,
        name: "Evergreen Health",
        region: "North",
        segment: "Mid-Market",
        annualRevenue: null,
        creditLimit: 600000,
        active: true,
        signupDate: "2024-01-14"
    },
    {
        customerId: 106,
        name: "Frontier Logistics",
        region: "West",
        segment: "Enterprise",
        annualRevenue: 21300000,
        creditLimit: 2500000,
        active: true,
        signupDate: "2019-06-30"
    },
    {
        customerId: 107,
        name: "Granite Systems",
        region: "East",
        segment: "SMB",
        annualRevenue: 950000,
        creditLimit: null,
        active: true,
        signupDate: "2024-05-02"
    },
    {
        customerId: 108,
        name: "Harbor Hotels",
        region: "South",
        segment: "Mid-Market",
        annualRevenue: 5900000,
        creditLimit: 500000,
        active: false,
        signupDate: "2022-03-17"
    }
];

const orders = [
    { orderId: 5001, customerId: 101, salesRep: "Anita", region: "North", productCategory: "Cloud", orderValue: 245000, status: "Shipped", orderDate: "2026-09-03", priority: "High", discountRate: 0.05 },
    { orderId: 5002, customerId: 102, salesRep: "Rahul", region: "West", productCategory: "Security", orderValue: 185000, status: "Pending", orderDate: "2026-09-04", priority: "Medium", discountRate: 0.02 },
    { orderId: 5003, customerId: 103, salesRep: "Meera", region: "South", productCategory: "Analytics", orderValue: 72000, status: "Shipped", orderDate: "2026-09-05", priority: "Low", discountRate: 0.00 },
    { orderId: 5004, customerId: 104, salesRep: "Vikram", region: "East", productCategory: "Cloud", orderValue: 310000, status: "Cancelled", orderDate: "2026-09-06", priority: "High", discountRate: 0.10 },
    { orderId: 5005, customerId: 105, salesRep: "Anita", region: "North", productCategory: "Security", orderValue: 126000, status: "Processing", orderDate: "2026-09-08", priority: "High", discountRate: 0.03 },
    { orderId: 5006, customerId: 106, salesRep: "Rahul", region: "West", productCategory: "Cloud", orderValue: 455000, status: "Shipped", orderDate: "2026-09-09", priority: "High", discountRate: 0.07 },
    { orderId: 5007, customerId: 107, salesRep: "Vikram", region: "East", productCategory: "Analytics", orderValue: 64000, status: "Pending", orderDate: "2026-09-10", priority: "Low", discountRate: 0.00 },
    { orderId: 5008, customerId: 108, salesRep: "Meera", region: "South", productCategory: "Security", orderValue: 198000, status: "Shipped", orderDate: "2026-09-11", priority: "Medium", discountRate: 0.04 },
    { orderId: 5009, customerId: 101, salesRep: "Anita", region: "North", productCategory: "Analytics", orderValue: 175000, status: "Processing", orderDate: "2026-09-12", priority: "Medium", discountRate: 0.02 },
    { orderId: 5010, customerId: 102, salesRep: "Rahul", region: "West", productCategory: "Cloud", orderValue: 225000, status: "Shipped", orderDate: "2026-09-13", priority: "High", discountRate: 0.05 },
    { orderId: 5011, customerId: 103, salesRep: "Meera", region: "South", productCategory: "Security", orderValue: 91000, status: "Pending", orderDate: "2026-09-15", priority: "Low", discountRate: 0.01 },
    { orderId: 5012, customerId: 106, salesRep: "Rahul", region: "West", productCategory: "Security", orderValue: 275000, status: "Processing", orderDate: "2026-09-16", priority: "High", discountRate: 0.06 }
];


// -----------------------------------------------------------------------------
// Presentation helpers
// -----------------------------------------------------------------------------

function printTitle(title) {
    console.log(`\n${"=".repeat(78)}\n${title}\n${"=".repeat(78)}`);
}

function printRows(rows, fields) {
    if (rows.length === 0) {
        console.log("(no rows)");
        return;
    }

    const normalized = rows.map(row =>
        fields.map(field => {
            const value = row[field];
            return value === null || value === undefined ? "" : String(value);
        })
    );

    const widths = fields.map((field, index) =>
        Math.max(
            field.length,
            ...normalized.map(row => row[index].length)
        )
    );

    console.log(
        fields.map((field, index) => field.padEnd(widths[index])).join(" | ")
    );

    console.log(
        widths.map(width => "-".repeat(width)).join("-+-")
    );

    normalized.forEach(row => {
        console.log(
            row.map((value, index) => value.padEnd(widths[index])).join(" | ")
        );
    });
}


// -----------------------------------------------------------------------------
// WHERE-style predicate functions
// -----------------------------------------------------------------------------

const equals = (field, expected) => row => row[field] === expected;

const greaterThan = (field, threshold) => row =>
    row[field] !== null &&
    row[field] !== undefined &&
    row[field] > threshold;

const greaterOrEqual = (field, threshold) => row =>
    row[field] !== null &&
    row[field] !== undefined &&
    row[field] >= threshold;

const lessThan = (field, threshold) => row =>
    row[field] !== null &&
    row[field] !== undefined &&
    row[field] < threshold;

const contains = (field, fragment) => {
    const normalizedFragment = fragment.toLocaleLowerCase();

    return row => {
        const value = row[field];

        return value !== null &&
            value !== undefined &&
            String(value).toLocaleLowerCase().includes(normalizedFragment);
    };
};

const inValues = (field, allowedValues) => row =>
    allowedValues.has(row[field]);

const isNull = field => row => row[field] === null || row[field] === undefined;

const isNotNull = field => row =>
    row[field] !== null && row[field] !== undefined;

const allOf = (...predicates) => row =>
    predicates.every(predicate => predicate(row));

const anyOf = (...predicates) => row =>
    predicates.some(predicate => predicate(row));

const negate = predicate => row => !predicate(row);


// -----------------------------------------------------------------------------
// Filtering
// -----------------------------------------------------------------------------

function where(rows, predicate) {
    return rows.filter(predicate);
}


// -----------------------------------------------------------------------------
// Null-safe ORDER BY
// -----------------------------------------------------------------------------

function compareValues(left, right, descending, nullsLast = true) {
    const leftNull = left === null || left === undefined;
    const rightNull = right === null || right === undefined;

    if (leftNull && rightNull) {
        return 0;
    }

    if (leftNull) {
        return nullsLast ? 1 : -1;
    }

    if (rightNull) {
        return nullsLast ? -1 : 1;
    }

    let comparison = 0;

    if (left < right) {
        comparison = -1;
    } else if (left > right) {
        comparison = 1;
    }

    return descending ? -comparison : comparison;
}

function orderBy(rows, specifications) {
    // Modern ECMAScript specifies stable Array.prototype.sort. The final
    // orderId tie-breaker below can still be used when reports require
    // deterministic ordering independent of source-array ordering.
    return [...rows].sort((left, right) => {
        for (const specification of specifications) {
            const result = compareValues(
                left[specification.field],
                right[specification.field],
                specification.descending,
                specification.nullsLast
            );

            if (result !== 0) {
                return result;
            }
        }

        return 0;
    });
}


// -----------------------------------------------------------------------------
// Query object
// -----------------------------------------------------------------------------

class BusinessQuery {
    constructor(rows) {
        this.rows = [...rows];
        this.predicates = [];
        this.orderings = [];
    }

    where(predicate) {
        this.predicates.push(predicate);
        return this;
    }

    orderBy(field, descending = false, nullsLast = true) {
        this.orderings.push({
            field,
            descending,
            nullsLast
        });

        return this;
    }

    execute({ offset = 0, limit = undefined } = {}) {
        if (!Number.isInteger(offset) || offset < 0) {
            throw new RangeError("offset must be a non-negative integer");
        }

        if (
            limit !== undefined &&
            (!Number.isInteger(limit) || limit < 0)
        ) {
            throw new RangeError("limit must be a non-negative integer");
        }

        let result = this.rows;

        for (const predicate of this.predicates) {
            result = where(result, predicate);
        }

        if (this.orderings.length > 0) {
            result = orderBy(result, this.orderings);
        }

        result = result.slice(offset);

        if (limit !== undefined) {
            result = result.slice(0, limit);
        }

        return result;
    }
}


// -----------------------------------------------------------------------------
// Validation
// -----------------------------------------------------------------------------

const validStatuses = new Set([
    "Pending",
    "Processing",
    "Shipped",
    "Cancelled"
]);

const validPriorities = new Set([
    "Low",
    "Medium",
    "High"
]);

function validateOrders(rows) {
    const errors = [];

    for (const order of rows) {
        if (order.orderValue < 0) {
            errors.push(`Order ${order.orderId}: negative order value`);
        }

        if (order.discountRate < 0 || order.discountRate > 1) {
            errors.push(`Order ${order.orderId}: invalid discount rate`);
        }

        if (!validStatuses.has(order.status)) {
            errors.push(`Order ${order.orderId}: invalid status`);
        }

        if (!validPriorities.has(order.priority)) {
            errors.push(`Order ${order.orderId}: invalid priority`);
        }
    }

    return errors;
}


// -----------------------------------------------------------------------------
// Aggregation after filtering
// -----------------------------------------------------------------------------

function totalOrderValue(rows) {
    return rows.reduce((total, order) => total + order.orderValue, 0);
}

function averageOrderValue(rows) {
    return rows.length === 0
        ? 0
        : totalOrderValue(rows) / rows.length;
}

function groupSum(rows, field) {
    const totals = new Map();

    for (const row of rows) {
        const key = row[field];
        totals.set(key, (totals.get(key) ?? 0) + row.orderValue);
    }

    return totals;
}


// -----------------------------------------------------------------------------
// Asynchronous event-driven query service
// -----------------------------------------------------------------------------

class BusinessDataService {
    constructor(rows) {
        this.rows = [...rows];
        this.listeners = new Map();
    }

    on(eventName, listener) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }

        this.listeners.get(eventName).push(listener);
    }

    emit(eventName, payload) {
        const listeners = this.listeners.get(eventName) ?? [];

        for (const listener of listeners) {
            listener(payload);
        }
    }

    async execute(query) {
        this.emit("queryStarted", {
            timestamp: new Date().toISOString()
        });

        // Promise.resolve().then() makes the service asynchronous without
        // introducing an external dependency or pretending that an in-memory
        // operation is a network/database call.
        const result = await Promise.resolve().then(() => query.execute());

        this.emit("queryCompleted", {
            rowCount: result.length,
            timestamp: new Date().toISOString()
        });

        return result;
    }
}


// -----------------------------------------------------------------------------
// Demonstrations
// -----------------------------------------------------------------------------

function demonstrateBasicFiltering() {
    printTitle("Basic WHERE-style filtering");

    const northCustomers = where(
        customers,
        equals("region", "North")
    );

    printRows(
        northCustomers,
        ["customerId", "name", "region", "segment"]
    );

    const largeOrders = where(
        orders,
        greaterThan("orderValue", 200000)
    );

    console.log("\nOrders above 200,000:");
    printRows(
        largeOrders,
        ["orderId", "region", "orderValue", "status"]
    );
}

function demonstrateBooleanFiltering() {
    printTitle("AND, OR, and NOT predicate composition");

    const targetCustomers = where(
        customers,
        allOf(
            equals("active", true),
            anyOf(
                equals("segment", "Enterprise"),
                greaterThan("annualRevenue", 10000000)
            )
        )
    );

    console.log("\nActive Enterprise customers OR active customers above 10M revenue:");
    printRows(
        targetCustomers,
        ["customerId", "name", "segment", "annualRevenue"]
    );

    const openOrders = where(
        orders,
        negate(equals("status", "Cancelled"))
    );

    console.log("\nOrders not cancelled:");
    printRows(
        openOrders,
        ["orderId", "status", "orderValue"]
    );
}

function demonstrateNullHandling() {
    printTitle("NULL-style filtering");

    const unknownRevenue = where(
        customers,
        isNull("annualRevenue")
    );

    console.log("\nCustomers with unknown annual revenue:");
    printRows(
        unknownRevenue,
        ["customerId", "name", "annualRevenue"]
    );

    const knownRevenue = where(
        customers,
        isNotNull("annualRevenue")
    );

    console.log("\nCustomers with known annual revenue:");
    printRows(
        knownRevenue,
        ["customerId", "name", "annualRevenue"]
    );
}

function demonstrateOrdering() {
    printTitle("ORDER BY-style sorting");

    const highestValue = orderBy(
        orders,
        [
            {
                field: "orderValue",
                descending: true,
                nullsLast: true
            }
        ]
    );

    console.log("\nHighest-value orders first:");
    printRows(
        highestValue,
        ["orderId", "orderValue", "region", "status"]
    );

    const regionalQueue = orderBy(
        orders,
        [
            {
                field: "region",
                descending: false,
                nullsLast: true
            },
            {
                field: "orderValue",
                descending: true,
                nullsLast: true
            },
            {
                field: "orderId",
                descending: false,
                nullsLast: true
            }
        ]
    );

    console.log("\nRegion ascending, value descending, order ID as tie-breaker:");
    printRows(
        regionalQueue,
        ["orderId", "region", "orderValue"]
    );
}

function demonstrateQueryPipeline() {
    printTitle("Filtering followed by sorting and pagination");

    const query = new BusinessQuery(orders)
        .where(equals("status", "Shipped"))
        .where(greaterOrEqual("orderValue", 150000))
        .orderBy("orderValue", true)
        .orderBy("orderId", false);

    const firstPage = query.execute({
        offset: 0,
        limit: 3
    });

    console.log("\nFirst three qualifying shipped orders:");
    printRows(
        firstPage,
        ["orderId", "orderValue", "status", "orderDate"]
    );

    const secondPage = query.execute({
        offset: 3,
        limit: 3
    });

    console.log("\nSecond page:");
    printRows(
        secondPage,
        ["orderId", "orderValue", "status", "orderDate"]
    );
}

function demonstrateBusinessReport() {
    printTitle("Filtered sales report");

    const qualifiedOrders = new BusinessQuery(orders)
        .where(negate(equals("status", "Cancelled")))
        .where(greaterOrEqual("orderValue", 100000))
        .orderBy("orderValue", true)
        .execute();

    console.log("\nQualified orders:");
    printRows(
        qualifiedOrders,
        ["orderId", "salesRep", "region", "orderValue", "status"]
    );

    console.log(`\nQualified order count: ${qualifiedOrders.length}`);
    console.log(
        `Qualified order value: ${totalOrderValue(qualifiedOrders).toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })}`
    );

    console.log(
        `Average qualified order: ${averageOrderValue(qualifiedOrders).toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })}`
    );

    const totals = groupSum(qualifiedOrders, "region");

    console.log("\nQualified value by region:");

    [...totals.entries()]
        .sort((left, right) => right[1] - left[1])
        .forEach(([region, value]) => {
            console.log(
                `${region.padEnd(10)} ${value.toLocaleString("en-IN", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                })}`
            );
        });
}

function demonstrateOperationalQueue() {
    printTitle("Operational queue with business priority");

    const queue = new BusinessQuery(orders)
        .where(
            allOf(
                inValues("status", new Set(["Pending", "Processing"])),
                negate(equals("priority", "Low"))
            )
        )
        .orderBy("priority", true)
        .orderBy("orderDate", false)
        .orderBy("orderId", false)
        .execute();

    printRows(
        queue,
        ["orderId", "priority", "status", "orderDate", "orderValue"]
    );
}

function demonstrateCustomerOrderRelationship() {
    printTitle("Customer analysis from filtered orders");

    const shippedOrders = where(
        orders,
        equals("status", "Shipped")
    );

    const shippedValueByCustomer = new Map();

    for (const order of shippedOrders) {
        shippedValueByCustomer.set(
            order.customerId,
            (shippedValueByCustomer.get(order.customerId) ?? 0) +
            order.orderValue
        );
    }

    const customerLookup = new Map(
        customers.map(customer => [customer.customerId, customer])
    );

    const qualified = [...shippedValueByCustomer.entries()]
        .filter(([, value]) => value >= 300000)
        .map(([customerId, value]) => ({
            customer: customerLookup.get(customerId),
            shippedValue: value
        }))
        .filter(item => item.customer !== undefined)
        .sort((left, right) => right.shippedValue - left.shippedValue);

    console.log("\nCustomers with at least 300K shipped-order value:");

    for (const item of qualified) {
        console.log(
            `${item.customer.name.padEnd(22)} ${item.shippedValue.toLocaleString("en-IN")}`
        );
    }
}

function demonstrateValidation() {
    printTitle("Business-data validation");

    const errors = validateOrders(orders);

    if (errors.length === 0) {
        console.log("All sample orders passed validation.");
    } else {
        errors.forEach(error => console.log(`- ${error}`));
    }

    try {
        new BusinessQuery(orders).execute({
            offset: -1
        });
    } catch (error) {
        console.log(`Invalid pagination rejected: ${error.message}`);
    }
}

async function demonstrateEventDrivenService() {
    printTitle("Event-driven asynchronous query service");

    const service = new BusinessDataService(orders);

    service.on("queryStarted", event => {
        console.log(`Query started at ${event.timestamp}`);
    });

    service.on("queryCompleted", event => {
        console.log(`Query completed with ${event.rowCount} rows`);
    });

    const query = new BusinessQuery(orders)
        .where(equals("region", "West"))
        .where(greaterThan("orderValue", 200000))
        .orderBy("orderValue", true)
        .orderBy("orderId", false);

    const result = await service.execute(query);

    console.log("\nWest-region orders above 200K:");
    printRows(
        result,
        ["orderId", "region", "orderValue", "status"]
    );
}


// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

async function main() {
    demonstrateBasicFiltering();
    demonstrateBooleanFiltering();
    demonstrateNullHandling();
    demonstrateOrdering();
    demonstrateQueryPipeline();
    demonstrateBusinessReport();
    demonstrateOperationalQueue();
    demonstrateCustomerOrderRelationship();
    demonstrateValidation();

    await demonstrateEventDrivenService();

    printTitle("Filtering and sorting demonstration complete");
}

main().catch(error => {
    // A top-level rejection handler prevents asynchronous failures from
    // silently disappearing in a command-line business reporting process.
    console.error("Query execution failed:", error.message);
    process.exitCode = 1;
});
