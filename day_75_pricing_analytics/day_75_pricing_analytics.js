"use strict";

/**
 * Pricing Analytics
 * Pricing structures, elasticity and optimization.
 *
 * Runtime: Node.js 18+
 *
 * Features:
 * - Strategy-based pricing
 * - Segmented demand models
 * - Asynchronous market data processing
 * - Competitor benchmarking
 * - Price optimization
 * - Revenue and contribution analysis
 * - Pricing policy evaluation
 * - Event-driven price recommendation workflow
 */

const EventEmitter = require("node:events");
const fs = require("node:fs/promises");

class PricingError extends Error {
    constructor(message) {
        super(message);
        this.name = "PricingError";
    }
}

const Strategy = Object.freeze({
    COST_PLUS: "COST_PLUS",
    VALUE_BASED: "VALUE_BASED",
    COMPETITIVE: "COMPETITIVE",
    PENETRATION: "PENETRATION",
    PREMIUM: "PREMIUM",
    DYNAMIC: "DYNAMIC"
});

const Objective = Object.freeze({
    PROFIT: "PROFIT",
    REVENUE: "REVENUE"
});

class Product {
    constructor({
        id,
        name,
        cost,
        referencePrice,
        minPrice,
        maxPrice,
        inventory
    }) {
        if (!id || !name) {
            throw new PricingError("Product identity is required.");
        }

        const values = [
            cost,
            referencePrice,
            minPrice,
            maxPrice,
            inventory
        ];

        if (!values.every(Number.isFinite)) {
            throw new PricingError("All product values must be finite.");
        }

        if (
            cost < 0 ||
            referencePrice <= 0 ||
            minPrice <= cost ||
            maxPrice < minPrice ||
            inventory < 0 ||
            !Number.isInteger(inventory)
        ) {
            throw new PricingError("Invalid product configuration.");
        }

        Object.assign(this, {
            id,
            name,
            cost,
            referencePrice,
            minPrice,
            maxPrice,
            inventory
        });

        Object.freeze(this);
    }
}

class SegmentDemandModel {
    constructor({
        segment,
        basePrice,
        baseDemand,
        elasticity,
        crossPriceCoefficient = 0
    }) {
        if (
            !segment ||
            basePrice <= 0 ||
            baseDemand < 0 ||
            elasticity >= 0 ||
            !Number.isFinite(elasticity) ||
            !Number.isFinite(crossPriceCoefficient)
        ) {
            throw new PricingError("Invalid segment demand parameters.");
        }

        this.segment = segment;
        this.basePrice = basePrice;
        this.baseDemand = baseDemand;
        this.elasticity = elasticity;
        this.crossPriceCoefficient = crossPriceCoefficient;
    }

    forecast(price, competitorPrice = this.basePrice) {
        if (price <= 0 || competitorPrice <= 0) {
            throw new PricingError("Prices must be positive.");
        }

        const ownPriceEffect =
            Math.pow(price / this.basePrice, this.elasticity);

        const competitiveEffect = Math.pow(
            competitorPrice / this.basePrice,
            this.crossPriceCoefficient
        );

        return this.baseDemand * ownPriceEffect * competitiveEffect;
    }
}

class PricePolicy {
    constructor({
        minimumMargin = 0,
        maximumDiscount = 0.30,
        requireCompetitorData = false,
        allowedStrategies = Object.values(Strategy)
    } = {}) {
        if (
            minimumMargin < 0 ||
            minimumMargin >= 1 ||
            maximumDiscount < 0 ||
            maximumDiscount >= 1
        ) {
            throw new PricingError("Invalid pricing policy.");
        }

        this.minimumMargin = minimumMargin;
        this.maximumDiscount = maximumDiscount;
        this.requireCompetitorData = requireCompetitorData;
        this.allowedStrategies = new Set(allowedStrategies);
    }

    evaluate(product, price, strategy, competitorPrice = null) {
        const violations = [];

        if (!this.allowedStrategies.has(strategy)) {
            violations.push("Strategy is not authorized.");
        }

        if (
            price < product.minPrice ||
            price > product.maxPrice
        ) {
            violations.push("Price violates product boundaries.");
        }

        const margin = (price - product.cost) / price;

        if (margin < this.minimumMargin) {
            violations.push("Minimum margin requirement not met.");
        }

        if (
            price < product.referencePrice * (1 - this.maximumDiscount)
        ) {
            violations.push("Maximum discount exceeded.");
        }

        if (
            this.requireCompetitorData &&
            competitorPrice === null
        ) {
            violations.push("Competitor information is required.");
        }

        return {
            accepted: violations.length === 0,
            violations,
            margin
        };
    }
}

class PricingEngine extends EventEmitter {
    constructor(product, models, policy) {
        super();

        if (!models.length) {
            throw new PricingError("At least one demand model is required.");
        }

        this.product = product;
        this.models = new Map();

        for (const model of models) {
            if (this.models.has(model.segment)) {
                throw new PricingError("Duplicate customer segment.");
            }

            this.models.set(model.segment, model);
        }

        this.policy = policy;
        this.recommendationHistory = [];
    }

    forecast(price, competitorPrice = this.product.referencePrice) {
        let demand = 0;

        for (const model of this.models.values()) {
            demand += model.forecast(price, competitorPrice);
        }

        return Math.min(demand, this.product.inventory);
    }

    calculate(price, competitorPrice = this.product.referencePrice) {
        const demand = this.forecast(price, competitorPrice);
        const revenue = price * demand;
        const variableCost = this.product.cost * demand;
        const profit = revenue - variableCost;

        return {
            price: Number(price.toFixed(2)),
            demand,
            revenue,
            variableCost,
            profit,
            margin: revenue > 0 ? profit / revenue : 0
        };
    }

    optimize({
        objective = Objective.PROFIT,
        step = 1,
        competitorPrice = null
    } = {}) {
        if (!Object.values(Objective).includes(objective)) {
            throw new PricingError("Unsupported optimization objective.");
        }

        if (!Number.isFinite(step) || step <= 0) {
            throw new PricingError("Search step must be positive.");
        }

        const referenceCompetitor =
            competitorPrice ?? this.product.referencePrice;

        if (referenceCompetitor <= 0) {
            throw new PricingError("Invalid competitor price.");
        }

        let best = null;

        for (
            let price = this.product.minPrice;
            price <= this.product.maxPrice + 1e-9;
            price += step
        ) {
            const evaluation = this.policy.evaluate(
                this.product,
                price,
                Strategy.DYNAMIC,
                competitorPrice
            );

            if (!evaluation.accepted) continue;

            const metrics = this.calculate(price, referenceCompetitor);

            const score =
                objective === Objective.PROFIT
                    ? metrics.profit
                    : metrics.revenue;

            if (
                best === null ||
                score > best.score ||
                (score === best.score && price > best.price)
            ) {
                best = {
                    ...metrics,
                    score,
                    strategy: Strategy.DYNAMIC,
                    objective
                };
            }
        }

        if (!best) {
            throw new PricingError(
                "No candidate satisfies the pricing policy."
            );
        }

        this.recommendationHistory.push(best);
        this.emit("priceRecommended", best);

        return best;
    }

    async optimizeScenarios(scenarios) {
        return Promise.all(
            scenarios.map(async scenario => {
                await new Promise(resolve => setImmediate(resolve));

                return {
                    scenario: scenario.name,
                    result: this.optimize(scenario)
                };
            })
        );
    }

    async exportRecommendations(filename) {
        const records = this.recommendationHistory;

        if (!records.length) {
            throw new PricingError("No recommendations available.");
        }

        const headers = [
            "price",
            "demand",
            "revenue",
            "variableCost",
            "profit",
            "margin",
            "objective"
        ];

        const escape = value =>
            `"${String(value).replaceAll('"', '""')}"`;

        const lines = [
            headers.join(","),
            ...records.map(record =>
                headers.map(key => escape(record[key] ?? "")).join(",")
            )
        ];

        await fs.writeFile(
            filename,
            lines.join("\n") + "\n",
            { encoding: "utf8", flag: "w" }
        );
    }
}

class CompetitorAnalyzer {
    static benchmark(prices) {
        if (!Array.isArray(prices) || prices.length === 0) {
            throw new PricingError("Competitor prices are required.");
        }

        if (!prices.every(
            item => Number.isFinite(item.price) && item.price > 0
        )) {
            throw new PricingError("Invalid competitor price.");
        }

        const sorted = prices.map(item => item.price).sort((a, b) => a - b);

        const median = sorted.length % 2
            ? sorted[Math.floor(sorted.length / 2)]
            : (
                sorted[sorted.length / 2 - 1] +
                sorted[sorted.length / 2]
            ) / 2;

        return {
            minimum: sorted[0],
            maximum: sorted[sorted.length - 1],
            average: sorted.reduce((a, b) => a + b, 0) / sorted.length,
            median
        };
    }
}

function estimateElasticity(observations) {
    const data = observations.filter(
        item =>
            item.price > 0 &&
            item.quantity > 0 &&
            Number.isFinite(item.price) &&
            Number.isFinite(item.quantity)
    );

    if (data.length < 3) {
        throw new PricingError("Three valid observations are required.");
    }

    const x = data.map(item => Math.log(item.price));
    const y = data.map(item => Math.log(item.quantity));

    const mean = values =>
        values.reduce((sum, value) => sum + value, 0) / values.length;

    const mx = mean(x);
    const my = mean(y);

    const denominator = x.reduce(
        (sum, value) => sum + (value - mx) ** 2,
        0
    );

    if (denominator === 0) {
        throw new PricingError("Insufficient price variation.");
    }

    const elasticity = x.reduce(
        (sum, value, index) =>
            sum + (value - mx) * (y[index] - my),
        0
    ) / denominator;

    if (elasticity >= 0) {
        throw new PricingError(
            "Estimated demand relationship is not negatively elastic."
        );
    }

    return elasticity;
}

async function main() {
    const product = new Product({
        id: "SUB-100",
        name: "Enterprise Software Subscription",
        cost: 200,
        referencePrice: 500,
        minPrice: 300,
        maxPrice: 900,
        inventory: 1000
    });

    const observations = [
        { price: 400, quantity: 150 },
        { price: 450, quantity: 130 },
        { price: 500, quantity: 115 },
        { price: 550, quantity: 105 },
        { price: 600, quantity: 94 },
        { price: 650, quantity: 86 }
    ];

    const elasticity = estimateElasticity(observations);

    console.log("Estimated elasticity:", elasticity.toFixed(4));

    const models = [
        new SegmentDemandModel({
            segment: "SMB",
            basePrice: 500,
            baseDemand: 70,
            elasticity: -1.4
        }),
        new SegmentDemandModel({
            segment: "ENTERPRISE",
            basePrice: 500,
            baseDemand: 45,
            elasticity: -0.8
        })
    ];

    const policy = new PricePolicy({
        minimumMargin: 0.20,
        maximumDiscount: 0.40,
        requireCompetitorData: true
    });

    const engine = new PricingEngine(product, models, policy);

    engine.on("priceRecommended", recommendation => {
        console.log(
            `Recommendation event: ${recommendation.price}, ` +
            `profit=${recommendation.profit.toFixed(2)}`
        );
    });

    const competitors = [
        { name: "Market A", price: 520 },
        { name: "Market B", price: 540 },
        { name: "Market C", price: 560 }
    ];

    const benchmark = CompetitorAnalyzer.benchmark(competitors);

    console.log("Competitor benchmark:", benchmark);

    const scenarios = await engine.optimizeScenarios([
        {
            name: "Profit maximization",
            objective: Objective.PROFIT,
            step: 5,
            competitorPrice: benchmark.average
        },
        {
            name: "Revenue maximization",
            objective: Objective.REVENUE,
            step: 5,
            competitorPrice: benchmark.average
        }
    ]);

    for (const scenario of scenarios) {
        console.log(
            scenario.scenario,
            JSON.stringify(scenario.result, null, 2)
        );
    }

    await engine.exportRecommendations("pricing_recommendations.csv");

    console.log("Recommendations exported.");

    // Validate inventory and pricing boundaries.
    for (const scenario of scenarios) {
        const result = scenario.result;

        if (result.demand > product.inventory) {
            throw new Error("Inventory constraint violated.");
        }

        if (
            result.price < product.minPrice ||
            result.price > product.maxPrice
        ) {
            throw new Error("Price boundary violated.");
        }
    }

    console.log("All pricing validations passed.");
}

main().catch(error => {
    console.error("Pricing execution failed:", error.message);
    process.exitCode = 1;
});
