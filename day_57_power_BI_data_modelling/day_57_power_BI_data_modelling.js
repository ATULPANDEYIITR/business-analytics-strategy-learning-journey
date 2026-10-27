'use strict';

/*
 * Power BI-style dimensional model implemented with Node.js standard features.
 *
 * The model uses a star schema:
 *   DimDate       \
 *   DimCustomer   ---> FactSales
 *   DimProduct    /
 *
 * Dimension filters are evaluated first, then measures aggregate fact rows.
 */

const { EventEmitter } = require('node:events');

class ModelValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ModelValidationError';
    }
}

class DimensionTable {
    constructor(name, keyName) {
        this.name = name;
        this.keyName = keyName;
        this.rows = new Map();
    }

    add(row) {
        const key = row[this.keyName];

        if (key === undefined || key === null) {
            throw new ModelValidationError(
                `${this.name}: missing ${this.keyName}`
            );
        }

        if (this.rows.has(key)) {
            throw new ModelValidationError(
                `${this.name}: duplicate key ${key}`
            );
        }

        this.rows.set(key, Object.freeze({ ...row }));
    }

    get(key) {
        return this.rows.get(key);
    }

    has(key) {
        return this.rows.has(key);
    }

    values() {
        return [...this.rows.values()];
    }
}

class FactSalesTable {
    constructor() {
        this.rows = [];
        this.keys = new Set();
    }

    add(row, dimensions) {
        if (this.keys.has(row.salesKey)) {
            throw new ModelValidationError(
                `FactSales: duplicate sales key ${row.salesKey}`
            );
        }

        if (!Number.isInteger(row.quantity) || row.quantity <= 0) {
            throw new ModelValidationError(
                `FactSales: quantity must be a positive integer`
            );
        }

        if (row.unitPrice < 0) {
            throw new ModelValidationError(
                `FactSales: unit price cannot be negative`
            );
        }

        if (row.discountRate < 0 || row.discountRate > 1) {
            throw new ModelValidationError(
                `FactSales: discount rate must be between 0 and 1`
            );
        }

        if (!dimensions.date.has(row.dateKey)) {
            throw new ModelValidationError(
                `FactSales: missing date key ${row.dateKey}`
            );
        }

        if (!dimensions.customer.has(row.customerKey)) {
            throw new ModelValidationError(
                `FactSales: missing customer key ${row.customerKey}`
            );
        }

        if (!dimensions.product.has(row.productKey)) {
            throw new ModelValidationError(
                `FactSales: missing product key ${row.productKey}`
            );
        }

        this.rows.push(Object.freeze({ ...row }));
        this.keys.add(row.salesKey);
    }
}

class StarSchemaModel extends EventEmitter {
    constructor() {
        super();

        this.date = new DimensionTable('DimDate', 'dateKey');
        this.customer = new DimensionTable('DimCustomer', 'customerKey');
        this.product = new DimensionTable('DimProduct', 'productKey');
        this.sales = new FactSalesTable();

        this.relationships = [
            {
                from: 'FactSales.dateKey',
                to: 'DimDate.dateKey',
                cardinality: 'many-to-one',
                direction: 'single'
            },
            {
                from: 'FactSales.customerKey',
                to: 'DimCustomer.customerKey',
                cardinality: 'many-to-one',
                direction: 'single'
            },
            {
                from: 'FactSales.productKey',
                to: 'DimProduct.productKey',
                cardinality: 'many-to-one',
                direction: 'single'
            }
        ];
    }

    addSale(row) {
        this.sales.add(row, {
            date: this.date,
            customer: this.customer,
            product: this.product
        });

        this.emit('saleAdded', row);
    }

    validateModel() {
        for (const relationship of this.relationships) {
            if (
                relationship.cardinality !== 'many-to-one' ||
                relationship.direction !== 'single'
            ) {
                throw new ModelValidationError(
                    `Unsupported relationship configuration: ${JSON.stringify(
                        relationship
                    )}`
                );
            }
        }

        for (const fact of this.sales.rows) {
            if (!this.date.has(fact.dateKey)) {
                throw new ModelValidationError('Broken date relationship');
            }
            if (!this.customer.has(fact.customerKey)) {
                throw new ModelValidationError('Broken customer relationship');
            }
            if (!this.product.has(fact.productKey)) {
                throw new ModelValidationError('Broken product relationship');
            }
        }
    }

    filterSales(criteria = {}) {
        return this.sales.rows.filter((fact) => {
            const date = this.date.get(fact.dateKey);
            const customer = this.customer.get(fact.customerKey);
            const product = this.product.get(fact.productKey);

            if (criteria.year !== undefined && date.year !== criteria.year) {
                return false;
            }

            if (
                criteria.region !== undefined &&
                customer.region !== criteria.region
            ) {
                return false;
            }

            if (
                criteria.category !== undefined &&
                product.category !== criteria.category
            ) {
                return false;
            }

            if (
                criteria.segment !== undefined &&
                customer.segment !== criteria.segment
            ) {
                return false;
            }

            return true;
        });
    }

    netSales(facts) {
        return facts.reduce((total, fact) => {
            const gross = fact.quantity * fact.unitPrice;
            return total + gross * (1 - fact.discountRate);
        }, 0);
    }

    quantity(facts) {
        return facts.reduce((total, fact) => total + fact.quantity, 0);
    }

    groupBy(facts, keySelector) {
        const result = new Map();

        for (const fact of facts) {
            const key = keySelector(fact);
            const amount =
                fact.quantity *
                fact.unitPrice *
                (1 - fact.discountRate);

            result.set(key, (result.get(key) || 0) + amount);
        }

        return result;
    }

    async evaluateAsync(criteria) {
        // Promise-based evaluation models a service/report query boundary.
        await Promise.resolve();

        const facts = this.filterSales(criteria);

        return {
            criteria,
            rows: facts.length,
            netSales: this.netSales(facts),
            quantity: this.quantity(facts)
        };
    }
}

function createModel() {
    const model = new StarSchemaModel();

    model.date.add({
        dateKey: 20260105,
        calendarDate: '2026-01-05',
        year: 2026,
        quarter: 1,
        month: 1
    });

    model.date.add({
        dateKey: 20260207,
        calendarDate: '2026-02-07',
        year: 2026,
        quarter: 1,
        month: 2
    });

    model.date.add({
        dateKey: 20260312,
        calendarDate: '2026-03-12',
        year: 2026,
        quarter: 1,
        month: 3
    });

    model.date.add({
        dateKey: 20260425,
        calendarDate: '2026-04-25',
        year: 2026,
        quarter: 2,
        month: 4
    });

    model.customer.add({
        customerKey: 1,
        customerId: 'C001',
        customerName: 'Apex Systems',
        segment: 'Enterprise',
        region: 'North'
    });

    model.customer.add({
        customerKey: 2,
        customerId: 'C002',
        customerName: 'Blue Retail',
        segment: 'SMB',
        region: 'West'
    });

    model.customer.add({
        customerKey: 3,
        customerId: 'C003',
        customerName: 'Cedar Health',
        segment: 'Enterprise',
        region: 'South'
    });

    model.customer.add({
        customerKey: 4,
        customerId: 'C004',
        customerName: 'Delta Labs',
        segment: 'Mid-Market',
        region: 'East'
    });

    model.product.add({
        productKey: 1,
        productId: 'P001',
        productName: 'Analytics Platform',
        category: 'Software',
        subcategory: 'Analytics'
    });

    model.product.add({
        productKey: 2,
        productId: 'P002',
        productName: 'Security Suite',
        category: 'Software',
        subcategory: 'Security'
    });

    model.product.add({
        productKey: 3,
        productId: 'P003',
        productName: 'Cloud Appliance',
        category: 'Hardware',
        subcategory: 'Infrastructure'
    });

    model.product.add({
        productKey: 4,
        productId: 'P004',
        productName: 'Support Contract',
        category: 'Services',
        subcategory: 'Support'
    });

    model.addSale({
        salesKey: 1,
        dateKey: 20260105,
        customerKey: 1,
        productKey: 1,
        orderId: 'SO1001',
        quantity: 3,
        unitPrice: 1200,
        discountRate: 0.05
    });

    model.addSale({
        salesKey: 2,
        dateKey: 20260207,
        customerKey: 2,
        productKey: 2,
        orderId: 'SO1002',
        quantity: 2,
        unitPrice: 800,
        discountRate: 0
    });

    model.addSale({
        salesKey: 3,
        dateKey: 20260312,
        customerKey: 3,
        productKey: 3,
        orderId: 'SO1003',
        quantity: 1,
        unitPrice: 4500,
        discountRate: 0.1
    });

    model.addSale({
        salesKey: 4,
        dateKey: 20260425,
        customerKey: 4,
        productKey: 4,
        orderId: 'SO1004',
        quantity: 5,
        unitPrice: 300,
        discountRate: 0.05
    });

    model.validateModel();

    return model;
}

async function main() {
    const model = createModel();

    model.on('saleAdded', (sale) => {
        if (sale.quantity > 1000) {
            console.warn(
                `High-volume transaction detected: ${sale.orderId}`
            );
        }
    });

    const all = model.filterSales();
    const software = model.filterSales({ category: 'Software' });
    const enterprise = model.filterSales({ segment: 'Enterprise' });

    console.log('POWER BI-STYLE DATA MODEL');
    console.log('=========================');
    console.log(`Fact rows: ${all.length}`);
    console.log(`Total net sales: $${model.netSales(all).toFixed(2)}`);
    console.log(`Software sales: $${model.netSales(software).toFixed(2)}`);
    console.log(
        `Enterprise sales: $${model.netSales(enterprise).toFixed(2)}`
    );

    console.log('\nSales by region');

    const byRegion = model.groupBy(
        all,
        (fact) => model.customer.get(fact.customerKey).region
    );

    for (const [region, amount] of byRegion) {
        console.log(`${region}: $${amount.toFixed(2)}`);
    }

    const query = await model.evaluateAsync({
        year: 2026,
        region: 'North'
    });

    console.log('\nAsync report query');
    console.log(JSON.stringify(query, null, 2));

    console.log('\nValidation failure');

    try {
        model.addSale({
            salesKey: 99,
            dateKey: 20269999,
            customerKey: 1,
            productKey: 1,
            orderId: 'INVALID',
            quantity: 1,
            unitPrice: 100,
            discountRate: 0
        });
    } catch (error) {
        console.log(`${error.name}: ${error.message}`);
    }

    console.log('\nDesign characteristics');
    console.log('- Dimensions are indexed by surrogate keys using Map.');
    console.log('- Fact rows contain additive and semi-additive business measures.');
    console.log('- Relationships are explicitly validated as many-to-one.');
    console.log('- Filtering represents dimension-to-fact filter propagation.');
    console.log('- Aggregation scans only the filtered fact set.');
    console.log('- Immutable rows reduce accidental mutation of model state.');
}

main().catch((error) => {
    console.error(`Fatal error: ${error.message}`);
    process.exitCode = 1;
});
