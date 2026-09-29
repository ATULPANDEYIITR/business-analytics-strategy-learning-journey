"use strict";

/*
 * Excel What-If Analysis
 * Scenario Manager, Goal Seek, and Sensitivity Analysis
 *
 * This file provides a JavaScript implementation of the same core concepts:
 *   - model assumptions and formulas
 *   - named scenarios
 *   - Goal Seek
 *   - one-variable sensitivity
 *   - two-variable sensitivity
 *   - break-even analysis
 *   - DCF sensitivity
 *   - numerical sensitivity
 *   - validation and edge cases
 *
 * It uses only standard JavaScript and can run in Node.js or a browser console.
 */

// -----------------------------------------------------------------------------
// 1. MODEL INPUTS AND OUTPUTS
// -----------------------------------------------------------------------------

class ModelInputs {
    constructor({
        unitsSold = 10000,
        pricePerUnit = 50,
        variableCostPerUnit = 28,
        fixedCosts = 100000,
        taxRate = 0.25,
        initialInvestment = 250000
    } = {}) {
        this.unitsSold = unitsSold;
        this.pricePerUnit = pricePerUnit;
        this.variableCostPerUnit = variableCostPerUnit;
        this.fixedCosts = fixedCosts;
        this.taxRate = taxRate;
        this.initialInvestment = initialInvestment;
    }

    cloneWith(changes = {}) {
        return new ModelInputs({
            unitsSold: changes.unitsSold ?? this.unitsSold,
            pricePerUnit: changes.pricePerUnit ?? this.pricePerUnit,
            variableCostPerUnit:
                changes.variableCostPerUnit ?? this.variableCostPerUnit,
            fixedCosts: changes.fixedCosts ?? this.fixedCosts,
            taxRate: changes.taxRate ?? this.taxRate,
            initialInvestment:
                changes.initialInvestment ?? this.initialInvestment
        });
    }
}

function validateInputs(inputs) {
    if (inputs.unitsSold < 0) {
        throw new Error("Units sold cannot be negative.");
    }

    if (inputs.pricePerUnit < 0) {
        throw new Error("Price per unit cannot be negative.");
    }

    if (inputs.variableCostPerUnit < 0) {
        throw new Error("Variable cost per unit cannot be negative.");
    }

    if (inputs.fixedCosts < 0) {
        throw new Error("Fixed costs cannot be negative.");
    }

    if (inputs.taxRate < 0 || inputs.taxRate > 1) {
        throw new Error("Tax rate must be between 0 and 1.");
    }

    if (inputs.initialInvestment <= 0) {
        throw new Error("Initial investment must be greater than zero.");
    }
}

function calculateModel(inputs) {
    validateInputs(inputs);

    const revenue = inputs.unitsSold * inputs.pricePerUnit;
    const variableCost = inputs.unitsSold * inputs.variableCostPerUnit;
    const grossProfit = revenue - variableCost;
    const operatingProfit = grossProfit - inputs.fixedCosts;

    // Tax is not treated as a negative tax benefit in this simplified model.
    const tax = Math.max(0, operatingProfit * inputs.taxRate);
    const netProfit = operatingProfit - tax;
    const roi = netProfit / inputs.initialInvestment;

    const contributionMargin =
        inputs.pricePerUnit - inputs.variableCostPerUnit;

    const breakEvenUnits =
        contributionMargin > 0
            ? inputs.fixedCosts / contributionMargin
            : null;

    return {
        revenue,
        variableCost,
        grossProfit,
        operatingProfit,
        tax,
        netProfit,
        roi,
        breakEvenUnits
    };
}

function printModel(label, result) {
    console.log(`\n--- ${label} ---`);
    console.log(`Revenue:          $${result.revenue.toFixed(2)}`);
    console.log(`Variable Cost:    $${result.variableCost.toFixed(2)}`);
    console.log(`Gross Profit:     $${result.grossProfit.toFixed(2)}`);
    console.log(`Operating Profit: $${result.operatingProfit.toFixed(2)}`);
    console.log(`Tax:              $${result.tax.toFixed(2)}`);
    console.log(`Net Profit:       $${result.netProfit.toFixed(2)}`);
    console.log(`ROI:              ${(result.roi * 100).toFixed(2)}%`);
    console.log(
        `Break-even Units: ${
            result.breakEvenUnits === null
                ? "Not achievable"
                : result.breakEvenUnits.toFixed(2)
        }`
    );
}


// -----------------------------------------------------------------------------
// 2. SCENARIO MANAGER
// -----------------------------------------------------------------------------

class ScenarioManager {
    constructor(baseInputs) {
        this.baseInputs = baseInputs;
        this.scenarios = new Map();
    }

    addScenario(name, changes) {
        if (!name || !name.trim()) {
            throw new Error("Scenario name cannot be empty.");
        }

        this.scenarios.set(name, {
            name,
            changes: { ...changes }
        });
    }

    evaluate(name) {
        const scenario = this.scenarios.get(name);

        if (!scenario) {
            throw new Error(`Scenario not found: ${name}`);
        }

        const inputs = this.baseInputs.cloneWith(scenario.changes);
        return calculateModel(inputs);
    }

    evaluateAll() {
        const results = new Map();

        for (const name of this.scenarios.keys()) {
            results.set(name, this.evaluate(name));
        }

        return results;
    }
}

function scenarioDemo() {
    console.log("\n================ SCENARIO MANAGER ================");

    const manager = new ScenarioManager(new ModelInputs());

    manager.addScenario("Base", {
        unitsSold: 10000,
        pricePerUnit: 50,
        variableCostPerUnit: 28
    });

    manager.addScenario("Optimistic", {
        unitsSold: 13000,
        pricePerUnit: 55,
        variableCostPerUnit: 26
    });

    manager.addScenario("Conservative", {
        unitsSold: 8000,
        pricePerUnit: 47,
        variableCostPerUnit: 30
    });

    for (const [name, result] of manager.evaluateAll()) {
        printModel(name, result);
    }
}


// -----------------------------------------------------------------------------
// 3. GOAL SEEK
// -----------------------------------------------------------------------------

function goalSeek(
    functionToSolve,
    target,
    lower,
    upper,
    tolerance = 1e-8,
    maxIterations = 200
) {
    if (lower >= upper) {
        throw new Error("Lower bound must be less than upper bound.");
    }

    let lowerValue = functionToSolve(lower) - target;
    let upperValue = functionToSolve(upper) - target;

    if (Math.abs(lowerValue) <= tolerance) {
        return lower;
    }

    if (Math.abs(upperValue) <= tolerance) {
        return upper;
    }

    // Bisection requires the target to lie between the endpoint values.
    if (lowerValue * upperValue > 0) {
        throw new Error(
            "Goal cannot be bracketed by the supplied lower and upper bounds."
        );
    }

    let low = lower;
    let high = upper;

    for (let iteration = 0; iteration < maxIterations; iteration++) {
        const midpoint = (low + high) / 2;
        const midpointValue = functionToSolve(midpoint) - target;

        if (Math.abs(midpointValue) <= tolerance) {
            return midpoint;
        }

        if (lowerValue * midpointValue <= 0) {
            high = midpoint;
            upperValue = midpointValue;
        } else {
            low = midpoint;
            lowerValue = midpointValue;
        }

        if (Math.abs(high - low) <= tolerance) {
            return (low + high) / 2;
        }
    }

    return (low + high) / 2;
}

function goalSeekDemo() {
    console.log("\n================ GOAL SEEK ================");

    const base = new ModelInputs();
    const targetProfit = 100000;

    const profitFromUnits = (units) => {
        const candidate = base.cloneWith({ unitsSold: units });
        return calculateModel(candidate).netProfit;
    };

    const requiredUnits = goalSeek(
        profitFromUnits,
        targetProfit,
        0,
        100000
    );

    console.log(`Target net profit: $${targetProfit.toFixed(2)}`);
    console.log(`Required units:    ${requiredUnits.toFixed(2)}`);
    console.log(
        `Resulting profit:  $${profitFromUnits(requiredUnits).toFixed(2)}`
    );
}

function priceGoalSeekDemo() {
    console.log("\n================ PRICE GOAL SEEK ================");

    const base = new ModelInputs();
    const targetROI = 0.40;

    const roiFromPrice = (price) => {
        const candidate = base.cloneWith({ pricePerUnit: price });
        return calculateModel(candidate).roi;
    };

    const requiredPrice = goalSeek(
        roiFromPrice,
        targetROI,
        base.variableCostPerUnit + 0.01,
        200
    );

    console.log(`Target ROI:    ${(targetROI * 100).toFixed(2)}%`);
    console.log(`Required price: $${requiredPrice.toFixed(2)}`);
    console.log(
        `Resulting ROI:  ${(roiFromPrice(requiredPrice) * 100).toFixed(2)}%`
    );
}


// -----------------------------------------------------------------------------
// 4. ONE-VARIABLE SENSITIVITY
// -----------------------------------------------------------------------------

function oneVariableSensitivity(
    baseInputs,
    propertyName,
    values,
    outputSelector
) {
    if (!(propertyName in baseInputs)) {
        throw new Error(`Unknown input: ${propertyName}`);
    }

    return values.map((value) => {
        const candidate = baseInputs.cloneWith({
            [propertyName]: value
        });

        const output = outputSelector(calculateModel(candidate));

        return {
            input: value,
            output
        };
    });
}

function oneVariableSensitivityDemo() {
    console.log("\n================ ONE-VARIABLE SENSITIVITY ================");

    const base = new ModelInputs();

    const results = oneVariableSensitivity(
        base,
        "pricePerUnit",
        [40, 45, 50, 55, 60, 65],
        (result) => result.netProfit
    );

    for (const row of results) {
        console.log(
            `Price $${row.input.toFixed(2)} -> ` +
            `Net Profit $${row.output.toFixed(2)}`
        );
    }
}


// -----------------------------------------------------------------------------
// 5. TWO-VARIABLE SENSITIVITY
// -----------------------------------------------------------------------------

function twoVariableSensitivity(
    baseInputs,
    rowProperty,
    rowValues,
    columnProperty,
    columnValues,
    outputSelector
) {
    if (!(rowProperty in baseInputs)) {
        throw new Error(`Unknown row input: ${rowProperty}`);
    }

    if (!(columnProperty in baseInputs)) {
        throw new Error(`Unknown column input: ${columnProperty}`);
    }

    if (rowProperty === columnProperty) {
        throw new Error("Row and column inputs must be different.");
    }

    return rowValues.map((rowValue) => {
        return columnValues.map((columnValue) => {
            const candidate = baseInputs.cloneWith({
                [rowProperty]: rowValue,
                [columnProperty]: columnValue
            });

            return outputSelector(calculateModel(candidate));
        });
    });
}

function twoVariableSensitivityDemo() {
    console.log("\n================ TWO-VARIABLE SENSITIVITY ================");

    const base = new ModelInputs();

    const units = [7500, 10000, 12500, 15000];
    const prices = [45, 50, 55, 60];

    const matrix = twoVariableSensitivity(
        base,
        "unitsSold",
        units,
        "pricePerUnit",
        prices,
        (result) => result.netProfit
    );

    console.log("Rows = units sold; columns = price.");

    console.table(
        matrix.map((row, index) => ({
            unitsSold: units[index],
            "$45": row[0],
            "$50": row[1],
            "$55": row[2],
            "$60": row[3]
        }))
    );
}


// -----------------------------------------------------------------------------
// 6. PERCENTAGE CHANGE AND ELASTICITY
// -----------------------------------------------------------------------------

function percentChange(oldValue, newValue) {
    if (oldValue === 0) {
        return null;
    }

    return (newValue - oldValue) / Math.abs(oldValue);
}

function elasticity(
    baseInput,
    changedInput,
    baseOutput,
    changedOutput
) {
    const inputChange = percentChange(baseInput, changedInput);
    const outputChange = percentChange(baseOutput, changedOutput);

    if (
        inputChange === null ||
        inputChange === 0 ||
        outputChange === null
    ) {
        return null;
    }

    return outputChange / inputChange;
}

function elasticityDemo() {
    console.log("\n================ SENSITIVITY METRICS ================");

    const base = new ModelInputs();
    const changed = base.cloneWith({ unitsSold: 11000 });

    const baseOutput = calculateModel(base);
    const changedOutput = calculateModel(changed);

    const result = elasticity(
        base.unitsSold,
        changed.unitsSold,
        baseOutput.netProfit,
        changedOutput.netProfit
    );

    console.log(
        `Units change:  ${(percentChange(
            base.unitsSold,
            changed.unitsSold
        ) * 100).toFixed(2)}%`
    );

    console.log(
        `Profit change: ${(percentChange(
            baseOutput.netProfit,
            changedOutput.netProfit
        ) * 100).toFixed(2)}%`
    );

    console.log(`Elasticity:    ${result.toFixed(4)}`);
}


// -----------------------------------------------------------------------------
// 7. DISCOUNTED CASH FLOW
// -----------------------------------------------------------------------------

function presentValue(cashFlow, discountRate, period) {
    if (discountRate <= -1) {
        throw new Error("Discount rate must be greater than -100%.");
    }

    return cashFlow / Math.pow(1 + discountRate, period);
}

function npv(cashFlows, discountRate) {
    return cashFlows.reduce(
        (total, cashFlow, period) =>
            total + presentValue(cashFlow, discountRate, period),
        0
    );
}

function dcfSensitivityDemo() {
    console.log("\n================ DCF SENSITIVITY ================");

    const cashFlows = [-250000, 80000, 100000, 120000, 140000];

    for (const rate of [0.06, 0.08, 0.10, 0.12, 0.14]) {
        console.log(
            `${(rate * 100).toFixed(0)}% discount rate -> ` +
            `NPV $${npv(cashFlows, rate).toFixed(2)}`
        );
    }
}


// -----------------------------------------------------------------------------
// 8. NUMERICAL DERIVATIVE
// -----------------------------------------------------------------------------

function numericalDerivative(fn, x, step = 1e-5) {
    if (step <= 0) {
        throw new Error("Step must be positive.");
    }

    return (fn(x + step) - fn(x - step)) / (2 * step);
}

function numericalDerivativeDemo() {
    console.log("\n================ NUMERICAL SENSITIVITY ================");

    const base = new ModelInputs();

    const profitFromPrice = (price) => {
        return calculateModel(
            base.cloneWith({ pricePerUnit: price })
        ).netProfit;
    };

    const derivative = numericalDerivative(
        profitFromPrice,
        base.pricePerUnit,
        0.01
    );

    console.log(
        `Approximate profit increase per $1 price change: ` +
        `$${derivative.toFixed(2)}`
    );
}


// -----------------------------------------------------------------------------
// 9. BREAK-EVEN ANALYSIS
// -----------------------------------------------------------------------------

function breakEvenDemo() {
    console.log("\n================ BREAK-EVEN ================");

    const result = calculateModel(new ModelInputs());

    console.log(
        result.breakEvenUnits === null
            ? "Break-even is not achievable."
            : `Break-even units: ${result.breakEvenUnits.toFixed(2)}`
    );
}


// -----------------------------------------------------------------------------
// 10. EDGE CASES AND VALIDATION
// -----------------------------------------------------------------------------

function edgeCaseDemo() {
    console.log("\n================ EDGE CASES ================");

    const zeroSales = calculateModel(
        new ModelInputs({ unitsSold: 0 })
    );

    console.log(
        `Zero sales net profit: $${zeroSales.netProfit.toFixed(2)}`
    );

    const zeroMargin = calculateModel(
        new ModelInputs({
            pricePerUnit: 30,
            variableCostPerUnit: 30
        })
    );

    console.log(
        `Zero-margin break-even: ${zeroMargin.breakEvenUnits}`
    );

    try {
        calculateModel(new ModelInputs({ taxRate: 1.5 }));
    } catch (error) {
        console.log(`Validation correctly rejected input: ${error.message}`);
    }

    try {
        goalSeek(
            (x) => x * x,
            10,
            1,
            2
        );
    } catch (error) {
        console.log(`Goal Seek correctly rejected range: ${error.message}`);
    }
}


// -----------------------------------------------------------------------------
// 11. SCENARIO GRID
// -----------------------------------------------------------------------------

function scenarioGridDemo() {
    console.log("\n================ SCENARIO GRID ================");

    const base = new ModelInputs();
    const unitMultipliers = [0.8, 0.9, 1.0, 1.1, 1.2];
    const priceMultipliers = [0.9, 0.95, 1.0, 1.05, 1.1];

    const profits = [];

    for (const unitMultiplier of unitMultipliers) {
        for (const priceMultiplier of priceMultipliers) {
            const candidate = base.cloneWith({
                unitsSold: base.unitsSold * unitMultiplier,
                pricePerUnit: base.pricePerUnit * priceMultiplier
            });

            profits.push(calculateModel(candidate).netProfit);
        }
    }

    const profitable = profits.filter((profit) => profit > 0).length;

    console.log(`Grid combinations: ${profits.length}`);
    console.log(`Minimum profit: $${Math.min(...profits).toFixed(2)}`);
    console.log(`Maximum profit: $${Math.max(...profits).toFixed(2)}`);
    console.log(`Profitable cases: ${profitable}/${profits.length}`);
}


// -----------------------------------------------------------------------------
// 12. MAIN EXECUTION
// -----------------------------------------------------------------------------

function main() {
    console.log("========================================================");
    console.log("EXCEL WHAT-IF ANALYSIS");
    console.log("Scenario Manager | Goal Seek | Sensitivity Analysis");
    console.log("========================================================");

    printModel(
        "BASE CASE",
        calculateModel(new ModelInputs())
    );

    scenarioDemo();
    goalSeekDemo();
    priceGoalSeekDemo();
    oneVariableSensitivityDemo();
    twoVariableSensitivityDemo();
    elasticityDemo();
    dcfSensitivityDemo();
    numericalDerivativeDemo();
    breakEvenDemo();
    edgeCaseDemo();
    scenarioGridDemo();

    console.log("\nStudy implementation completed successfully.");
}

main();
