'use strict';

/*
 * SQL-style Aggregations in JavaScript
 * ------------------------------------
 *
 * This file models COUNT, SUM, AVG, MIN, and MAX around an order-processing
 * workflow. It emphasizes JavaScript-specific techniques:
 *
 * - Array.reduce() for aggregation
 * - Map for grouped aggregation
 * - event-driven processing with EventEmitter
 * - asynchronous record streams
 * - BigInt for exact integer quantities
 * - explicit handling of null and undefined
 * - immutable domain records
 * - validation and policy checks
 *
 * Run with:
 *     node aggregations.js
 */

const { EventEmitter } = require('node:events');

// ---------------------------------------------------------------------------
// Domain data
// ---------------------------------------------------------------------------

const orders = Object.freeze([
    Object.freeze({
        orderId: 1001,
        customer: 'Aarav',
        region: 'North',
        category: 'Laptop',
        quantity: 2,
        unitPrice: 850,
        status: 'completed'
    }),
    Object.freeze({
        orderId: 1002,
        customer: 'Diya',
        region: 'North',
        category: 'Phone',
        quantity: 3,
        unitPrice: 500,
        status: 'completed'
    }),
    Object.freeze({
        orderId: 1003,
        customer: 'Kabir',
        region: 'West',
        category: 'Monitor',
        quantity: 1,
        unitPrice: 300,
        status: 'completed'
    }),
    Object.freeze({
        orderId: 1004,
        customer: 'Meera',
        region: 'South',
        category: 'Laptop',
        quantity: 1,
        unitPrice: 920,
        status: 'cancelled'
    }),
    Object.freeze({
        orderId: 1005,
        customer: 'Aarav',
        region: 'North',
        category: 'Keyboard',
        quantity: 4,
        unitPrice: 75,
        status: 'completed'
    }),
    Object.freeze({
        orderId: 1006,
        customer: 'Riya',
        region: 'East',
        category: 'Phone',
        quantity: 2,
        unitPrice: 650,
        status: 'completed'
    }),
    Object.freeze({
        orderId: 1007,
        customer: 'Kabir',
        region: 'West',
        category: 'Laptop',
        quantity: 1,
        unitPrice: 1100,
        status: 'completed'
    }),
    Object.freeze({
        orderId: 1008,
        customer: 'Meera',
        region: 'South',
        category: 'Monitor',
        quantity: 2,
        unitPrice: 280,
        status: 'completed'
    }),
    Object.freeze({
        orderId: 1009,
        customer: 'Riya',
        region: 'East',
        category: 'Keyboard',
        quantity: 5,
        unitPrice: 60,
        status: 'pending'
    }),
    Object.freeze({
        orderId: 1010,
        customer: 'Aarav',
        region: 'North',
        category: 'Monitor',
        quantity: 2,
        unitPrice: 325,
        status: 'completed'
    })
]);

function revenue(order) {
    return order.quantity * order.unitPrice;
}

// ---------------------------------------------------------------------------
// Basic aggregation functions
// ---------------------------------------------------------------------------

function countRows(values) {
    // COUNT(*) counts rows even when the selected value is null.
    return values.length;
}

function countNonNull(values) {
    // SQL COUNT(column) excludes NULL. Treat both null and undefined as
    // missing values at the application boundary.
    return values.reduce(
        (count, value) => count + (value !== null && value !== undefined ? 1 : 0),
        0
    );
}

function sumValues(values) {
    return values.reduce((total, value) => {
        if (value === null || value === undefined) {
            return total;
        }

        if (typeof value !== 'number' || !Number.isFinite(value)) {
            throw new TypeError(`SUM received a non-finite value: ${value}`);
        }

        return total + value;
    }, 0);
}

function averageValues(values) {
    const present = values.filter(
        value => value !== null && value !== undefined
    );

    if (present.length === 0) {
        return null;
    }

    return sumValues(present) / present.length;
}

function minValue(values) {
    const present = values.filter(
        value => value !== null && value !== undefined
    );

    return present.length === 0 ? null : Math.min(...present);
}

function maxValue(values) {
    const present = values.filter(
        value => value !== null && value !== undefined
    );

    return present.length === 0 ? null : Math.max(...present);
}

// ---------------------------------------------------------------------------
// Fundamental demonstration
// ---------------------------------------------------------------------------

function demonstrateBasicAggregations() {
    console.log('\n=== Basic Aggregations ===');

    const quantities = orders.map(order => order.quantity);
    const prices = orders.map(order => order.unitPrice);
    const revenues = orders.map(revenue);

    console.log('COUNT(*)          =', countRows(orders));
    console.log('COUNT(quantity)   =', countNonNull(quantities));
    console.log('SUM(quantity)     =', sumValues(quantities));
    console.log('SUM(revenue)      =', sumValues(revenues));
    console.log('AVG(unitPrice)    =', averageValues(prices));
    console.log('MIN(unitPrice)    =', minValue(prices));
    console.log('MAX(unitPrice)    =', maxValue(prices));
}

// ---------------------------------------------------------------------------
// Missing values
// ---------------------------------------------------------------------------

function demonstrateNullSemantics() {
    console.log('\n=== Missing Values ===');

    const values = [80, null, 90, undefined, 70];

    console.log('Input             =', values);
    console.log('COUNT(*)          =', countRows(values));
    console.log('COUNT(value)      =', countNonNull(values));
    console.log('SUM(value)        =', sumValues(values));
    console.log('AVG(value)        =', averageValues(values));
    console.log('MIN(value)        =', minValue(values));
    console.log('MAX(value)        =', maxValue(values));
}

// ---------------------------------------------------------------------------
// Filtering and conditional aggregation
// ---------------------------------------------------------------------------

function demonstrateFiltering() {
    console.log('\n=== Filtering Before Aggregation ===');

    const completed = orders.filter(order => order.status === 'completed');

    console.log('Completed count   =', countRows(completed));
    console.log(
        'Completed revenue =',
        sumValues(completed.map(revenue)).toFixed(2)
    );

    console.log('\n=== Conditional Aggregation ===');

    const pendingCount = countRows(
        orders.filter(order => order.status === 'pending')
    );

    const cancelledCount = countRows(
        orders.filter(order => order.status === 'cancelled')
    );

    console.log('Pending orders    =', pendingCount);
    console.log('Cancelled orders  =', cancelledCount);
}

// ---------------------------------------------------------------------------
// GROUP BY using Map
// ---------------------------------------------------------------------------

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

function aggregateGroup(records) {
    const quantities = records.map(order => order.quantity);
    const revenues = records.map(revenue);

    return Object.freeze({
        count: records.length,
        quantitySum: sumValues(quantities),
        revenueSum: sumValues(revenues),
        revenueAverage: averageValues(revenues),
        revenueMin: minValue(revenues),
        revenueMax: maxValue(revenues)
    });
}

function demonstrateGroupedAggregation() {
    console.log('\n=== GROUP BY Region ===');

    const groups = groupBy(orders, order => order.region);

    for (const [region, records] of groups) {
        const aggregate = aggregateGroup(records);

        console.log(
            region.padEnd(6),
            `COUNT=${aggregate.count}`,
            `SUM(quantity)=${aggregate.quantitySum}`,
            `AVG(revenue)=${aggregate.revenueAverage.toFixed(2)}`,
            `MIN(revenue)=${aggregate.revenueMin.toFixed(2)}`,
            `MAX(revenue)=${aggregate.revenueMax.toFixed(2)}`
        );
    }
}

// ---------------------------------------------------------------------------
// Post-aggregation filtering
// ---------------------------------------------------------------------------

function demonstrateHavingStyleFiltering() {
    console.log('\n=== HAVING-style Filtering ===');

    const groups = groupBy(orders, order => order.region);

    for (const [region, records] of groups) {
        const totalRevenue = sumValues(records.map(revenue));

        // The threshold is evaluated after the region's SUM has been built.
        if (totalRevenue >= 2000) {
            console.log(
                `${region}: revenue ${totalRevenue.toFixed(2)}`
            );
        }
    }
}

// ---------------------------------------------------------------------------
// Single-pass aggregation
// ---------------------------------------------------------------------------

function aggregateInOnePass(values) {
    /*
     * A single pass avoids creating separate filtered arrays for every
     * aggregate. This matters when the input contains millions of records.
     */
    let count = 0;
    let nonNullCount = 0;
    let sum = 0;
    let minimum = null;
    let maximum = null;

    for (const value of values) {
        count += 1;

        if (value === null || value === undefined) {
            continue;
        }

        if (!Number.isFinite(value)) {
            throw new TypeError(`Invalid aggregate value: ${value}`);
        }

        nonNullCount += 1;
        sum += value;

        if (minimum === null || value < minimum) {
            minimum = value;
        }

        if (maximum === null || value > maximum) {
            maximum = value;
        }
    }

    return Object.freeze({
        count,
        nonNullCount,
        sum,
        average: nonNullCount === 0 ? null : sum / nonNullCount,
        minimum,
        maximum
    });
}

function demonstrateSinglePassAggregation() {
    console.log('\n=== Single-pass Aggregation ===');

    const result = aggregateInOnePass([
        10,
        null,
        20,
        40,
        undefined,
        30
    ]);

    console.log(result);
}

// ---------------------------------------------------------------------------
// Event-driven aggregation
// ---------------------------------------------------------------------------

class OrderAggregator extends EventEmitter {
    constructor() {
        super();

        this.state = {
            count: 0,
            completedCount: 0,
            revenueSum: 0,
            minimumOrderValue: null,
            maximumOrderValue: null
        };
    }

    process(order) {
        validateOrder(order);

        this.state.count += 1;

        const orderRevenue = revenue(order);

        if (order.status === 'completed') {
            this.state.completedCount += 1;
            this.state.revenueSum += orderRevenue;

            if (
                this.state.minimumOrderValue === null ||
                orderRevenue < this.state.minimumOrderValue
            ) {
                this.state.minimumOrderValue = orderRevenue;
            }

            if (
                this.state.maximumOrderValue === null ||
                orderRevenue > this.state.maximumOrderValue
            ) {
                this.state.maximumOrderValue = orderRevenue;
            }
        }

        this.emit('orderProcessed', order);
    }

    result() {
        const completedCount = this.state.completedCount;

        return Object.freeze({
            ...this.state,
            averageCompletedOrderValue:
                completedCount === 0
                    ? null
                    : this.state.revenueSum / completedCount
        });
    }
}

function demonstrateEventDrivenAggregation() {
    console.log('\n=== Event-driven Aggregation ===');

    const aggregator = new OrderAggregator();

    aggregator.on('orderProcessed', order => {
        // EventEmitter decouples record ingestion from aggregation consumers.
        if (order.status === 'cancelled') {
            console.log(`Observed cancelled order ${order.orderId}`);
        }
    });

    for (const order of orders) {
        aggregator.process(order);
    }

    console.log(aggregator.result());
}

// ---------------------------------------------------------------------------
// Asynchronous processing
// ---------------------------------------------------------------------------

async function* orderStream(records) {
    for (const record of records) {
        // A real application could receive records from a network response,
        // message queue, file stream, or database cursor.
        await Promise.resolve();
        yield record;
    }
}

async function aggregateAsync(stream) {
    let count = 0;
    let revenueSum = 0;

    for await (const order of stream) {
        validateOrder(order);
        count += 1;
        revenueSum += revenue(order);
    }

    return Object.freeze({
        count,
        revenueSum,
        averageRevenue: count === 0 ? null : revenueSum / count
    });
}

async function demonstrateAsyncAggregation() {
    console.log('\n=== Asynchronous Aggregation ===');

    const result = await aggregateAsync(orderStream(orders));

    console.log(result);
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function validateOrder(order) {
    if (!order || typeof order !== 'object') {
        throw new TypeError('Order must be an object');
    }

    if (!Number.isInteger(order.orderId)) {
        throw new TypeError('orderId must be an integer');
    }

    if (!Number.isInteger(order.quantity) || order.quantity <= 0) {
        throw new RangeError(
            `Order ${order.orderId}: quantity must be positive`
        );
    }

    if (
        typeof order.unitPrice !== 'number' ||
        !Number.isFinite(order.unitPrice) ||
        order.unitPrice < 0
    ) {
        throw new RangeError(
            `Order ${order.orderId}: unitPrice must be a finite non-negative number`
        );
    }

    const allowedStatuses = new Set([
        'completed',
        'pending',
        'cancelled'
    ]);

    if (!allowedStatuses.has(order.status)) {
        throw new RangeError(
            `Order ${order.orderId}: unsupported status ${order.status}`
        );
    }
}

function demonstrateValidation() {
    console.log('\n=== Validation ===');

    const invalidOrder = {
        orderId: 2001,
        quantity: -4,
        unitPrice: 100,
        status: 'completed'
    };

    try {
        validateOrder(invalidOrder);
    } catch (error) {
        console.log('Rejected invalid record:', error.message);
    }
}

// ---------------------------------------------------------------------------
// BigInt and exact integer aggregation
// ---------------------------------------------------------------------------

function demonstrateBigInt() {
    console.log('\n=== BigInt for Large Integer Counts ===');

    const quantities = [
        9007199254740991n,
        8n,
        12n
    ];

    const total = quantities.reduce(
        (sum, quantity) => sum + quantity,
        0n
    );

    console.log('Exact quantity total =', total.toString());

    /*
     * JavaScript Number is not safe for every integer above
     * Number.MAX_SAFE_INTEGER. BigInt is appropriate for exact integer
     * counts, but BigInt cannot be mixed directly with Number.
     */
}

// ---------------------------------------------------------------------------
// Floating-point precision
// ---------------------------------------------------------------------------

function demonstrateNumericPrecision() {
    console.log('\n=== Numeric Precision ===');

    const floatingPointTotal = 0.1 + 0.1 + 0.1;

    console.log(
        'JavaScript floating-point SUM =',
        floatingPointTotal
    );

    console.log(
        'Rounded monetary SUM          =',
        floatingPointTotal.toFixed(2)
    );

    /*
     * Formatting with toFixed() only controls presentation. It does not turn
     * binary floating-point arithmetic into decimal arithmetic. Financial
     * applications should use integer minor units or a decimal arithmetic
     * library when exact monetary aggregation is required.
     */
}

// ---------------------------------------------------------------------------
// Executable correctness checks
// ---------------------------------------------------------------------------

function runChecks() {
    const revenues = orders.map(revenue);

    if (countRows(orders) !== 10) {
        throw new Error('COUNT(*) invariant failed');
    }

    if (sumValues(revenues) !== 6905) {
        throw new Error('SUM(revenue) invariant failed');
    }

    if (minValue(revenues) !== 300) {
        throw new Error('MIN(revenue) invariant failed');
    }

    if (maxValue(revenues) !== 1700) {
        throw new Error('MAX(revenue) invariant failed');
    }

    const values = [10, null, 30];

    if (countNonNull(values) !== 2) {
        throw new Error('COUNT(value) NULL rule failed');
    }

    if (sumValues(values) !== 40) {
        throw new Error('NULL-aware SUM failed');
    }

    if (averageValues(values) !== 20) {
        throw new Error('AVG calculation failed');
    }

    if (minValue(values) !== 10 || maxValue(values) !== 30) {
        throw new Error('MIN/MAX calculation failed');
    }

    if (
        averageValues([]) !== null ||
        minValue([]) !== null ||
        maxValue([]) !== null
    ) {
        throw new Error('Empty-input aggregate behavior failed');
    }

    console.log('\nAll JavaScript aggregation checks passed.');
}

// ---------------------------------------------------------------------------
// SQL reference
// ---------------------------------------------------------------------------

function printSqlReference() {
    console.log('\n=== SQL Reference ===');

    console.log('SELECT COUNT(*) FROM orders;');
    console.log('SELECT COUNT(unit_price) FROM orders;');
    console.log('SELECT SUM(quantity) FROM orders;');
    console.log('SELECT AVG(unit_price) FROM orders;');
    console.log('SELECT MIN(unit_price) FROM orders;');
    console.log('SELECT MAX(unit_price) FROM orders;');
    console.log(
        'SELECT region, COUNT(*), SUM(quantity), AVG(unit_price), ' +
        'MIN(unit_price), MAX(unit_price) FROM orders GROUP BY region;'
    );
}

// ---------------------------------------------------------------------------
// Main execution
// ---------------------------------------------------------------------------

async function main() {
    demonstrateBasicAggregations();
    demonstrateNullSemantics();
    demonstrateFiltering();
    demonstrateGroupedAggregation();
    demonstrateHavingStyleFiltering();
    demonstrateSinglePassAggregation();
    demonstrateEventDrivenAggregation();
    await demonstrateAsyncAggregation();
    demonstrateValidation();
    demonstrateBigInt();
    demonstrateNumericPrecision();
    printSqlReference();
    runChecks();
}

main().catch(error => {
    console.error('Aggregation program failed:', error.message);
    process.exitCode = 1;
});
