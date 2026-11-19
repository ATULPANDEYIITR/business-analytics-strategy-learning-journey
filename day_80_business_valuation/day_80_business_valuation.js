'use strict';

/*
 * BUSINESS VALUATION ENGINE
 *
 * Focus:
 * - Financial input normalization
 * - DCF valuation
 * - WACC calculation
 * - Terminal value
 * - Trading comparables
 * - Valuation policy evaluation
 * - Event-driven financial model
 * - Sensitivity and scenario analysis
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const EventEmitter = require('node:events');
const assert = require('node:assert/strict');

class ValuationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValuationError';
    }
}

const Scenario = Object.freeze({
    BEAR: 'BEAR',
    BASE: 'BASE',
    BULL: 'BULL'
});

function requirePositive(value, field) {
    if (!Number.isFinite(value) || value <= 0) {
        throw new ValuationError(`${field} must be positive.`);
    }
}

function requireNonNegative(value, field) {
    if (!Number.isFinite(value) || value < 0) {
        throw new ValuationError(`${field} cannot be negative.`);
    }
}

function requireRate(value, field, allowNegative = false) {
    if (!Number.isFinite(value)) {
        throw new ValuationError(`${field} must be finite.`);
    }

    if ((!allowNegative && value < 0) || value >= 1) {
        throw new ValuationError(`${field} must be below 100%.`);
    }
}

class FinancialModel {
    constructor({
        revenue,
        ebit,
        depreciation,
        capex,
        workingCapital,
        taxRate,
        cash,
        debt,
        shares
    }) {
        requirePositive(revenue, 'Revenue');
        requireNonNegative(depreciation, 'Depreciation');
        requireNonNegative(capex, 'Capital expenditure');
        requireNonNegative(cash, 'Cash');
        requireNonNegative(debt, 'Debt');
        requirePositive(shares, 'Shares');
        requireRate(taxRate, 'Tax rate');

        if (!Number.isFinite(ebit)) {
            throw new ValuationError('EBIT must be finite.');
        }

        if (ebit < 0) {
            throw new ValuationError(
                'This model does not recognize tax benefits from losses.'
            );
        }

        this.revenue = revenue;
        this.ebit = ebit;
        this.depreciation = depreciation;
        this.capex = capex;
        this.workingCapital = workingCapital;
        this.taxRate = taxRate;
        this.cash = cash;
        this.debt = debt;
        this.shares = shares;

        Object.freeze(this);
    }
}

class CapitalCost {
    constructor({
        costOfEquity,
        costOfDebt,
        equityWeight,
        debtWeight,
        taxRate
    }) {
        for (const [name, value] of Object.entries({
            costOfEquity,
            costOfDebt
        })) {
            requireRate(value, name);
        }

        if (
            !Number.isFinite(equityWeight) ||
            !Number.isFinite(debtWeight) ||
            equityWeight < 0 ||
            debtWeight < 0
        ) {
            throw new ValuationError('Invalid capital structure weights.');
        }

        if (Math.abs(equityWeight + debtWeight - 1) > 1e-9) {
            throw new ValuationError('Capital weights must sum to 1.');
        }

        requireRate(taxRate, 'Tax rate');

        this.costOfEquity = costOfEquity;
        this.costOfDebt = costOfDebt;
        this.equityWeight = equityWeight;
        this.debtWeight = debtWeight;
        this.taxRate = taxRate;

        Object.freeze(this);
    }

    calculateWACC() {
        return (
            this.equityWeight * this.costOfEquity +
            this.debtWeight * this.costOfDebt * (1 - this.taxRate)
        );
    }
}

class ForecastPlan {
    constructor({
        growth,
        margins,
        taxRate,
        depreciationRate,
        capexRate,
        workingCapitalRate,
        terminalGrowth
    }) {
        if (
            !Array.isArray(growth) ||
            !Array.isArray(margins) ||
            growth.length === 0 ||
            growth.length !== margins.length
        ) {
            throw new ValuationError('Invalid forecast periods.');
        }

        growth.forEach((rate, index) => {
            if (!Number.isFinite(rate) || rate <= -1) {
                throw new ValuationError(
                    `Invalid growth rate at period ${index + 1}.`
                );
            }
        });

        margins.forEach((margin, index) => {
            requireRate(margin, `EBIT margin ${index + 1}`);
        });

        requireRate(taxRate, 'Tax rate');
        requireRate(depreciationRate, 'Depreciation rate');
        requireRate(capexRate, 'Capex rate');
        requireRate(workingCapitalRate, 'Working capital rate');
        requireRate(terminalGrowth, 'Terminal growth');

        this.growth = Object.freeze([...growth]);
        this.margins = Object.freeze([...margins]);
        this.taxRate = taxRate;
        this.depreciationRate = depreciationRate;
        this.capexRate = capexRate;
        this.workingCapitalRate = workingCapitalRate;
        this.terminalGrowth = terminalGrowth;

        Object.freeze(this);
    }
}

class DCFEngine {
    constructor(financials, capital, plan) {
        this.financials = financials;
        this.capital = capital;
        this.plan = plan;

        this.wacc = capital.calculateWACC();

        if (this.wacc <= 0 || this.wacc <= plan.terminalGrowth) {
            throw new ValuationError(
                'WACC must be positive and exceed terminal growth.'
            );
        }
    }

    project() {
        let revenue = this.financials.revenue;

        let previousWorkingCapital =
            revenue * this.plan.workingCapitalRate;

        const periods = [];

        for (let i = 0; i < this.plan.growth.length; i++) {
            revenue *= 1 + this.plan.growth[i];

            const ebit = revenue * this.plan.margins[i];
            const nopat = ebit * (1 - this.plan.taxRate);

            const depreciation =
                revenue * this.plan.depreciationRate;

            const capex = revenue * this.plan.capexRate;

            const currentWorkingCapital =
                revenue * this.plan.workingCapitalRate;

            const changeInWorkingCapital =
                currentWorkingCapital - previousWorkingCapital;

            const fcff =
                nopat +
                depreciation -
                capex -
                changeInWorkingCapital;

            const discountFactor =
                1 / Math.pow(1 + this.wacc, i + 1);

            periods.push(Object.freeze({
                year: i + 1,
                revenue,
                ebit,
                nopat,
                depreciation,
                capex,
                changeInWorkingCapital,
                fcff,
                discountFactor,
                presentValue: fcff * discountFactor
            }));

            previousWorkingCapital = currentWorkingCapital;
        }

        return Object.freeze(periods);
    }

    calculate() {
        const periods = this.project();
        const finalFCFF = periods[periods.length - 1].fcff;

        const terminalValue =
            finalFCFF * (1 + this.plan.terminalGrowth) /
            (this.wacc - this.plan.terminalGrowth);

        const terminalPresentValue =
            terminalValue / Math.pow(1 + this.wacc, periods.length);

        const explicitValue = periods.reduce(
            (total, period) => total + period.presentValue,
            0
        );

        const enterpriseValue = explicitValue + terminalPresentValue;

        const equityValue =
            enterpriseValue + this.financials.cash - this.financials.debt;

        return Object.freeze({
            wacc: this.wacc,
            explicitValue,
            terminalValue,
            terminalPresentValue,
            enterpriseValue,
            equityValue,
            valuePerShare: equityValue / this.financials.shares,
            terminalContribution:
                terminalPresentValue / enterpriseValue,
            periods
        });
    }

    sensitivity(waccChanges, growthChanges) {
        const basePeriods = this.project();
        const finalFCFF = basePeriods[basePeriods.length - 1].fcff;
        const output = [];

        for (const waccChange of waccChanges) {
            const adjustedWACC = this.wacc + waccChange;

            for (const growthChange of growthChanges) {
                const adjustedGrowth =
                    this.plan.terminalGrowth + growthChange;

                if (
                    adjustedWACC <= 0 ||
                    adjustedGrowth < 0 ||
                    adjustedWACC <= adjustedGrowth
                ) {
                    continue;
                }

                const explicit = basePeriods.reduce(
                    (total, period) =>
                        total +
                        period.fcff /
                        Math.pow(1 + adjustedWACC, period.year),
                    0
                );

                const terminal =
                    finalFCFF * (1 + adjustedGrowth) /
                    (adjustedWACC - adjustedGrowth);

                const terminalPV =
                    terminal /
                    Math.pow(1 + adjustedWACC, basePeriods.length);

                output.push({
                    wacc: adjustedWACC,
                    terminalGrowth: adjustedGrowth,
                    enterpriseValue: explicit + terminalPV
                });
            }
        }

        return Object.freeze(output);
    }
}

class ComparableCompany {
    constructor(name, enterpriseValue, revenue, ebitda, netIncome) {
        if (!name || !name.trim()) {
            throw new ValuationError('Company name is required.');
        }

        requirePositive(enterpriseValue, 'Enterprise value');
        requirePositive(revenue, 'Revenue');
        requirePositive(ebitda, 'EBITDA');
        requirePositive(netIncome, 'Net income');

        this.name = name;
        this.enterpriseValue = enterpriseValue;
        this.revenue = revenue;
        this.ebitda = ebitda;
        this.netIncome = netIncome;

        Object.freeze(this);
    }

    get evRevenue() {
        return this.enterpriseValue / this.revenue;
    }

    get evEbitda() {
        return this.enterpriseValue / this.ebitda;
    }

    get peRatio() {
        return this.enterpriseValue / this.netIncome;
    }
}

class ComparableEngine {
    constructor(companies) {
        if (!Array.isArray(companies) || companies.length === 0) {
            throw new ValuationError('Comparable dataset is empty.');
        }

        this.companies = [...companies];
    }

    median(values) {
        const sorted = [...values].sort((a, b) => a - b);
        const middle = Math.floor(sorted.length / 2);

        return sorted.length % 2 === 0
            ? (sorted[middle - 1] + sorted[middle]) / 2
            : sorted[middle];
    }

    calculate() {
        return Object.freeze({
            medianEVRevenue: this.median(
                this.companies.map(company => company.evRevenue)
            ),
            medianEVEbitda: this.median(
                this.companies.map(company => company.evEbitda)
            ),
            medianPE: this.median(
                this.companies.map(company => company.peRatio)
            )
        });
    }

    valueTarget({
        revenue,
        ebitda,
        netIncome,
        cash,
        debt,
        shares
    }) {
        requirePositive(revenue, 'Target revenue');
        requirePositive(ebitda, 'Target EBITDA');
        requirePositive(netIncome, 'Target net income');
        requireNonNegative(cash, 'Cash');
        requireNonNegative(debt, 'Debt');
        requirePositive(shares, 'Shares');

        const multiples = this.calculate();

        const evByEBITDA = ebitda * multiples.medianEVEbitda;
        const evByRevenue = revenue * multiples.medianEVRevenue;

        const peEquityValue = netIncome * multiples.medianPE;

        return Object.freeze({
            evByEBITDA,
            evByRevenue,
            peEquityValue,
            equityByEBITDA: evByEBITDA + cash - debt,
            equityByRevenue: evByRevenue + cash - debt,
            priceByEBITDA: (evByEBITDA + cash - debt) / shares,
            priceByRevenue: (evByRevenue + cash - debt) / shares,
            priceByPE: peEquityValue / shares
        });
    }
}

class ValuationPolicy {
    constructor({
        minimumTerminalContribution = 0,
        maximumTerminalContribution = 0.85,
        maximumWACC = 0.30,
        minimumWACC = 0.01
    } = {}) {
        this.minimumTerminalContribution = minimumTerminalContribution;
        this.maximumTerminalContribution = maximumTerminalContribution;
        this.maximumWACC = maximumWACC;
        this.minimumWACC = minimumWACC;
    }

    evaluate(result) {
        const issues = [];

        if (
            result.terminalContribution >
            this.maximumTerminalContribution
        ) {
            issues.push('Terminal value contribution is too high.');
        }

        if (
            result.terminalContribution <
            this.minimumTerminalContribution
        ) {
            issues.push('Terminal value contribution is below policy.');
        }

        if (result.wacc > this.maximumWACC) {
            issues.push('WACC exceeds the configured maximum.');
        }

        if (result.wacc < this.minimumWACC) {
            issues.push('WACC is below the configured minimum.');
        }

        if (result.equityValue <= 0) {
            issues.push('Calculated equity value is not positive.');
        }

        return Object.freeze({
            eligible: issues.length === 0,
            issues
        });
    }
}

class ValuationEventBus extends EventEmitter {
    publish(eventName, payload) {
        this.emit(eventName, Object.freeze(payload));
    }
}

function getScenario(name) {
    const scenarios = {
        [Scenario.BEAR]: {
            growth: [0.04, 0.035, 0.03, 0.025, 0.02],
            margins: [0.15, 0.15, 0.155, 0.16, 0.16],
            terminalGrowth: 0.02
        },
        [Scenario.BASE]: {
            growth: [0.10, 0.09, 0.08, 0.07, 0.06],
            margins: [0.18, 0.19, 0.20, 0.205, 0.21],
            terminalGrowth: 0.03
        },
        [Scenario.BULL]: {
            growth: [0.16, 0.14, 0.12, 0.10, 0.08],
            margins: [0.20, 0.21, 0.22, 0.23, 0.23],
            terminalGrowth: 0.035
        }
    };

    if (!scenarios[name]) {
        throw new ValuationError(`Unknown scenario: ${name}`);
    }

    return scenarios[name];
}

function formatMoney(value) {
    return value.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function runScenario(name, financials, capital) {
    const assumptions = getScenario(name);

    const plan = new ForecastPlan({
        ...assumptions,
        taxRate: 0.25,
        depreciationRate: 0.04,
        capexRate: 0.055,
        workingCapitalRate: 0.10
    });

    const engine = new DCFEngine(financials, capital, plan);

    return {
        engine,
        result: engine.calculate()
    };
}

function main() {
    console.log('BUSINESS VALUATION ENGINE');
    console.log('Currency: INR millions unless stated otherwise');

    const financials = new FinancialModel({
        revenue: 1000,
        ebit: 180,
        depreciation: 40,
        capex: 55,
        workingCapital: 10,
        taxRate: 0.25,
        cash: 100,
        debt: 300,
        shares: 50
    });

    const capital = new CapitalCost({
        costOfEquity: 0.14,
        costOfDebt: 0.09,
        equityWeight: 0.70,
        debtWeight: 0.30,
        taxRate: 0.25
    });

    const events = new ValuationEventBus();

    events.on('valuation:completed', report => {
        console.log(`\n${report.scenario} valuation completed.`);
        console.log(`Enterprise value: ${formatMoney(report.enterpriseValue)}`);
        console.log(`Equity value: ${formatMoney(report.equityValue)}`);
        console.log(`Value per share: ${formatMoney(report.valuePerShare)}`);
    });

    const policy = new ValuationPolicy({
        maximumTerminalContribution: 0.85
    });

    const scenarioResults = new Map();

    for (const scenario of Object.values(Scenario)) {
        const { engine, result } = runScenario(
            scenario,
            financials,
            capital
        );

        scenarioResults.set(scenario, result);

        events.publish('valuation:completed', {
            scenario,
            ...result
        });

        const decision = policy.evaluate(result);

        console.log(
            'Policy:',
            decision.eligible ? 'PASS' : 'REVIEW REQUIRED'
        );

        for (const issue of decision.issues) {
            console.log(`- ${issue}`);
        }

        if (scenario === Scenario.BASE) {
            console.log('\nBase case forecast');

            for (const period of result.periods) {
                console.log(
                    `Year ${period.year}: Revenue ${formatMoney(period.revenue)}, ` +
                    `FCFF ${formatMoney(period.fcff)}`
                );
            }

            console.log('\nSensitivity analysis');

            const sensitivity = engine.sensitivity(
                [-0.01, 0, 0.01],
                [-0.01, 0, 0.01]
            );

            for (const row of sensitivity) {
                console.log(
                    `WACC ${row.wacc.toFixed(2)}, ` +
                    `Growth ${row.terminalGrowth.toFixed(2)}, ` +
                    `EV ${formatMoney(row.enterpriseValue)}`
                );
            }
        }
    }

    const companies = [
        new ComparableCompany('Alpha Technologies', 1800, 1200, 240, 140),
        new ComparableCompany('Beta Systems', 2100, 1500, 300, 175),
        new ComparableCompany('Gamma Digital', 1650, 1100, 220, 125),
        new ComparableCompany('Delta Software', 2400, 1600, 320, 190)
    ];

    const comparableEngine = new ComparableEngine(companies);
    const multiples = comparableEngine.calculate();

    console.log('\nTRADING COMPARABLES');
    console.log(`Median EV/Revenue: ${multiples.medianEVRevenue.toFixed(2)}x`);
    console.log(`Median EV/EBITDA: ${multiples.medianEVEbitda.toFixed(2)}x`);
    console.log(`Median P/E: ${multiples.medianPE.toFixed(2)}x`);

    const target = comparableEngine.valueTarget({
        revenue: 1000,
        ebitda: 220,
        netIncome: 120,
        cash: 100,
        debt: 300,
        shares: 50
    });

    console.log('\nTARGET COMPANY VALUATION');

    for (const [key, value] of Object.entries(target)) {
        console.log(`${key}: ${formatMoney(value)}`);
    }

    // Financial integrity checks.
    const base = scenarioResults.get(Scenario.BASE);

    assert.ok(base.enterpriseValue > 0);
    assert.ok(base.periods.length === 5);

    assert.ok(
        Math.abs(
            base.equityValue -
            (base.enterpriseValue + financials.cash - financials.debt)
        ) < 1e-8
    );

    console.log('\nAll valuation integrity checks passed.');
}

try {
    main();
} catch (error) {
    console.error(`${error.name}: ${error.message}`);
    process.exitCode = 1;
}
