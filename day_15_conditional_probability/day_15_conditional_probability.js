/*
 * Conditional Probability for Business Decisions Under Uncertainty
 * =================================================================
 *
 * Self-contained JavaScript study program.
 * Run with:
 *     node conditional_probability_business.js
 *
 * The examples progress from basic probability through Bayes' theorem,
 * decision analysis, simulation, classification metrics, A/B testing,
 * and an event-driven business decision dashboard.
 */

"use strict";

// ---------------------------------------------------------------------------
// 1. BASIC UTILITIES
// ---------------------------------------------------------------------------

function section(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function subsection(title) {
    console.log("\n" + "-".repeat(78));
    console.log(title);
    console.log("-".repeat(78));
}

function percentage(value) {
    return `${(value * 100).toFixed(2)}%`;
}

function probability(eventCount, totalCount) {
    if (!Number.isFinite(eventCount) || !Number.isFinite(totalCount)) {
        throw new TypeError("Counts must be finite numbers.");
    }

    if (totalCount <= 0) {
        throw new RangeError("Total count must be positive.");
    }

    if (eventCount < 0 || eventCount > totalCount) {
        throw new RangeError("Event count must be between 0 and total count.");
    }

    return eventCount / totalCount;
}

function conditionalProbability(jointCount, conditionCount) {
    if (conditionCount <= 0) {
        throw new RangeError("The conditioning event must have positive count.");
    }

    if (jointCount < 0 || jointCount > conditionCount) {
        throw new RangeError(
            "Joint count must be between zero and conditioning count."
        );
    }

    return jointCount / conditionCount;
}

function assertAlmostEqual(actual, expected, tolerance = 1e-10) {
    if (Math.abs(actual - expected) > tolerance) {
        throw new Error(`Expected ${expected}, received ${actual}.`);
    }
}


// ---------------------------------------------------------------------------
// 2. BASIC PROBABILITY
// ---------------------------------------------------------------------------

section("1. Probability fundamentals");

const visitors = 10000;
const purchases = 1800;
const purchaseRate = probability(purchases, visitors);

console.log(`Observed purchase rate: ${percentage(purchaseRate)}`);


// ---------------------------------------------------------------------------
// 3. CONDITIONAL PROBABILITY
// ---------------------------------------------------------------------------

section("2. Conditional probability");

const mobileCustomers = 6000;
const mobilePurchases = 1500;

const pMobile = probability(mobileCustomers, visitors);
const pMobileAndPurchase = probability(mobilePurchases, visitors);
const pPurchaseGivenMobile =
    pMobileAndPurchase / pMobile;

console.log(`P(Mobile): ${percentage(pMobile)}`);
console.log(`P(Mobile and Purchase): ${percentage(pMobileAndPurchase)}`);
console.log(`P(Purchase | Mobile): ${percentage(pPurchaseGivenMobile)}`);


// ---------------------------------------------------------------------------
// 4. REVERSE CONDITIONAL PROBABILITY
// ---------------------------------------------------------------------------

section("3. P(A | B) versus P(B | A)");

const total = 10000;
const mobile = 6000;
const purchase = 2000;
const mobilePurchase = 1200;

const pPurchase = purchase / total;
const pMobileGivenPurchase = mobilePurchase / purchase;
const pPurchaseGivenMobile2 = mobilePurchase / mobile;

console.log(`P(Mobile | Purchase): ${percentage(pMobileGivenPurchase)}`);
console.log(`P(Purchase | Mobile): ${percentage(pPurchaseGivenMobile2)}`);


// ---------------------------------------------------------------------------
// 5. BAYES' THEOREM
// ---------------------------------------------------------------------------

section("4. Bayes' theorem");

function bayes({
    prior,
    likelihoodGivenCondition,
    likelihoodGivenNotCondition
}) {
    if (prior < 0 || prior > 1) {
        throw new RangeError("Prior probability must be between 0 and 1.");
    }

    const likelihoodOfEvidence =
        likelihoodGivenCondition * prior +
        likelihoodGivenNotCondition * (1 - prior);

    if (likelihoodOfEvidence === 0) {
        throw new RangeError(
            "Evidence has zero probability under the supplied model."
        );
    }

    return (
        likelihoodGivenCondition * prior /
        likelihoodOfEvidence
    );
}

const fraudPosterior = bayes({
    prior: 0.01,
    likelihoodGivenCondition: 0.95,
    likelihoodGivenNotCondition: 0.05
});

console.log(`P(Fraud | Flag): ${percentage(fraudPosterior)}`);


// ---------------------------------------------------------------------------
// 6. LAW OF TOTAL PROBABILITY
// ---------------------------------------------------------------------------

section("5. Law of total probability");

const regions = [
    { name: "North", share: 0.25, conversion: 0.12 },
    { name: "South", share: 0.35, conversion: 0.08 },
    { name: "East", share: 0.20, conversion: 0.15 },
    { name: "West", share: 0.20, conversion: 0.10 }
];

const totalConversion = regions.reduce(
    (sum, region) =>
        sum + region.share * region.conversion,
    0
);

console.log(`Overall conversion: ${percentage(totalConversion)}`);


// ---------------------------------------------------------------------------
// 7. INDEPENDENCE
// ---------------------------------------------------------------------------

section("6. Independence");

const pAdvertisement = 0.20;
const pWeekend = 0.30;
const observedJoint = 0.06;
const expectedJointIfIndependent =
    pAdvertisement * pWeekend;

console.log(
    `Expected joint probability: ${percentage(expectedJointIfIndependent)}`
);
console.log(
    `Observed joint probability: ${percentage(observedJoint)}`
);
console.log(
    `Independent: ${
        Math.abs(observedJoint - expectedJointIfIndependent) < 1e-12
    }`
);


// ---------------------------------------------------------------------------
// 8. BINOMIAL PROBABILITY
// ---------------------------------------------------------------------------

section("7. Binomial probability");

function factorial(n) {
    if (!Number.isInteger(n) || n < 0) {
        throw new RangeError("Factorial requires a non-negative integer.");
    }

    let result = 1;

    for (let i = 2; i <= n; i++) {
        result *= i;
    }

    return result;
}

function combination(n, k) {
    if (!Number.isInteger(n) || !Number.isInteger(k)) {
        throw new TypeError("n and k must be integers.");
    }

    if (n < 0 || k < 0 || k > n) {
        throw new RangeError("Require n >= 0 and 0 <= k <= n.");
    }

    return factorial(n) / (
        factorial(k) * factorial(n - k)
    );
}

function binomialProbability(n, k, p) {
    if (p < 0 || p > 1) {
        throw new RangeError("p must be between 0 and 1.");
    }

    return (
        combination(n, k) *
        p ** k *
        (1 - p) ** (n - k)
    );
}

console.log(
    `P(exactly 3 successes in 10): ${
        percentage(binomialProbability(10, 3, 0.20))
    }`
);

console.log(
    `P(at least one success): ${
        percentage(1 - binomialProbability(10, 0, 0.20))
    }`
);


// ---------------------------------------------------------------------------
// 9. BUSINESS FUNNEL
// ---------------------------------------------------------------------------

section("8. Sequential conditional probabilities");

const signUpGivenVisit = 0.40;
const activationGivenSignup = 0.60;
const paidGivenActivation = 0.30;

const paidProbability =
    signUpGivenVisit *
    activationGivenSignup *
    paidGivenActivation;

console.log(`P(Paid | Initial visitor): ${percentage(paidProbability)}`);


// ---------------------------------------------------------------------------
// 10. EXPECTED VALUE
// ---------------------------------------------------------------------------

section("9. Expected value");

const scenarios = [
    { name: "High demand", probability: 0.25, payoff: 200000 },
    { name: "Medium demand", probability: 0.50, payoff: 80000 },
    { name: "Low demand", probability: 0.25, payoff: -60000 }
];

function expectedValue(outcomes) {
    const probabilitySum = outcomes.reduce(
        (sum, outcome) => sum + outcome.probability,
        0
    );

    if (Math.abs(probabilitySum - 1) > 1e-10) {
        throw new Error("Probabilities must sum to 1.");
    }

    return outcomes.reduce(
        (sum, outcome) =>
            sum + outcome.probability * outcome.payoff,
        0
    );
}

console.log(`Expected payoff: ₹${expectedValue(scenarios).toFixed(2)}`);


// ---------------------------------------------------------------------------
// 11. EXPECTED VALUE AND RISK
// ---------------------------------------------------------------------------

section("10. Expected value and variance");

function expectedValueAndVariance(outcomes) {
    const mean = expectedValue(outcomes);

    const variance = outcomes.reduce(
        (sum, outcome) =>
            sum +
            outcome.probability *
            (outcome.payoff - mean) ** 2,
        0
    );

    return {
        mean,
        variance,
        standardDeviation: Math.sqrt(variance)
    };
}

const riskyDecision = [
    { probability: 0.50, payoff: 300000 },
    { probability: 0.50, payoff: -100000 }
];

const stableDecision = [
    { probability: 0.90, payoff: 120000 },
    { probability: 0.10, payoff: 80000 }
];

for (const [name, outcomes] of [
    ["Risky", riskyDecision],
    ["Stable", stableDecision]
]) {
    const result = expectedValueAndVariance(outcomes);

    console.log(
        `${name}: EV=₹${result.mean.toFixed(0)}, ` +
        `SD=₹${result.standardDeviation.toFixed(0)}`
    );
}


// ---------------------------------------------------------------------------
// 12. MONTE CARLO SIMULATION
// ---------------------------------------------------------------------------

section("11. Monte Carlo simulation");

function createSeededRandom(seed = 123456789) {
    // A small deterministic pseudo-random generator makes the example
    // reproducible without requiring an external package.
    let state = seed >>> 0;

    return function random() {
        state = (
            Math.imul(1664525, state) +
            1013904223
        ) >>> 0;

        return state / 4294967296;
    };
}

function simulateBernoulli(trials, probabilityOfSuccess, seed) {
    if (!Number.isInteger(trials) || trials <= 0) {
        throw new RangeError("Trials must be a positive integer.");
    }

    const random = createSeededRandom(seed);
    let successes = 0;

    for (let i = 0; i < trials; i++) {
        if (random() < probabilityOfSuccess) {
            successes++;
        }
    }

    return successes / trials;
}

const simulatedRate =
    simulateBernoulli(100000, 0.18, 42);

console.log(`Simulated probability: ${percentage(simulatedRate)}`);
console.log(`Theoretical probability: ${percentage(0.18)}`);


// ---------------------------------------------------------------------------
// 13. CONFUSION MATRIX
// ---------------------------------------------------------------------------

section("12. Classification metrics");

const confusionMatrix = {
    truePositive: 760,
    falsePositive: 140,
    trueNegative: 8500,
    falseNegative: 600
};

const precision =
    confusionMatrix.truePositive /
    (
        confusionMatrix.truePositive +
        confusionMatrix.falsePositive
    );

const recall =
    confusionMatrix.truePositive /
    (
        confusionMatrix.truePositive +
        confusionMatrix.falseNegative
    );

const specificity =
    confusionMatrix.trueNegative /
    (
        confusionMatrix.trueNegative +
        confusionMatrix.falsePositive
    );

console.log(`Precision: ${percentage(precision)}`);
console.log(`Recall: ${percentage(recall)}`);
console.log(`Specificity: ${percentage(specificity)}`);


// ---------------------------------------------------------------------------
// 14. RISK SEGMENTATION
// ---------------------------------------------------------------------------

section("13. Customer risk segmentation");

const riskSegments = [
    { name: "Low", share: 0.60, defaultRate: 0.02 },
    { name: "Medium", share: 0.30, defaultRate: 0.08 },
    { name: "High", share: 0.10, defaultRate: 0.25 }
];

const defaultRate = riskSegments.reduce(
    (sum, segment) =>
        sum + segment.share * segment.defaultRate,
    0
);

const highGivenDefault =
    (
        riskSegments[2].share *
        riskSegments[2].defaultRate
    ) / defaultRate;

console.log(`P(Default): ${percentage(defaultRate)}`);
console.log(`P(High risk | Default): ${percentage(highGivenDefault)}`);


// ---------------------------------------------------------------------------
// 15. BASE-RATE EFFECT
// ---------------------------------------------------------------------------

section("14. Base-rate effect");

function posteriorFromPositiveSignal(
    baseRate,
    sensitivity,
    falsePositiveRate
) {
    const positiveProbability =
        sensitivity * baseRate +
        falsePositiveRate * (1 - baseRate);

    return (
        sensitivity * baseRate /
        positiveProbability
    );
}

const posteriorFraud =
    posteriorFromPositiveSignal(
        0.005,
        0.99,
        0.02
    );

console.log(
    `P(Fraud | Positive signal): ${percentage(posteriorFraud)}`
);


// ---------------------------------------------------------------------------
// 16. BAYESIAN UPDATING
// ---------------------------------------------------------------------------

section("15. Bayesian updating");

let priorGoodMarket = 0.20;

function updateBelief(
    prior,
    likelihoodOfEvidenceGivenHypothesis,
    likelihoodOfEvidenceGivenAlternative
) {
    return bayes({
        prior,
        likelihoodGivenCondition:
            likelihoodOfEvidenceGivenHypothesis,
        likelihoodGivenNotCondition:
            likelihoodOfEvidenceGivenAlternative
    });
}

const posteriorGoodMarket = updateBelief(
    priorGoodMarket,
    0.75,
    0.25
);

console.log(
    `Prior P(Good market): ${percentage(priorGoodMarket)}`
);
console.log(
    `Posterior P(Good market | Evidence): ${
        percentage(posteriorGoodMarket)
    }`
);


// ---------------------------------------------------------------------------
// 17. EXPECTED VALUE OF PERFECT INFORMATION
// ---------------------------------------------------------------------------

section("16. Expected value of perfect information");

const decisionPayoffs = {
    Expand: {
        High: 200000,
        Low: -100000
    },
    DoNotExpand: {
        High: 90000,
        Low: 30000
    }
};

const stateProbabilities = {
    High: 0.40,
    Low: 0.60
};

const valuesWithoutInformation =
    Object.entries(decisionPayoffs).map(
        ([decision, payoffs]) => ({
            decision,
            expectedPayoff:
                Object.entries(stateProbabilities).reduce(
                    (sum, [state, stateProbability]) =>
                        sum +
                        stateProbability *
                        payoffs[state],
                    0
                )
        })
    );

const bestWithoutInformation =
    Math.max(
        ...valuesWithoutInformation.map(
            item => item.expectedPayoff
        )
    );

const expectedWithPerfectInformation =
    Object.entries(stateProbabilities).reduce(
        (sum, [state, stateProbability]) => {
            const bestPayoff = Math.max(
                ...Object.values(decisionPayoffs)
                    .map(payoffs => payoffs[state])
            );

            return sum + stateProbability * bestPayoff;
        },
        0
    );

const evpi =
    expectedWithPerfectInformation -
    bestWithoutInformation;

console.log(
    `Best EV without information: ₹${bestWithoutInformation}`
);
console.log(
    `EV with perfect information: ₹${expectedWithPerfectInformation}`
);
console.log(`EVPI: ₹${evpi}`);


// ---------------------------------------------------------------------------
// 18. A/B TESTING
// ---------------------------------------------------------------------------

section("17. A/B testing");

const control = {
    visitors: 5000,
    conversions: 450
};

const treatment = {
    visitors: 5000,
    conversions: 550
};

const controlConversion =
    control.conversions / control.visitors;

const treatmentConversion =
    treatment.conversions / treatment.visitors;

const absoluteLift =
    treatmentConversion - controlConversion;

const relativeLift =
    absoluteLift / controlConversion;

console.log(`Control: ${percentage(controlConversion)}`);
console.log(`Treatment: ${percentage(treatmentConversion)}`);
console.log(`Absolute lift: ${percentage(absoluteLift)}`);
console.log(`Relative lift: ${percentage(relativeLift)}`);


// ---------------------------------------------------------------------------
// 19. CONFIDENCE APPROXIMATION
// ---------------------------------------------------------------------------

section("18. Sampling uncertainty");

function proportionStandardError(p, n) {
    if (p < 0 || p > 1 || n <= 0) {
        throw new RangeError("Invalid p or n.");
    }

    return Math.sqrt(p * (1 - p) / n);
}

const standardError =
    proportionStandardError(
        treatmentConversion,
        treatment.visitors
    );

const marginOfError =
    1.96 * standardError;

console.log(
    `Approximate 95% margin of error: ±${percentage(marginOfError)}`
);


// ---------------------------------------------------------------------------
// 20. CONDITIONAL EXPECTATION
// ---------------------------------------------------------------------------

section("19. Conditional expectation");

const customerSegments = [
    { name: "Enterprise", probability: 0.20, revenue: 1200 },
    { name: "SMB", probability: 0.50, revenue: 500 },
    { name: "Consumer", probability: 0.30, revenue: 100 }
];

const expectedRevenue =
    customerSegments.reduce(
        (sum, segment) =>
            sum + segment.probability * segment.revenue,
        0
    );

console.log(
    `Expected revenue per customer: ₹${expectedRevenue.toFixed(2)}`
);


// ---------------------------------------------------------------------------
// 21. SIMPSON'S PARADOX
// ---------------------------------------------------------------------------

section("20. Simpson's paradox");

const groupedResults = {
    "High-value": {
        A: { success: 90, total: 100 },
        B: { success: 180, total: 200 }
    },
    "Low-value": {
        A: { success: 9, total: 10 },
        B: { success: 1, total: 2 }
    }
};

for (const [group, treatments] of Object.entries(groupedResults)) {
    const rateA =
        treatments.A.success / treatments.A.total;

    const rateB =
        treatments.B.success / treatments.B.total;

    console.log(
        `${group}: A=${percentage(rateA)}, B=${percentage(rateB)}`
    );
}

const aggregatedA = Object.values(groupedResults)
    .reduce(
        (accumulator, group) => ({
            success: accumulator.success + group.A.success,
            total: accumulator.total + group.A.total
        }),
        { success: 0, total: 0 }
    );

const aggregatedB = Object.values(groupedResults)
    .reduce(
        (accumulator, group) => ({
            success: accumulator.success + group.B.success,
            total: accumulator.total + group.B.total
        }),
        { success: 0, total: 0 }
    );

console.log(
    `Aggregated A: ${
        percentage(aggregatedA.success / aggregatedA.total)
    }`
);

console.log(
    `Aggregated B: ${
        percentage(aggregatedB.success / aggregatedB.total)
    }`
);


// ---------------------------------------------------------------------------
// 22. CONDITIONAL PROBABILITY TABLE
// ---------------------------------------------------------------------------

section("21. Probability table abstraction");

class ProbabilityTable {
    constructor(table) {
        this.table = table;
        this.validate();
    }

    validate() {
        const rows = Object.values(this.table);

        if (rows.length === 0) {
            throw new Error("Probability table cannot be empty.");
        }

        let total = 0;

        for (const row of rows) {
            if (Object.keys(row).length === 0) {
                throw new Error("Rows cannot be empty.");
            }

            for (const value of Object.values(row)) {
                if (value < 0) {
                    throw new Error("Probabilities cannot be negative.");
                }

                total += value;
            }
        }

        if (Math.abs(total - 1) > 1e-10) {
            throw new Error(
                `Joint probabilities must sum to 1. Received ${total}.`
            );
        }
    }

    marginalRow(rowName) {
        return Object.values(this.table[rowName])
            .reduce((sum, value) => sum + value, 0);
    }

    marginalColumn(columnName) {
        return Object.values(this.table)
            .reduce(
                (sum, row) =>
                    sum + (row[columnName] ?? 0),
                0
            );
    }

    joint(rowName, columnName) {
        return this.table[rowName][columnName];
    }

    conditionalColumnGivenRow(columnName, rowName) {
        const denominator = this.marginalRow(rowName);

        if (denominator === 0) {
            throw new Error(
                "Cannot condition on a zero-probability event."
            );
        }

        return this.joint(rowName, columnName) / denominator;
    }

    conditionalRowGivenColumn(rowName, columnName) {
        const denominator =
            this.marginalColumn(columnName);

        if (denominator === 0) {
            throw new Error(
                "Cannot condition on a zero-probability event."
            );
        }

        return this.joint(rowName, columnName) / denominator;
    }
}

const customerTable = new ProbabilityTable({
    New: {
        Buy: 0.08,
        NoBuy: 0.42
    },
    Returning: {
        Buy: 0.20,
        NoBuy: 0.30
    }
});

console.log(
    `P(Buy | Returning): ${
        percentage(
            customerTable.conditionalColumnGivenRow(
                "Buy",
                "Returning"
            )
        )
    }`
);

console.log(
    `P(Returning | Buy): ${
        percentage(
            customerTable.conditionalRowGivenColumn(
                "Returning",
                "Buy"
            )
        )
    }`
);


// ---------------------------------------------------------------------------
// 23. BUSINESS DECISION ENGINE
// ---------------------------------------------------------------------------

section("22. Business decision engine");

class BusinessDecision {
    constructor(name, payoffs) {
        this.name = name;
        this.payoffs = payoffs;
    }

    expectedValue(states) {
        return states.reduce(
            (sum, state) =>
                sum +
                state.probability *
                this.payoffs[state.name],
            0
        );
    }

    worstCase() {
        return Math.min(...Object.values(this.payoffs));
    }

    bestCase() {
        return Math.max(...Object.values(this.payoffs));
    }
}

const marketStates = [
    { name: "High", probability: 0.30 },
    { name: "Normal", probability: 0.50 },
    { name: "Low", probability: 0.20 }
];

const decisions = [
    new BusinessDecision(
        "Large launch",
        {
            High: 600000,
            Normal: 180000,
            Low: -250000
        }
    ),
    new BusinessDecision(
        "Small launch",
        {
            High: 300000,
            Normal: 140000,
            Low: 20000
        }
    ),
    new BusinessDecision(
        "Delay",
        {
            High: 100000,
            Normal: 80000,
            Low: 50000
        }
    )
];

const rankedDecisions = decisions
    .map(decision => ({
        decision,
        expectedValue:
            decision.expectedValue(marketStates)
    }))
    .sort(
        (a, b) =>
            b.expectedValue - a.expectedValue
    );

for (const result of rankedDecisions) {
    console.log(
        `${result.decision.name}: EV=₹${result.expectedValue}`
    );
}

console.log(
    `Best expected-value decision: ${
        rankedDecisions[0].decision.name
    }`
);


// ---------------------------------------------------------------------------
// 24. EVENT-DRIVEN BUSINESS SIGNAL PROCESSOR
// ---------------------------------------------------------------------------

section("23. Event-driven probability update");

class SignalProcessor {
    constructor(prior) {
        this.prior = prior;
        this.history = [];
    }

    observe(signalName, likelihoodGood, likelihoodBad) {
        const posterior = updateBelief(
            this.prior,
            likelihoodGood,
            likelihoodBad
        );

        this.history.push({
            signalName,
            prior: this.prior,
            posterior
        });

        this.prior = posterior;

        return posterior;
    }
}

const processor = new SignalProcessor(0.30);

console.log(
    `After sales signal: ${
        percentage(
            processor.observe("Sales growth", 0.80, 0.30)
        )
    }`
);

console.log(
    `After customer signal: ${
        percentage(
            processor.observe("Retention improvement", 0.70, 0.40)
        )
    }`
);

console.log("Evidence history:", processor.history);


// ---------------------------------------------------------------------------
// 25. VALIDATION AND ERROR HANDLING
// ---------------------------------------------------------------------------

section("24. Edge cases and validation");

const invalidOperations = [
    () => probability(1, 0),
    () => conditionalProbability(5, 0),
    () => binomialProbability(5, 8, 0.5),
    () => bayes({
        prior: 1.5,
        likelihoodGivenCondition: 0.8,
        likelihoodGivenNotCondition: 0.2
    })
];

for (const operation of invalidOperations) {
    try {
        operation();
    } catch (error) {
        console.log(`Handled: ${error.message}`);
    }
}


// ---------------------------------------------------------------------------
// 26. PERFORMANCE COMPARISON
// ---------------------------------------------------------------------------

section("25. Performance considerations");

function naiveBinomialDistribution(n, p) {
    const distribution = [];

    for (let k = 0; k <= n; k++) {
        distribution.push(
            binomialProbability(n, k, p)
        );
    }

    return distribution;
}

const start = process.hrtime.bigint();

const distribution =
    naiveBinomialDistribution(40, 0.25);

const elapsedNanoseconds =
    process.hrtime.bigint() - start;

console.log(
    `Computed ${distribution.length} probabilities in ` +
    `${Number(elapsedNanoseconds) / 1e6} ms`
);

console.log(
    "For very large n, direct factorial calculations can overflow. " +
    "Production numerical systems often use logarithms, recurrence relations, " +
    "or specialized statistical libraries."
);


// ---------------------------------------------------------------------------
// 27. BUSINESS RISK SCORING
// ---------------------------------------------------------------------------

section("26. Conditional risk scoring");

function classifyRisk(probabilityOfDefault) {
    if (probabilityOfDefault < 0.03) {
        return "Low";
    }

    if (probabilityOfDefault < 0.10) {
        return "Medium";
    }

    return "High";
}

const customersForScoring = [
    { id: "C001", defaultProbability: 0.015 },
    { id: "C002", defaultProbability: 0.075 },
    { id: "C003", defaultProbability: 0.22 }
];

for (const customer of customersForScoring) {
    console.log(
        `${customer.id}: ${
            percentage(customer.defaultProbability)
        } -> ${classifyRisk(customer.defaultProbability)}`
    );
}


// ---------------------------------------------------------------------------
// 28. MINI TEST SUITE
// ---------------------------------------------------------------------------

section("27. Embedded tests");

function runTests() {
    assertAlmostEqual(
        conditionalProbability(25, 100),
        0.25
    );

    assertAlmostEqual(
        binomialProbability(1, 1, 0.7),
        0.7
    );

    assertAlmostEqual(
        binomialProbability(1, 0, 0.7),
        0.3
    );

    assertAlmostEqual(
        expectedValue([
            { probability: 0.5, payoff: 100 },
            { probability: 0.5, payoff: 0 }
        ]),
        50
    );

    try {
        conditionalProbability(1, 0);
    } catch (error) {
        console.log("Zero-condition test passed.");
    }

    console.log("All mathematical tests passed.");
}

runTests();


// ---------------------------------------------------------------------------
// 29. BROWSER-COMPATIBLE OPTIONAL DEMONSTRATION
// ---------------------------------------------------------------------------

if (typeof window !== "undefined") {
    /*
     * In a browser, this demonstrates event-driven interaction.
     * It deliberately avoids external frameworks.
     */
    window.addEventListener("load", () => {
        const button = document.createElement("button");
        button.textContent = "Calculate P(Purchase | Mobile)";

        const output = document.createElement("pre");

        button.addEventListener("click", () => {
            output.textContent =
                `P(Purchase | Mobile) = ${
                    percentage(pPurchaseGivenMobile)
                }`;
        });

        document.body.appendChild(button);
        document.body.appendChild(output);
    });
}


// ---------------------------------------------------------------------------
// 30. FINAL BUSINESS INTERPRETATION
// ---------------------------------------------------------------------------

section("28. Business interpretation");

console.log(
    "Conditional probability is useful whenever a decision changes after " +
    "new information becomes available."
);

console.log(
    "Examples include customer conversion, credit risk, fraud detection, " +
    "marketing response, demand forecasting, A/B testing, inventory planning, " +
    "and investment decisions."
);

console.log(
    "The key analytical discipline is to distinguish P(A | B) from P(B | A), " +
    "account for base rates, identify possible confounders, and quantify the " +
    "financial consequences of uncertain outcomes."
);
