"use strict";

/*
 * BREAK-EVEN ANALYSIS AND FINANCIAL SCENARIO ENGINE
 *
 * Node.js 18+
 *
 * Features:
 * - Event-driven financial analysis
 * - Fixed and variable cost classification
 * - Contribution margin calculations
 * - Break-even and target-profit evaluation
 * - Multi-product sales-mix analysis
 * - Scenario simulation
 * - Policy-based profitability alerts
 * - Asynchronous scenario execution
 * - Input validation and structured errors
 */

const EventEmitter = require("node:events");

class FinancialError extends Error {
    constructor(message, code = "FINANCIAL_ERROR") {
        super(message);
        this.name = "FinancialError";
        this.code = code;
    }
}

const CostType = Object.freeze({
    FIXED: "FIXED",
    VARIABLE: "VARIABLE"
});

function validateNumber(value, name, minimum = 0) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < minimum
    ) {
        throw new FinancialError(
            `${name} must be a finite number >= ${minimum}`,
            "INVALID_INPUT"
        );
    }
}

class CostLedger {
    #items = new Map();

    add(name, amount, type) {
        if (!name || typeof name !== "string" || !name.trim()) {
            throw new FinancialError("Cost name is required.");
        }

        validateNumber(amount, "Cost amount");

        if (!Object.values(CostType).includes(type)) {
            throw new FinancialError("Invalid cost classification.");
        }

        if (this.#items.has(name)) {
            throw new FinancialError(`Duplicate cost: ${name}`);
        }

        this.#items.set(name, Object.freeze({
            name,
            amount,
            type
        }));
    }

    totals() {
        const result = {
            fixed: 0,
            variable: 0
        };

        for (const item of this.#items.values()) {
            if (item.type === CostType.FIXED) {
                result.fixed += item.amount;
            } else {
                result.variable += item.amount;
            }
        }

        return Object.freeze(result);
    }

    get items() {
        return Array.from(this.#items.values());
    }
}

class BreakEvenEngine extends EventEmitter {
    constructor({ sellingPrice, variableCost, fixedCosts }) {
        super();

        validateNumber(sellingPrice, "Selling price");
        validateNumber(variableCost, "Variable cost");
        validateNumber(fixedCosts, "Fixed costs");

        if (sellingPrice === 0) {
            throw new FinancialError("Selling price must be positive.");
        }

        if (sellingPrice <= variableCost) {
            throw new FinancialError(
                "Selling price must exceed variable cost.",
                "NON_POSITIVE_CONTRIBUTION"
            );
        }

        this.sellingPrice = sellingPrice;
        this.variableCost = variableCost;
        this.fixedCosts = fixedCosts;

        this.contribution = sellingPrice - variableCost;
        this.marginRatio = this.contribution / sellingPrice;
    }

    calculate(units, targetProfit = 0) {
        validateNumber(units, "Sales units");
        validateNumber(targetProfit, "Target profit");

        const revenue = units * this.sellingPrice;
        const totalVariable = units * this.variableCost;
        const totalCost = this.fixedCosts + totalVariable;
        const profit = revenue - totalCost;

        const exactBreakEven = this.fixedCosts / this.contribution;

        const result = Object.freeze({
            units,
            revenue,
            totalVariable,
            fixedCosts: this.fixedCosts,
            totalCost,
            profit,
            contributionPerUnit: this.contribution,
            contributionMarginRatio: this.marginRatio,
            breakEvenUnits: exactBreakEven,
            practicalBreakEvenUnits: Math.ceil(exactBreakEven),
            breakEvenRevenue: this.fixedCosts / this.marginRatio,
            targetProfit,
            targetProfitUnits: Math.ceil(
                (this.fixedCosts + targetProfit) / this.contribution
            ),
            marginOfSafetyUnits: units - exactBreakEven,
            marginOfSafetyRatio: units > 0
                ? (units - exactBreakEven) / units
                : null
        });

        this.emit("calculated", result);

        return result;
    }

    operatingLeverage(units) {
        const result = this.calculate(units);

        if (result.profit <= 0) {
            return null;
        }

        return (
            units * this.contribution / result.profit
        );
    }

    evaluatePolicy(result, policy) {
        if (
            !policy ||
            !Number.isFinite(policy.minimumMarginOfSafety) ||
            policy.minimumMarginOfSafety < 0 ||
            policy.minimumMarginOfSafety > 1
        ) {
            throw new FinancialError("Invalid profitability policy.");
        }

        const alerts = [];

        if (result.profit < 0) {
            alerts.push("OPERATING_LOSS");
        }

        if (
            result.marginOfSafetyRatio === null ||
            result.marginOfSafetyRatio < policy.minimumMarginOfSafety
        ) {
            alerts.push("LOW_MARGIN_OF_SAFETY");
        }

        if (result.profit === 0) {
            alerts.push("BREAK_EVEN_OPERATIONS");
        }

        const decision = Object.freeze({
            approved: alerts.length === 0,
            alerts
        });

        this.emit("policyEvaluated", decision);

        return decision;
    }

    sensitivity(priceChanges, costChanges) {
        if (!Array.isArray(priceChanges) || !Array.isArray(costChanges)) {
            throw new FinancialError("Sensitivity inputs must be arrays.");
        }

        const scenarios = [];

        for (const priceChange of priceChanges) {
            validateNumber(
                priceChange + 1,
                "Price multiplier",
                0.000001
            );

            for (const costChange of costChanges) {
                validateNumber(
                    costChange + 1,
                    "Cost multiplier",
                    0.000001
                );

                const price = this.sellingPrice * (1 + priceChange);
                const cost = this.variableCost * (1 + costChange);

                try {
                    const engine = new BreakEvenEngine({
                        sellingPrice: price,
                        variableCost: cost,
                        fixedCosts: this.fixedCosts
                    });

                    scenarios.push({
                        priceChange,
                        costChange,
                        breakEvenUnits:
                            engine.calculate(0).breakEvenUnits
                    });
                } catch (error) {
                    scenarios.push({
                        priceChange,
                        costChange,
                        error: error.message
                    });
                }
            }
        }

        return scenarios;
    }
}

class ProductPortfolio {
    #products = new Map();

    add(product) {
        const {
            name,
            sellingPrice,
            variableCost,
            salesMix
        } = product;

        if (!name || typeof name !== "string") {
            throw new FinancialError("Product name is required.");
        }

        validateNumber(sellingPrice, "Selling price", 0.000001);
        validateNumber(variableCost, "Variable cost");
        validateNumber(salesMix, "Sales mix", 0.000001);

        if (variableCost >= sellingPrice) {
            throw new FinancialError(
                `Product ${name} has non-positive contribution.`
            );
        }

        if (this.#products.has(name)) {
            throw new FinancialError(`Duplicate product: ${name}`);
        }

        this.#products.set(name, Object.freeze({
            name,
            sellingPrice,
            variableCost,
            salesMix
        }));
    }

    weightedContribution() {
        const products = Array.from(this.#products.values());

        if (products.length === 0) {
            throw new FinancialError("Product portfolio is empty.");
        }

        const totalMix = products.reduce(
            (sum, p) => sum + p.salesMix,
            0
        );

        return products.reduce(
            (sum, p) => (
                sum +
                (p.salesMix / totalMix) *
                (p.sellingPrice - p.variableCost)
            ),
            0
        );
    }

    breakEven(fixedCosts) {
        validateNumber(fixedCosts, "Fixed costs");

        return fixedCosts / this.weightedContribution();
    }

    allocation(fixedCosts) {
        const products = Array.from(this.#products.values());
        const totalMix = products.reduce(
            (sum, p) => sum + p.salesMix,
            0
        );

        const weightedMargin = this.weightedContribution();
        const totalUnits = fixedCosts / weightedMargin;

        return products.map(p => {
            const mix = p.salesMix / totalMix;

            return {
                product: p.name,
                normalizedMix: mix,
                breakEvenUnits: totalUnits * mix,
                contribution: p.sellingPrice - p.variableCost
            };
        });
    }
}

async function executeScenarios(engine, salesLevels) {
    if (!Array.isArray(salesLevels)) {
        throw new FinancialError("Sales levels must be an array.");
    }

    // Promise.all allows independent scenario calculations to run together.
    return Promise.all(
        salesLevels.map(async units => {
            await Promise.resolve();
            return engine.calculate(units);
        })
    );
}

async function main() {
    console.log("=".repeat(65));
    console.log("BREAK-EVEN ANALYSIS ENGINE");
    console.log("=".repeat(65));

    const ledger = new CostLedger();

    ledger.add("Factory Rent", 80000, CostType.FIXED);
    ledger.add("Salaries", 120000, CostType.FIXED);
    ledger.add("Insurance", 20000, CostType.FIXED);

    ledger.add("Raw Materials", 250, CostType.VARIABLE);
    ledger.add("Packaging", 50, CostType.VARIABLE);
    ledger.add("Direct Labour", 100, CostType.VARIABLE);

    const totals = ledger.totals();

    console.log("\nCOST CLASSIFICATION");
    console.log(totals);

    const engine = new BreakEvenEngine({
        sellingPrice: 1000,
        variableCost: 400,
        fixedCosts: totals.fixed
    });

    engine.on("calculated", result => {
        console.log(
            `Analysis completed for ${result.units} units.`
        );
    });

    engine.on("policyEvaluated", decision => {
        console.log(
            `Policy evaluation: ${decision.approved ? "PASS" : "FAIL"}`
        );
    });

    console.log("\nUNIT ECONOMICS");
    console.log({
        contribution: engine.contribution,
        marginRatio: engine.marginRatio
    });

    console.log("\nBREAK-EVEN ANALYSIS");

    const base = engine.calculate(600, 200000);
    console.log(base);

    console.log("\nPROFITABILITY POLICY");

    const policy = engine.evaluatePolicy(base, {
        minimumMarginOfSafety: 0.15
    });

    console.log(policy);

    console.log("\nOPERATING LEVERAGE");
    console.log(engine.operatingLeverage(600));

    console.log("\nASYNC SALES SCENARIOS");

    const scenarios = await executeScenarios(
        engine,
        [200, 300, 367, 400, 600, 1000]
    );

    for (const scenario of scenarios) {
        console.log({
            units: scenario.units,
            profit: scenario.profit,
            marginOfSafety: scenario.marginOfSafetyUnits
        });
    }

    console.log("\nMULTI-PRODUCT PORTFOLIO");

    const portfolio = new ProductPortfolio();

    portfolio.add({
        name: "Standard",
        sellingPrice: 1000,
        variableCost: 400,
        salesMix: 60
    });

    portfolio.add({
        name: "Premium",
        sellingPrice: 1500,
        variableCost: 650,
        salesMix: 40
    });

    console.log(
        "Weighted contribution:",
        portfolio.weightedContribution()
    );

    console.log(
        "Weighted break-even units:",
        portfolio.breakEven(220000)
    );

    console.log(
        "Product allocation:",
        portfolio.allocation(220000)
    );

    console.log("\nSENSITIVITY ANALYSIS");

    console.log(
        engine.sensitivity(
            [-0.10, 0, 0.10],
            [-0.10, 0, 0.10]
        )
    );

    console.log("\nVALIDATION");

    try {
        new BreakEvenEngine({
            sellingPrice: 100,
            variableCost: 100,
            fixedCosts: 500
        });
    } catch (error) {
        console.log("Expected rejection:", error.code);
    }

    try {
        engine.calculate(-5);
    } catch (error) {
        console.log("Expected rejection:", error.message);
    }

    const assertions = engine.calculate(600);

    if (assertions.profit !== 140000) {
        throw new Error("Profit calculation assertion failed.");
    }

    if (assertions.practicalBreakEvenUnits !== 367) {
        throw new Error("Break-even assertion failed.");
    }

    console.log("All assertions passed.");
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
