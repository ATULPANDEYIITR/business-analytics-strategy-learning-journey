'use strict';

/*
 * DAX fundamentals represented through a JavaScript analytical model.
 *
 * The implementation separates:
 * 1. row-level calculations, similar to calculated columns
 * 2. filter-context calculations, similar to measures
 * 3. context-changing measure evaluation, similar to CALCULATE
 * 4. event-driven reporting
 *
 * No external packages are required.
 */

const { EventEmitter } = require('node:events');
const { strict: assert } = require('node:assert');

class ModelValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ModelValidationError';
    }
}

class SalesModel extends EventEmitter {
    constructor(rows) {
        super();

        if (!Array.isArray(rows) || rows.length === 0) {
            throw new ModelValidationError('Sales model requires rows.');
        }

        this.rows = rows.map((row) => Object.freeze({ ...row }));
        this.validate();

        // Map provides O(1)-average lookup for product-level aggregations.
        this.productIndex = new Map();

        for (const row of this.rows) {
            const existing = this.productIndex.get(row.product) ?? 0;
            this.productIndex.set(row.product, existing + this.salesAmount(row));
        }
    }

    validate() {
        const ids = new Set();

        for (const row of this.rows) {
            const required = [
                'orderId',
                'orderDate',
                'region',
                'product',
                'category',
                'quantity',
                'unitPrice',
                'unitCost'
            ];

            for (const field of required) {
                if (row[field] === undefined || row[field] === null) {
                    throw new ModelValidationError(
                        `Missing ${field} for order ${row.orderId}`
                    );
                }
            }

            if (ids.has(row.orderId)) {
                throw new ModelValidationError(
                    `Duplicate order ID: ${row.orderId}`
                );
            }

            ids.add(row.orderId);

            if (!Number.isInteger(row.quantity) || row.quantity <= 0) {
                throw new ModelValidationError(
                    `Invalid quantity for order ${row.orderId}`
                );
            }

            if (
                !Number.isFinite(row.unitPrice) ||
                !Number.isFinite(row.unitCost) ||
                row.unitPrice < 0 ||
                row.unitCost < 0
            ) {
                throw new ModelValidationError(
                    `Invalid price for order ${row.orderId}`
                );
            }

            if (row.unitCost > row.unitPrice) {
                throw new ModelValidationError(
                    `Cost exceeds price for order ${row.orderId}`
                );
            }
        }
    }

    salesAmount(row) {
        return row.quantity * row.unitPrice;
    }

    costAmount(row) {
        return row.quantity * row.unitCost;
    }

    profitAmount(row) {
        return this.salesAmount(row) - this.costAmount(row);
    }

    profitMargin(row) {
        const sales = this.salesAmount(row);
        return sales === 0 ? 0 : this.profitAmount(row) / sales;
    }

    salesBand(row) {
        const sales = this.salesAmount(row);

        if (sales >= 5000) return 'High';
        if (sales >= 2000) return 'Medium';
        return 'Low';
    }

    totalSales(context = this.rows) {
        return context.reduce(
            (sum, row) => sum + this.salesAmount(row),
            0
        );
    }

    totalCost(context = this.rows) {
        return context.reduce(
            (sum, row) => sum + this.costAmount(row),
            0
        );
    }

    totalProfit(context = this.rows) {
        return context.reduce(
            (sum, row) => sum + this.profitAmount(row),
            0
        );
    }

    profitMarginMeasure(context = this.rows) {
        const sales = this.totalSales(context);
        return sales === 0 ? 0 : this.totalProfit(context) / sales;
    }

    averageOrderValue(context = this.rows) {
        return context.length === 0
            ? 0
            : this.totalSales(context) / context.length;
    }

    filterContext(filters = {}) {
        const {
            region,
            category,
            product,
            minimumSales
        } = filters;

        return this.rows.filter((row) => {
            if (region !== undefined && row.region !== region) {
                return false;
            }

            if (category !== undefined && row.category !== category) {
                return false;
            }

            if (product !== undefined && row.product !== product) {
                return false;
            }

            if (
                minimumSales !== undefined &&
                this.salesAmount(row) < minimumSales
            ) {
                return false;
            }

            return true;
        });
    }

    calculate(measure, filters = {}) {
        const context = this.filterContext(filters);
        return measure.call(this, context);
    }

    summarize(field) {
        const groups = new Map();

        for (const row of this.rows) {
            const key = row[field];

            if (!groups.has(key)) {
                groups.set(key, []);
            }

            groups.get(key).push(row);
        }

        return [...groups.entries()]
            .sort(([a], [b]) => String(a).localeCompare(String(b)))
            .map(([key, context]) => ({
                key,
                sales: this.totalSales(context),
                profit: this.totalProfit(context),
                margin: this.profitMarginMeasure(context),
                orders: context.length
            }));
    }

    calculatedColumns() {
        return this.rows.map((row) => ({
            ...row,
            salesAmount: this.salesAmount(row),
            costAmount: this.costAmount(row),
            profitAmount: this.profitAmount(row),
            profitMargin: this.profitMargin(row),
            salesBand: this.salesBand(row)
        }));
    }

    topProducts(limit = 3) {
        if (!Number.isInteger(limit) || limit <= 0) {
            throw new RangeError('limit must be a positive integer');
        }

        return [...this.productIndex.entries()]
            .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
            .slice(0, limit);
    }
}

function money(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

function main() {
    const rows = [
        {
            orderId: 1001,
            orderDate: '2026-01-05',
            region: 'North',
            product: 'Laptop',
            category: 'Technology',
            quantity: 2,
            unitPrice: 1200,
            unitCost: 850
        },
        {
            orderId: 1002,
            orderDate: '2026-01-07',
            region: 'South',
            product: 'Monitor',
            category: 'Technology',
            quantity: 4,
            unitPrice: 350,
            unitCost: 220
        },
        {
            orderId: 1003,
            orderDate: '2026-01-09',
            region: 'North',
            product: 'Desk',
            category: 'Furniture',
            quantity: 3,
            unitPrice: 500,
            unitCost: 310
        },
        {
            orderId: 1004,
            orderDate: '2026-01-12',
            region: 'West',
            product: 'Laptop',
            category: 'Technology',
            quantity: 1,
            unitPrice: 1500,
            unitCost: 980
        },
        {
            orderId: 1005,
            orderDate: '2026-01-15',
            region: 'South',
            product: 'Chair',
            category: 'Furniture',
            quantity: 8,
            unitPrice: 180,
            unitCost: 110
        },
        {
            orderId: 1006,
            orderDate: '2026-01-19',
            region: 'West',
            product: 'Desk',
            category: 'Furniture',
            quantity: 2,
            unitPrice: 550,
            unitCost: 320
        },
        {
            orderId: 1007,
            orderDate: '2026-01-23',
            region: 'North',
            product: 'Monitor',
            category: 'Technology',
            quantity: 5,
            unitPrice: 325,
            unitCost: 200
        },
        {
            orderId: 1008,
            orderDate: '2026-01-27',
            region: 'South',
            product: 'Laptop',
            category: 'Technology',
            quantity: 3,
            unitPrice: 1100,
            unitCost: 790
        }
    ];

    const model = new SalesModel(rows);

    model.on('reportGenerated', (event) => {
        console.log(`Event: ${event.type} generated.`);
    });

    const report = {
        totalSales: model.totalSales(),
        totalProfit: model.totalProfit(),
        margin: model.profitMarginMeasure(),
        averageOrderValue: model.averageOrderValue(),
        northSales: model.calculate(model.totalSales, {
            region: 'North'
        }),
        southTechnologyProfit: model.calculate(
            model.totalProfit,
            {
                region: 'South',
                category: 'Technology'
            }
        ),
        regions: model.summarize('region'),
        categories: model.summarize('category'),
        topProducts: model.topProducts(3)
    };

    console.log('=== DAX FUNDAMENTALS MODEL ===');
    console.log(`Total Sales: ${money(report.totalSales)}`);
    console.log(`Total Profit: ${money(report.totalProfit)}`);
    console.log(`Profit Margin: ${(report.margin * 100).toFixed(2)}%`);
    console.log(`Average Order Value: ${money(report.averageOrderValue)}`);

    console.log('\n=== FILTER CONTEXT ===');
    console.log(`North Sales: ${money(report.northSales)}`);
    console.log(
        `South Technology Profit: ${money(report.southTechnologyProfit)}`
    );

    console.log('\n=== CALCULATED COLUMN LOGIC ===');
    for (const row of model.calculatedColumns()) {
        console.log(
            `Order ${row.orderId}: ` +
            `${money(row.salesAmount)} sales, ` +
            `${money(row.profitAmount)} profit, ` +
            `${(row.profitMargin * 100).toFixed(2)}% margin, ` +
            `${row.salesBand}`
        );
    }

    console.log('\n=== REGION MEASURES ===');
    for (const item of report.regions) {
        console.log(
            `${item.key}: sales=${money(item.sales)}, ` +
            `profit=${money(item.profit)}, ` +
            `margin=${(item.margin * 100).toFixed(2)}%`
        );
    }

    console.log('\n=== TOP PRODUCTS ===');
    for (const [product, sales] of report.topProducts) {
        console.log(`${product}: ${money(sales)}`);
    }

    model.emit('reportGenerated', {
        type: 'sales-report',
        rowCount: model.rows.length
    });

    // Runtime checks cover edge cases and expected model semantics.
    assert.equal(model.totalSales(), 10555);
    assert.equal(model.totalProfit(), 3405);
    assert.equal(model.filterContext({ region: 'North' }).length, 3);
    assert.equal(model.totalSales([]), 0);
    assert.equal(model.profitMarginMeasure([]), 0);

    console.log('\nValidation checks: PASSED');
}

main();
