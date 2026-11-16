'use strict';

/**
 * Cost Analytics and Cost Optimization Engine
 *
 * Node.js 18+
 *
 * Focus:
 * - Event-driven cost monitoring
 * - Cost classification
 * - Cost centre aggregation
 * - Budget control
 * - Unit economics
 * - Optimization policy evaluation
 * - Scenario comparison
 * - Asynchronous reporting
 * - Audit events
 */

const fs = require('node:fs/promises');
const path = require('node:path');
const { EventEmitter } = require('node:events');
const { randomUUID } = require('node:crypto');


class CostError extends Error {
    constructor(message, code = 'COST_ERROR') {
        super(message);
        this.name = 'CostError';
        this.code = code;
    }
}


const CostType = Object.freeze({
    FIXED: 'fixed',
    VARIABLE: 'variable',
    SEMI_VARIABLE: 'semi_variable'
});

const CostBehavior = Object.freeze({
    DIRECT: 'direct',
    INDIRECT: 'indirect'
});

const Categories = Object.freeze([
    'labor',
    'materials',
    'technology',
    'facilities',
    'logistics',
    'administration'
]);


function validateMoney(value, field) {
    if (!Number.isFinite(value) || value < 0) {
        throw new CostError(
            `${field} must be a finite non-negative number.`,
            'INVALID_MONEY'
        );
    }
}


function validateText(value, field) {
    if (typeof value !== 'string' || value.trim().length === 0) {
        throw new CostError(`${field} is required.`, 'INVALID_TEXT');
    }
}


class CostRecord {
    constructor(data) {
        validateText(data.costCenter, 'Cost centre');
        validateText(data.period, 'Period');
        validateText(data.description, 'Description');

        validateMoney(data.amount, 'Amount');
        validateMoney(data.activityUnits, 'Activity units');

        if (!Categories.includes(data.category)) {
            throw new CostError('Invalid cost category.');
        }

        if (!Object.values(CostType).includes(data.costType)) {
            throw new CostError('Invalid cost type.');
        }

        if (!Object.values(CostBehavior).includes(data.behavior)) {
            throw new CostError('Invalid cost behavior.');
        }

        this.id = data.id || randomUUID();
        this.costCenter = data.costCenter;
        this.period = data.period;
        this.category = data.category;
        this.costType = data.costType;
        this.behavior = data.behavior;
        this.amount = data.amount;
        this.activityUnits = data.activityUnits;
        this.description = data.description;

        Object.freeze(this);
    }
}


class Budget {
    constructor(costCenter, period, amount) {
        validateText(costCenter, 'Cost centre');
        validateText(period, 'Period');
        validateMoney(amount, 'Budget');

        this.costCenter = costCenter;
        this.period = period;
        this.amount = amount;

        Object.freeze(this);
    }
}


class CostLedger extends EventEmitter {
    #records = new Map();
    #revision = 0;

    get revision() {
        return this.#revision;
    }

    add(data) {
        const record = data instanceof CostRecord
            ? data
            : new CostRecord(data);

        if (this.#records.has(record.id)) {
            throw new CostError(
                `Duplicate cost record: ${record.id}`,
                'DUPLICATE_RECORD'
            );
        }

        this.#records.set(record.id, record);
        this.#revision++;

        this.emit('recordAdded', {
            recordId: record.id,
            revision: this.#revision,
            amount: record.amount
        });

        return record;
    }

    find({ period, costCenter } = {}) {
        return Array.from(this.#records.values()).filter(record => {
            return (!period || record.period === period)
                && (!costCenter || record.costCenter === costCenter);
        });
    }

    total(records = this.#records.values()) {
        return Array.from(records).reduce(
            (sum, record) => sum + record.amount,
            0
        );
    }

    snapshot() {
        return Object.freeze({
            revision: this.#revision,
            records: Object.freeze(
                Array.from(this.#records.values())
            )
        });
    }
}


class CostAnalytics {
    constructor(ledger) {
        this.ledger = ledger;
    }

    classify(period) {
        const result = {
            fixed: 0,
            variable: 0,
            semi_variable: 0,
            direct: 0,
            indirect: 0,
            categories: new Map()
        };

        for (const record of this.ledger.find({ period })) {
            result[record.costType] += record.amount;
            result[record.behavior] += record.amount;

            result.categories.set(
                record.category,
                (result.categories.get(record.category) || 0)
                    + record.amount
            );
        }

        return result;
    }

    costCenters(period) {
        const totals = new Map();

        for (const record of this.ledger.find({ period })) {
            totals.set(
                record.costCenter,
                (totals.get(record.costCenter) || 0) + record.amount
            );
        }

        return totals;
    }

    unitEconomics(period) {
        const records = this.ledger.find({ period });
        const cost = this.ledger.total(records);

        const units = records.reduce(
            (sum, record) => sum + record.activityUnits,
            0
        );

        if (units <= 0) {
            throw new CostError('Activity volume must be positive.');
        }

        return {
            totalCost: cost,
            activityUnits: units,
            unitCost: cost / units
        };
    }

    contributionAnalysis({
        sellingPrice,
        variableCost,
        fixedCost
    }) {
        validateMoney(sellingPrice, 'Selling price');
        validateMoney(variableCost, 'Variable cost');
        validateMoney(fixedCost, 'Fixed cost');

        if (sellingPrice <= variableCost) {
            throw new CostError(
                'Selling price must exceed variable cost.'
            );
        }

        const contribution = sellingPrice - variableCost;

        return {
            contribution,
            contributionMargin: contribution / sellingPrice,
            breakEvenUnits: Math.ceil(fixedCost / contribution),
            breakEvenRevenue: (
                Math.ceil(fixedCost / contribution) * sellingPrice
            )
        };
    }

    variance(budget, actual) {
        validateMoney(actual, 'Actual expenditure');

        const difference = budget.amount - actual;

        return {
            budget: budget.amount,
            actual,
            variance: difference,
            variancePercent: budget.amount === 0
                ? null
                : difference / budget.amount * 100,
            status: difference >= 0 ? 'UNDER_BUDGET' : 'OVER_BUDGET'
        };
    }

    allocateIndirectCosts(period) {
        const records = this.ledger.find({ period });

        const direct = new Map();
        let indirectTotal = 0;

        for (const record of records) {
            if (record.behavior === CostBehavior.DIRECT) {
                direct.set(
                    record.costCenter,
                    (direct.get(record.costCenter) || 0) + record.amount
                );
            } else {
                indirectTotal += record.amount;
            }
        }

        const base = Array.from(direct.values()).reduce(
            (sum, amount) => sum + amount,
            0
        );

        if (base === 0 && indirectTotal > 0) {
            throw new CostError(
                'No direct-cost allocation base exists.'
            );
        }

        return new Map(
            Array.from(direct.entries()).map(([center, amount]) => {
                const allocated = base === 0
                    ? 0
                    : indirectTotal * amount / base;

                return [
                    center,
                    {
                        directCost: amount,
                        allocatedIndirect: allocated,
                        totalCost: amount + allocated
                    }
                ];
            })
        );
    }
}


class OptimizationPolicy {
    constructor({
        maximumRisk = 5,
        minimumNetSavings = 0,
        minimumReduction = 0.01
    } = {}) {
        if (
            !Number.isFinite(maximumRisk)
            || maximumRisk < 0
            || maximumRisk > 10
        ) {
            throw new CostError('Invalid risk threshold.');
        }

        validateMoney(minimumNetSavings, 'Minimum savings');

        if (
            !Number.isFinite(minimumReduction)
            || minimumReduction < 0
            || minimumReduction > 1
        ) {
            throw new CostError('Invalid minimum reduction.');
        }

        this.maximumRisk = maximumRisk;
        this.minimumNetSavings = minimumNetSavings;
        this.minimumReduction = minimumReduction;

        Object.freeze(this);
    }
}


class OptimizationEngine {
    constructor(ledger, policy = new OptimizationPolicy()) {
        this.ledger = ledger;
        this.policy = policy;
    }

    evaluate(period, proposals) {
        const categoryTotals = new Map();

        for (const record of this.ledger.find({ period })) {
            categoryTotals.set(
                record.category,
                (categoryTotals.get(record.category) || 0)
                    + record.amount
            );
        }

        const results = proposals.map(proposal => {
            validateText(proposal.name, 'Proposal name');
            validateMoney(proposal.implementationCost, 'Implementation cost');

            if (!Categories.includes(proposal.category)) {
                throw new CostError('Invalid optimization category.');
            }

            if (
                !Number.isFinite(proposal.reductionRate)
                || proposal.reductionRate < 0
                || proposal.reductionRate > 1
            ) {
                throw new CostError('Invalid reduction rate.');
            }

            if (
                !Number.isFinite(proposal.risk)
                || proposal.risk < 0
                || proposal.risk > 10
            ) {
                throw new CostError('Invalid proposal risk.');
            }

            const baseline = categoryTotals.get(proposal.category) || 0;
            const grossSavings = baseline * proposal.reductionRate;
            const netSavings = grossSavings - proposal.implementationCost;

            const eligible = (
                baseline > 0
                && proposal.risk <= this.policy.maximumRisk
                && proposal.reductionRate >= this.policy.minimumReduction
                && netSavings >= this.policy.minimumNetSavings
            );

            return {
                name: proposal.name,
                baseline,
                grossSavings,
                implementationCost: proposal.implementationCost,
                netSavings,
                eligible,
                rejectionReason: eligible
                    ? null
                    : baseline === 0
                        ? 'No baseline expenditure'
                        : proposal.risk > this.policy.maximumRisk
                            ? 'Risk threshold exceeded'
                            : proposal.reductionRate < this.policy.minimumReduction
                                ? 'Reduction below policy threshold'
                                : 'Net savings below policy threshold'
            };
        });

        return {
            period,
            results,
            selected: results.filter(item => item.eligible),
            totalGrossSavings: results
                .filter(item => item.eligible)
                .reduce((sum, item) => sum + item.grossSavings, 0),
            totalImplementationCost: results
                .filter(item => item.eligible)
                .reduce((sum, item) => sum + item.implementationCost, 0),
            totalNetSavings: results
                .filter(item => item.eligible)
                .reduce((sum, item) => sum + item.netSavings, 0)
        };
    }
}


class ReportService {
    constructor(ledger, analytics) {
        this.ledger = ledger;
        this.analytics = analytics;
    }

    async exportJSON(destination, period) {
        const snapshot = this.ledger.snapshot();

        const report = {
            generatedAt: new Date().toISOString(),
            period,
            revision: snapshot.revision,
            totalCost: this.ledger.total(
                snapshot.records.filter(record => record.period === period)
            ),
            unitEconomics: this.analytics.unitEconomics(period),
            costCenters: Object.fromEntries(
                this.analytics.costCenters(period)
            ),
            classifications: {
                ...this.analytics.classify(period),
                categories: Object.fromEntries(
                    this.analytics.classify(period).categories
                )
            }
        };

        const absolutePath = path.resolve(destination);
        const temporary = `${absolutePath}.${randomUUID()}.tmp`;

        try {
            await fs.mkdir(path.dirname(absolutePath), {
                recursive: true
            });

            await fs.writeFile(
                temporary,
                JSON.stringify(report, null, 2),
                {
                    encoding: 'utf8',
                    flag: 'wx',
                    mode: 0o600
                }
            );

            await fs.rename(temporary, absolutePath);
            return report;
        } catch (error) {
            await fs.rm(temporary, { force: true }).catch(() => {});
            throw new CostError(
                `Report export failed: ${error.message}`,
                'EXPORT_FAILED'
            );
        }
    }
}


function createSampleLedger() {
    const ledger = new CostLedger();

    ledger.on('recordAdded', event => {
        console.log(
            `[AUDIT] Record ${event.recordId} added; revision ${event.revision}`
        );
    });

    const records = [
        {
            costCenter: 'PRODUCTION',
            category: 'labor',
            costType: CostType.FIXED,
            behavior: CostBehavior.DIRECT,
            amount: 120000,
            activityUnits: 1000,
            period: '2026-10',
            description: 'Production workforce'
        },
        {
            costCenter: 'PRODUCTION',
            category: 'materials',
            costType: CostType.VARIABLE,
            behavior: CostBehavior.DIRECT,
            amount: 180000,
            activityUnits: 1000,
            period: '2026-10',
            description: 'Raw material consumption'
        },
        {
            costCenter: 'PRODUCTION',
            category: 'facilities',
            costType: CostType.FIXED,
            behavior: CostBehavior.INDIRECT,
            amount: 45000,
            activityUnits: 1000,
            period: '2026-10',
            description: 'Facility expenses'
        },
        {
            costCenter: 'TECHNOLOGY',
            category: 'technology',
            costType: CostType.SEMI_VARIABLE,
            behavior: CostBehavior.INDIRECT,
            amount: 60000,
            activityUnits: 1000,
            period: '2026-10',
            description: 'Cloud services'
        },
        {
            costCenter: 'LOGISTICS',
            category: 'logistics',
            costType: CostType.VARIABLE,
            behavior: CostBehavior.DIRECT,
            amount: 35000,
            activityUnits: 1000,
            period: '2026-10',
            description: 'Distribution expenses'
        }
    ];

    for (const record of records) {
        ledger.add(record);
    }

    return ledger;
}


async function main() {
    const ledger = createSampleLedger();
    const analytics = new CostAnalytics(ledger);

    console.log('\nCOST ANALYTICS ENGINE');
    console.log('==============================');

    const period = '2026-10';

    console.log('\nClassification:');
    const classification = analytics.classify(period);

    console.log({
        fixed: classification.fixed,
        variable: classification.variable,
        semiVariable: classification.semi_variable,
        direct: classification.direct,
        indirect: classification.indirect,
        categories: Object.fromEntries(classification.categories)
    });

    console.log('\nCost centres:');
    console.log(Object.fromEntries(analytics.costCenters(period)));

    console.log('\nUnit economics:');
    console.log(analytics.unitEconomics(period));

    console.log('\nBreak-even:');
    console.log(analytics.contributionAnalysis({
        fixedCost: 150000,
        sellingPrice: 500,
        variableCost: 300
    }));

    console.log('\nBudget variance:');
    console.log(
        analytics.variance(
            new Budget('PRODUCTION', period, 350000),
            345000
        )
    );

    console.log('\nIndirect allocation:');
    console.log(
        Object.fromEntries(analytics.allocateIndirectCosts(period))
    );

    const optimizer = new OptimizationEngine(
        ledger,
        new OptimizationPolicy({
            maximumRisk: 5,
            minimumNetSavings: 1000,
            minimumReduction: 0.05
        })
    );

    const optimization = optimizer.evaluate(period, [
        {
            name: 'Cloud capacity rightsizing',
            category: 'technology',
            reductionRate: 0.20,
            implementationCost: 3000,
            risk: 2
        },
        {
            name: 'Procurement consolidation',
            category: 'materials',
            reductionRate: 0.08,
            implementationCost: 5000,
            risk: 3
        },
        {
            name: 'Logistics route optimization',
            category: 'logistics',
            reductionRate: 0.15,
            implementationCost: 2000,
            risk: 4
        },
        {
            name: 'High-risk workforce reduction',
            category: 'labor',
            reductionRate: 0.10,
            implementationCost: 1000,
            risk: 9
        }
    ]);

    console.log('\nOptimization decisions:');
    console.log(JSON.stringify(optimization, null, 2));

    const reporter = new ReportService(ledger, analytics);

    const report = await reporter.exportJSON(
        './output/cost-analytics-report.json',
        period
    );

    console.log('\nReport exported.');
    console.log(`Total expenditure: Rs. ${report.totalCost.toFixed(2)}`);

    // Edge-case validation.
    try {
        analytics.unitEconomics('UNKNOWN_PERIOD');
    } catch (error) {
        console.log(`Expected validation: ${error.message}`);
    }
}


main().catch(error => {
    console.error('Application failure:', error.message);
    process.exitCode = 1;
});
