"use strict";

/*
 * FINANCIAL RATIOS
 * Profitability, liquidity, leverage and efficiency analysis.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 */

const fs = require("node:fs/promises");
const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

const RatioCategory = Object.freeze({
    PROFITABILITY: "Profitability",
    LIQUIDITY: "Liquidity",
    LEVERAGE: "Leverage",
    EFFICIENCY: "Efficiency"
});

class FinancialDataError extends Error {
    constructor(message) {
        super(message);
        this.name = "FinancialDataError";
    }
}

class FinancialData {
    constructor(data) {
        this.company = data.company;
        this.period = data.period;

        this.revenue = data.revenue;
        this.costOfGoodsSold = data.costOfGoodsSold;
        this.operatingExpenses = data.operatingExpenses;
        this.operatingIncome = data.operatingIncome;
        this.netIncome = data.netIncome;

        this.totalAssets = data.totalAssets;
        this.currentAssets = data.currentAssets;
        this.inventory = data.inventory;
        this.cash = data.cash;
        this.accountsReceivable = data.accountsReceivable;

        this.totalLiabilities = data.totalLiabilities;
        this.currentLiabilities = data.currentLiabilities;
        this.totalDebt = data.totalDebt;
        this.shareholdersEquity = data.shareholdersEquity;

        this.interestExpense = data.interestExpense;
        this.inventoryBeginning = data.inventoryBeginning;
        this.inventoryEnding = data.inventoryEnding;
        this.receivablesBeginning = data.receivablesBeginning;
        this.receivablesEnding = data.receivablesEnding;

        this.validate();
    }

    validate() {
        if (typeof this.company !== "string" ||
            this.company.trim() === "") {
            throw new FinancialDataError(
                "Company name is required."
            );
        }

        if (typeof this.period !== "string" ||
            this.period.trim() === "") {
            throw new FinancialDataError(
                "Financial period is required."
            );
        }

        const numericFields = Object.keys(this)
            .filter(key =>
                key !== "company" && key !== "period"
            );

        for (const field of numericFields) {
            const value = this[field];

            if (!Number.isFinite(value) || value < 0) {
                throw new FinancialDataError(
                    `Invalid financial value: ${field}`
                );
            }
        }

        if (this.currentAssets > this.totalAssets) {
            throw new FinancialDataError(
                "Current assets exceed total assets."
            );
        }

        if (this.cash > this.currentAssets) {
            throw new FinancialDataError(
                "Cash exceeds current assets."
            );
        }

        if (this.inventory > this.currentAssets) {
            throw new FinancialDataError(
                "Inventory exceeds current assets."
            );
        }

        if (this.currentLiabilities > this.totalLiabilities) {
            throw new FinancialDataError(
                "Current liabilities exceed total liabilities."
            );
        }

        if (this.totalDebt > this.totalLiabilities) {
            throw new FinancialDataError(
                "Total debt exceeds total liabilities."
            );
        }
    }
}

class RatioCalculator {
    static divide(numerator, denominator) {
        if (denominator === 0) {
            return null;
        }

        return numerator / denominator;
    }

    static calculate(
        name,
        category,
        numerator,
        denominator,
        unit,
        interpretation
    ) {
        const value = this.divide(numerator, denominator);

        return Object.freeze({
            id: crypto.randomUUID(),
            name,
            category,
            value,
            unit,
            interpretation,
            warning: value === null
                ? "Undefined because denominator is zero."
                : null
        });
    }
}

class FinancialRatioEngine extends EventEmitter {
    constructor(financialData) {
        super();

        if (!(financialData instanceof FinancialData)) {
            throw new TypeError(
                "Expected a FinancialData instance."
            );
        }

        this.data = financialData;
        this.results = new Map();
        this.state = "READY";
    }

    addRatio(result) {
        if (this.results.has(result.name)) {
            throw new Error(
                `Duplicate ratio: ${result.name}`
            );
        }

        this.results.set(result.name, result);

        this.emit("ratioCalculated", result);
    }

    profitability() {
        const d = this.data;
        const grossProfit =
            d.revenue - d.costOfGoodsSold;

        return [
            RatioCalculator.calculate(
                "Gross Profit Margin",
                RatioCategory.PROFITABILITY,
                grossProfit,
                d.revenue,
                "%",
                "Profit remaining after direct production costs."
            ),

            RatioCalculator.calculate(
                "Operating Profit Margin",
                RatioCategory.PROFITABILITY,
                d.operatingIncome,
                d.revenue,
                "%",
                "Operating income relative to revenue."
            ),

            RatioCalculator.calculate(
                "Net Profit Margin",
                RatioCategory.PROFITABILITY,
                d.netIncome,
                d.revenue,
                "%",
                "Net profit relative to revenue."
            ),

            RatioCalculator.calculate(
                "Return on Assets",
                RatioCategory.PROFITABILITY,
                d.netIncome,
                d.totalAssets,
                "%",
                "Profitability relative to total assets."
            ),

            RatioCalculator.calculate(
                "Return on Equity",
                RatioCategory.PROFITABILITY,
                d.netIncome,
                d.shareholdersEquity,
                "%",
                "Profitability relative to shareholders' equity."
            )
        ];
    }

    liquidity() {
        const d = this.data;

        return [
            RatioCalculator.calculate(
                "Current Ratio",
                RatioCategory.LIQUIDITY,
                d.currentAssets,
                d.currentLiabilities,
                "x",
                "Short-term asset coverage."
            ),

            RatioCalculator.calculate(
                "Quick Ratio",
                RatioCategory.LIQUIDITY,
                d.currentAssets - d.inventory,
                d.currentLiabilities,
                "x",
                "Liquid asset coverage excluding inventory."
            ),

            RatioCalculator.calculate(
                "Cash Ratio",
                RatioCategory.LIQUIDITY,
                d.cash,
                d.currentLiabilities,
                "x",
                "Immediate cash coverage."
            )
        ];
    }

    leverage() {
        const d = this.data;

        return [
            RatioCalculator.calculate(
                "Debt-to-Equity Ratio",
                RatioCategory.LEVERAGE,
                d.totalDebt,
                d.shareholdersEquity,
                "x",
                "Debt relative to shareholders' equity."
            ),

            RatioCalculator.calculate(
                "Debt-to-Assets Ratio",
                RatioCategory.LEVERAGE,
                d.totalDebt,
                d.totalAssets,
                "%",
                "Asset financing provided by debt."
            ),

            RatioCalculator.calculate(
                "Debt Ratio",
                RatioCategory.LEVERAGE,
                d.totalLiabilities,
                d.totalAssets,
                "%",
                "Asset financing provided by liabilities."
            ),

            RatioCalculator.calculate(
                "Interest Coverage Ratio",
                RatioCategory.LEVERAGE,
                d.operatingIncome,
                d.interestExpense,
                "x",
                "Operating income available for interest payments."
            )
        ];
    }

    efficiency() {
        const d = this.data;

        const averageInventory =
            (d.inventoryBeginning + d.inventoryEnding) / 2;

        const averageReceivables =
            (d.receivablesBeginning + d.receivablesEnding) / 2;

        return [
            RatioCalculator.calculate(
                "Inventory Turnover",
                RatioCategory.EFFICIENCY,
                d.costOfGoodsSold,
                averageInventory,
                "x",
                "Inventory replacement frequency."
            ),

            RatioCalculator.calculate(
                "Receivables Turnover",
                RatioCategory.EFFICIENCY,
                d.revenue,
                averageReceivables,
                "x",
                "Receivables collection efficiency."
            ),

            RatioCalculator.calculate(
                "Total Asset Turnover",
                RatioCategory.EFFICIENCY,
                d.revenue,
                d.totalAssets,
                "x",
                "Revenue generated per unit of assets."
            ),

            RatioCalculator.calculate(
                "Days Sales Outstanding",
                RatioCategory.EFFICIENCY,
                averageReceivables * 365,
                d.revenue,
                "days",
                "Estimated receivables collection period."
            ),

            RatioCalculator.calculate(
                "Days Inventory Outstanding",
                RatioCategory.EFFICIENCY,
                averageInventory * 365,
                d.costOfGoodsSold,
                "days",
                "Estimated inventory holding period."
            )
        ];
    }

    async analyze() {
        if (this.state === "RUNNING") {
            throw new Error("Analysis is already running.");
        }

        this.state = "RUNNING";
        this.results.clear();

        this.emit("analysisStarted", {
            company: this.data.company,
            period: this.data.period
        });

        try {
            const stages = [
                this.profitability(),
                this.liquidity(),
                this.leverage(),
                this.efficiency()
            ];

            for (const stage of stages) {
                // Yield between categories to support event-driven consumers.
                await new Promise(resolve => setImmediate(resolve));

                for (const result of stage) {
                    this.addRatio(result);
                }
            }

            this.state = "COMPLETED";

            const report = this.report();

            this.emit("analysisCompleted", report);

            return report;
        } catch (error) {
            this.state = "FAILED";

            this.emit("analysisFailed", error);

            throw error;
        }
    }

    report() {
        const categories = Object.values(RatioCategory);

        const grouped = Object.fromEntries(
            categories.map(category => [
                category,
                [...this.results.values()].filter(
                    result => result.category === category
                )
            ])
        );

        return Object.freeze({
            company: this.data.company,
            period: this.data.period,
            generatedAt: new Date().toISOString(),
            state: this.state,
            categories: grouped
        });
    }

    async exportJSON(filename) {
        const report = this.report();

        // Write to a temporary file before replacing the destination.
        const temporaryFile = `${filename}.tmp`;

        try {
            await fs.writeFile(
                temporaryFile,
                JSON.stringify(report, null, 2),
                { encoding: "utf8", mode: 0o600 }
            );

            await fs.rename(temporaryFile, filename);
        } catch (error) {
            await fs.rm(temporaryFile, { force: true })
                .catch(() => {});

            throw new Error(
                `Report export failed: ${error.message}`
            );
        }
    }
}

function createSampleData() {
    return new FinancialData({
        company: "Apex Manufacturing Ltd.",
        period: "FY2025-26",

        revenue: 12000000,
        costOfGoodsSold: 7200000,
        operatingExpenses: 2400000,
        operatingIncome: 2400000,
        netIncome: 1500000,

        totalAssets: 10000000,
        currentAssets: 4000000,
        inventory: 1200000,
        cash: 800000,
        accountsReceivable: 1000000,

        totalLiabilities: 5000000,
        currentLiabilities: 2000000,
        totalDebt: 3000000,
        shareholdersEquity: 5000000,

        interestExpense: 400000,
        inventoryBeginning: 1000000,
        inventoryEnding: 1200000,
        receivablesBeginning: 800000,
        receivablesEnding: 1000000
    });
}

async function runTests() {
    const engine = new FinancialRatioEngine(createSampleData());

    const events = [];

    engine.on("ratioCalculated", result => {
        events.push(result.name);
    });

    const report = await engine.analyze();

    const findRatio = name =>
        report.categories[
            Object.values(RatioCategory).find(category =>
                report.categories[category].some(
                    ratio => ratio.name === name
                )
            )
        ].find(ratio => ratio.name === name);

    console.assert(
        Math.abs(findRatio("Current Ratio").value - 2) < 1e-9
    );

    console.assert(
        Math.abs(findRatio("Quick Ratio").value - 1.4) < 1e-9
    );

    console.assert(
        Math.abs(findRatio("Gross Profit Margin").value - 0.4) < 1e-9
    );

    console.assert(events.length === 17);

    const invalid = {
        ...createSampleData(),
        revenue: -100
    };

    try {
        new FinancialData(invalid);
        throw new Error("Negative revenue was accepted.");
    } catch (error) {
        if (!(error instanceof FinancialDataError)) {
            throw error;
        }
    }

    const zeroDenominator = RatioCalculator.calculate(
        "Test Ratio",
        RatioCategory.LIQUIDITY,
        100,
        0,
        "x",
        "Zero denominator test."
    );

    console.assert(zeroDenominator.value === null);

    console.log("All JavaScript tests passed.");
}

async function main() {
    try {
        const engine = new FinancialRatioEngine(
            createSampleData()
        );

        engine.on("ratioCalculated", result => {
            console.log(
                `[${result.category}] ${result.name}:`,
                result.value === null
                    ? "N/A"
                    : `${result.value.toFixed(4)} ${result.unit}`
            );
        });

        engine.on("analysisFailed", error => {
            console.error("Analysis event:", error.message);
        });

        const report = await engine.analyze();

        await engine.exportJSON("financial_ratios.json");

        console.log("\nAnalysis completed:", report.state);
        console.log("Report exported.");

        await runTests();
    } catch (error) {
        console.error("Financial analysis failed:", error.message);
        process.exitCode = 1;
    }
}

if (require.main === module) {
    main();
}

module.exports = {
    FinancialData,
    FinancialDataError,
    RatioCalculator,
    FinancialRatioEngine,
    RatioCategory
};
