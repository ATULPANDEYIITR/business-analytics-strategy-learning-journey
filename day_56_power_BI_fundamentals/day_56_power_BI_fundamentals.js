'use strict';

const fs = require('node:fs/promises');

const DatasetState = Object.freeze({
    CREATED: 'Created',
    REFRESHED: 'Refreshed',
    FAILED: 'Refresh Failed'
});

const VisualType = Object.freeze({
    CARD: 'Card',
    TABLE: 'Table',
    BAR_CHART: 'Bar Chart',
    LINE_CHART: 'Line Chart',
    SLICER: 'Slicer'
});

class Sale {
    constructor({ id, date, region, product, category, quantity, unitPrice, customerId }) {
        this.id = id;
        this.date = new Date(date);
        this.region = String(region).trim();
        this.product = String(product).trim();
        this.category = String(category).trim();
        this.quantity = Number(quantity);
        this.unitPrice = Number(unitPrice);
        this.customerId = Number(customerId);
    }

    get revenue() {
        return this.quantity * this.unitPrice;
    }
}

class Dataset {
    constructor(name, rows = []) {
        this.name = name;
        this.rows = rows;
        this.state = DatasetState.CREATED;
        this.lastRefresh = null;
    }

    validate() {
        if (!this.name.trim()) {
            throw new Error('Dataset name cannot be empty.');
        }

        const ids = new Set();

        for (const row of this.rows) {
            if (ids.has(row.id)) {
                throw new Error(`Duplicate sale ID: ${row.id}`);
            }

            ids.add(row.id);

            if (!Number.isInteger(row.quantity) || row.quantity <= 0) {
                throw new Error(`Invalid quantity for sale ${row.id}`);
            }

            if (!Number.isFinite(row.unitPrice) || row.unitPrice < 0) {
                throw new Error(`Invalid unit price for sale ${row.id}`);
            }

            if (!row.region || !row.product || !row.category) {
                throw new Error(`Missing dimensions for sale ${row.id}`);
            }

            if (Number.isNaN(row.date.getTime())) {
                throw new Error(`Invalid date for sale ${row.id}`);
            }
        }
    }

    async refresh() {
        try {
            this.validate();

            // Simulates an asynchronous dataset refresh operation.
            await new Promise(resolve => setTimeout(resolve, 20));

            this.state = DatasetState.REFRESHED;
            this.lastRefresh = new Date();
        } catch (error) {
            this.state = DatasetState.FAILED;
            throw error;
        }
    }

    aggregate(dimension, measure = 'Revenue') {
        const result = new Map();

        for (const row of this.rows) {
            const key = row[dimension];
            const value = measure === 'Revenue' ? row.revenue : row.quantity;
            result.set(key, (result.get(key) ?? 0) + value);
        }

        return Object.fromEntries(
            [...result.entries()].sort((a, b) => b[1] - a[1])
        );
    }

    totalRevenue() {
        return this.rows.reduce((total, row) => total + row.revenue, 0);
    }
}

class Visual {
    constructor({ title, type, measure, dimension = null, filter = null }) {
        this.title = title;
        this.type = type;
        this.measure = measure;
        this.dimension = dimension;
        this.filter = filter;
    }

    render(dataset) {
        if (dataset.state !== DatasetState.REFRESHED) {
            throw new Error('Cannot render a dataset before refresh.');
        }

        const rows = this.filter
            ? dataset.rows.filter(row => row.region === this.filter)
            : dataset.rows;

        const value = rows.reduce((total, row) => {
            return total + (this.measure === 'Revenue' ? row.revenue : row.quantity);
        }, 0);

        const result = {
            title: this.title,
            type: this.type,
            measure: this.measure,
            value: Number(value.toFixed(2))
        };

        if (this.dimension) {
            const grouped = new Map();

            for (const row of rows) {
                const key = row[this.dimension];
                const metric = this.measure === 'Revenue'
                    ? row.revenue
                    : row.quantity;

                grouped.set(key, (grouped.get(key) ?? 0) + metric);
            }

            result.groups = Object.fromEntries(
                [...grouped.entries()].sort((a, b) => b[1] - a[1])
            );
        }

        return result;
    }
}

class ReportPage {
    constructor(name, visuals = []) {
        this.name = name;
        this.visuals = visuals;
    }

    render(dataset) {
        return this.visuals.map(visual => visual.render(dataset));
    }
}

class Report {
    constructor(name, dataset) {
        this.name = name;
        this.dataset = dataset;
        this.pages = [];
    }

    addPage(page) {
        if (!page.name.trim()) {
            throw new Error('Report page name cannot be empty.');
        }
        this.pages.push(page);
    }

    definition() {
        return {
            name: this.name,
            dataset: this.dataset.name,
            datasetState: this.dataset.state,
            pages: this.pages.map(page => ({
                name: page.name,
                visuals: page.visuals.map(v => ({
                    title: v.title,
                    type: v.type,
                    measure: v.measure,
                    dimension: v.dimension,
                    filter: v.filter
                }))
            }))
        };
    }
}

function createDataset() {
    return new Dataset('Sales Analytics Dataset', [
        new Sale({
            id: 1, date: '2026-01-05', region: 'North',
            product: 'Laptop', category: 'Computers',
            quantity: 2, unitPrice: 85000, customerId: 101
        }),
        new Sale({
            id: 2, date: '2026-01-12', region: 'South',
            product: 'Monitor', category: 'Accessories',
            quantity: 5, unitPrice: 18000, customerId: 102
        }),
        new Sale({
            id: 3, date: '2026-02-02', region: 'North',
            product: 'Keyboard', category: 'Accessories',
            quantity: 8, unitPrice: 3500, customerId: 103
        }),
        new Sale({
            id: 4, date: '2026-02-14', region: 'West',
            product: 'Laptop', category: 'Computers',
            quantity: 1, unitPrice: 92000, customerId: 104
        }),
        new Sale({
            id: 5, date: '2026-02-21', region: 'South',
            product: 'Laptop', category: 'Computers',
            quantity: 3, unitPrice: 87000, customerId: 105
        }),
        new Sale({
            id: 6, date: '2026-03-03', region: 'East',
            product: 'Monitor', category: 'Accessories',
            quantity: 7, unitPrice: 17500, customerId: 106
        }),
        new Sale({
            id: 7, date: '2026-03-10', region: 'West',
            product: 'Keyboard', category: 'Accessories',
            quantity: 10, unitPrice: 3200, customerId: 107
        }),
        new Sale({
            id: 8, date: '2026-03-18', region: 'East',
            product: 'Laptop', category: 'Computers',
            quantity: 2, unitPrice: 88000, customerId: 108
        })
    ]);
}

async function main() {
    const dataset = createDataset();

    await dataset.refresh();

    const report = new Report('Regional Sales Report', dataset);

    report.addPage(new ReportPage('Executive Overview', [
        new Visual({
            title: 'Total Revenue',
            type: VisualType.CARD,
            measure: 'Revenue'
        }),
        new Visual({
            title: 'Revenue by Region',
            type: VisualType.BAR_CHART,
            measure: 'Revenue',
            dimension: 'region'
        }),
        new Visual({
            title: 'Quantity by Category',
            type: VisualType.TABLE,
            measure: 'Quantity',
            dimension: 'category'
        })
    ]));

    report.addPage(new ReportPage('North Analysis', [
        new Visual({
            title: 'North Revenue',
            type: VisualType.CARD,
            measure: 'Revenue',
            filter: 'North'
        })
    ]));

    console.log('DATASET STATE:', dataset.state);
    console.log('TOTAL REVENUE:', dataset.totalRevenue().toFixed(2));
    console.log('REGION REVENUE:', dataset.aggregate('region'));
    console.log('CATEGORY QUANTITY:', dataset.aggregate('category', 'Quantity'));

    for (const page of report.pages) {
        console.log(`\nPAGE: ${page.name}`);
        console.log(JSON.stringify(page.render(dataset), null, 2));
    }

    await fs.writeFile(
        'power_bi_report_definition.json',
        JSON.stringify(report.definition(), null, 2),
        'utf8'
    );

    // Demonstrates an explicit data-quality failure.
    try {
        const invalid = new Dataset('Invalid Dataset', [
            new Sale({
                id: 99, date: '2026-01-01', region: 'North',
                product: 'Invalid', category: 'Test',
                quantity: 0, unitPrice: 100, customerId: 999
            })
        ]);

        await invalid.refresh();
    } catch (error) {
        console.log('\nEXPECTED VALIDATION FAILURE:', error.message);
    }
}

main().catch(error => {
    console.error('Application failure:', error.message);
    process.exitCode = 1;
});
