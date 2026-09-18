/*
 * Correlation: Measuring Relationships Between Variables
 * ========================================================
 *
 * Self-contained JavaScript study file.
 *
 * The examples progress from basic Pearson correlation to ranking,
 * Spearman correlation, Kendall-style pair comparison, correlation
 * matrices, regression, bootstrapping, permutation testing, and a
 * practical browser-independent analytics case study.
 *
 * Run with:
 *     node correlation.js
 */


// ============================================================================
// 1. BASIC UTILITIES
// ============================================================================

function mean(values) {
    if (values.length === 0) {
        throw new Error("Mean requires at least one observation.");
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
}


function validatePairs(x, y) {
    if (x.length !== y.length) {
        throw new Error("Both variables must contain the same number of observations.");
    }

    if (x.length < 2) {
        throw new Error("At least two paired observations are required.");
    }

    for (const value of [...x, ...y]) {
        if (!Number.isFinite(value)) {
            throw new Error("Correlation requires finite numeric observations.");
        }
    }
}


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


// ============================================================================
// 2. COVARIANCE
// ============================================================================

function covarianceSample(x, y) {
    validatePairs(x, y);

    const xMean = mean(x);
    const yMean = mean(y);

    const crossDeviation = x.reduce(
        (sum, value, index) =>
            sum + (value - xMean) * (y[index] - yMean),
        0
    );

    return crossDeviation / (x.length - 1);
}


// ============================================================================
// 3. PEARSON CORRELATION
// ============================================================================

function pearsonCorrelation(x, y) {
    validatePairs(x, y);

    const xMean = mean(x);
    const yMean = mean(y);

    let numerator = 0;
    let xSquared = 0;
    let ySquared = 0;

    for (let i = 0; i < x.length; i++) {
        const centeredX = x[i] - xMean;
        const centeredY = y[i] - yMean;

        numerator += centeredX * centeredY;
        xSquared += centeredX * centeredX;
        ySquared += centeredY * centeredY;
    }

    const denominator = Math.sqrt(xSquared * ySquared);

    if (denominator === 0) {
        throw new Error(
            "Pearson correlation is undefined when either variable is constant."
        );
    }

    return numerator / denominator;
}


// ============================================================================
// 4. RANKING WITH TIES
// ============================================================================

function rankWithTies(values) {
    const indexed = values.map((value, index) => ({ value, index }));
    indexed.sort((a, b) => a.value - b.value);

    const ranks = new Array(values.length);
    let position = 0;

    while (position < indexed.length) {
        let end = position + 1;

        while (
            end < indexed.length &&
            indexed[end].value === indexed[position].value
        ) {
            end++;
        }

        const averageRank = ((position + 1) + end) / 2;

        for (let i = position; i < end; i++) {
            ranks[indexed[i].index] = averageRank;
        }

        position = end;
    }

    return ranks;
}


// ============================================================================
// 5. SPEARMAN CORRELATION
// ============================================================================

function spearmanCorrelation(x, y) {
    validatePairs(x, y);

    const xRanks = rankWithTies(x);
    const yRanks = rankWithTies(y);

    return pearsonCorrelation(xRanks, yRanks);
}


// ============================================================================
// 6. KENDALL'S TAU-A
// ============================================================================

function kendallTau(x, y) {
    validatePairs(x, y);

    let concordant = 0;
    let discordant = 0;

    for (let i = 0; i < x.length - 1; i++) {
        for (let j = i + 1; j < x.length; j++) {
            const dx = x[j] - x[i];
            const dy = y[j] - y[i];

            if (dx === 0 || dy === 0) {
                continue;
            }

            if (dx * dy > 0) {
                concordant++;
            } else {
                discordant++;
            }
        }
    }

    const totalPairs = x.length * (x.length - 1) / 2;

    return (concordant - discordant) / totalPairs;
}


// ============================================================================
// 7. PARTIAL CORRELATION
// ============================================================================

function linearRegressionCoefficients(x, y) {
    validatePairs(x, y);

    const xMean = mean(x);
    const yMean = mean(y);

    let numerator = 0;
    let denominator = 0;

    for (let i = 0; i < x.length; i++) {
        numerator += (x[i] - xMean) * (y[i] - yMean);
        denominator += (x[i] - xMean) ** 2;
    }

    if (denominator === 0) {
        throw new Error("Regression predictor has zero variance.");
    }

    const slope = numerator / denominator;
    const intercept = yMean - slope * xMean;

    return { intercept, slope };
}


function residualsAfterRegression(target, control) {
    const { intercept, slope } =
        linearRegressionCoefficients(control, target);

    return target.map(
        (value, index) =>
            value - (intercept + slope * control[index])
    );
}


function partialCorrelation(x, y, control) {
    validatePairs(x, y);
    validatePairs(x, control);

    const xResiduals = residualsAfterRegression(x, control);
    const yResiduals = residualsAfterRegression(y, control);

    return pearsonCorrelation(xResiduals, yResiduals);
}


// ============================================================================
// 8. SIMPLE LINEAR REGRESSION
// ============================================================================

function simpleLinearRegression(x, y) {
    const r = pearsonCorrelation(x, y);
    const { intercept, slope } = linearRegressionCoefficients(x, y);

    return {
        intercept,
        slope,
        r,
        rSquared: r * r,
        predict(value) {
            return intercept + slope * value;
        }
    };
}


// ============================================================================
// 9. CORRELATION MATRIX
// ============================================================================

function correlationMatrix(dataset) {
    const names = Object.keys(dataset);
    const matrix = {};

    for (const firstName of names) {
        matrix[firstName] = {};

        for (const secondName of names) {
            if (firstName === secondName) {
                matrix[firstName][secondName] = 1;
            } else {
                matrix[firstName][secondName] =
                    pearsonCorrelation(
                        dataset[firstName],
                        dataset[secondName]
                    );
            }
        }
    }

    return matrix;
}


function printCorrelationMatrix(matrix) {
    const names = Object.keys(matrix);

    console.log("".padEnd(16) + names.map(
        name => name.padStart(15)
    ).join(""));

    for (const row of names) {
        const values = names.map(
            column => matrix[row][column].toFixed(3).padStart(15)
        ).join("");

        console.log(row.padEnd(16) + values);
    }
}


// ============================================================================
// 10. RANDOM NUMBER GENERATOR FOR REPRODUCIBLE SIMULATIONS
// ============================================================================

class SeededRandom {
    /*
     * A small linear congruential generator is used so the demonstration can
     * reproduce bootstrap and permutation results without external packages.
     */
    constructor(seed = 42) {
        this.state = seed >>> 0;
    }

    next() {
        this.state =
            (1664525 * this.state + 1013904223) >>> 0;

        return this.state / 4294967296;
    }

    integer(maxExclusive) {
        return Math.floor(this.next() * maxExclusive);
    }

    choice(values) {
        return values[this.integer(values.length)];
    }

    shuffle(values) {
        // Fisher-Yates gives each permutation equal probability when the
        // underlying random-number generator is treated as uniform.
        for (let i = values.length - 1; i > 0; i--) {
            const j = this.integer(i + 1);
            [values[i], values[j]] = [values[j], values[i]];
        }
    }
}


// ============================================================================
// 11. BOOTSTRAP CONFIDENCE INTERVAL
// ============================================================================

function bootstrapCorrelationInterval(
    x,
    y,
    repetitions = 3000,
    confidence = 0.95,
    seed = 42
) {
    validatePairs(x, y);

    if (repetitions < 100) {
        throw new Error("Use at least 100 bootstrap repetitions.");
    }

    if (!(confidence > 0 && confidence < 1)) {
        throw new Error("Confidence must be between 0 and 1.");
    }

    const random = new SeededRandom(seed);
    const pairs = x.map((value, index) => ({
        x: value,
        y: y[index]
    }));

    const estimates = [];

    for (let repetition = 0; repetition < repetitions; repetition++) {
        const sampleX = [];
        const sampleY = [];

        for (let i = 0; i < pairs.length; i++) {
            const pair = random.choice(pairs);
            sampleX.push(pair.x);
            sampleY.push(pair.y);
        }

        try {
            estimates.push(pearsonCorrelation(sampleX, sampleY));
        } catch {
            // A bootstrap sample can contain the same observation repeatedly,
            // producing zero variance for small datasets.
        }
    }

    if (estimates.length === 0) {
        throw new Error("No valid bootstrap estimates were generated.");
    }

    estimates.sort((a, b) => a - b);

    const alpha = 1 - confidence;
    const lowerIndex =
        Math.floor((alpha / 2) * (estimates.length - 1));
    const upperIndex =
        Math.floor((1 - alpha / 2) * (estimates.length - 1));

    return [
        estimates[lowerIndex],
        estimates[upperIndex]
    ];
}


// ============================================================================
// 12. PERMUTATION TEST
// ============================================================================

function permutationCorrelationTest(
    x,
    y,
    repetitions = 3000,
    seed = 42
) {
    validatePairs(x, y);

    const observed = pearsonCorrelation(x, y);
    const random = new SeededRandom(seed);
    let extreme = 0;

    for (let repetition = 0; repetition < repetitions; repetition++) {
        const shuffledY = [...y];

        random.shuffle(shuffledY);

        const permutedCorrelation =
            pearsonCorrelation(x, shuffledY);

        if (Math.abs(permutedCorrelation) >= Math.abs(observed)) {
            extreme++;
        }
    }

    // +1 correction avoids reporting a zero probability from a finite
    // permutation sample.
    const pValue =
        (extreme + 1) / (repetitions + 1);

    return { observed, pValue };
}


// ============================================================================
// 13. FISHER Z TRANSFORMATION
// ============================================================================

function fisherZ(r) {
    if (!(r > -1 && r < 1)) {
        throw new Error("Fisher z requires -1 < r < 1.");
    }

    return 0.5 * Math.log((1 + r) / (1 - r));
}


function inverseFisherZ(z) {
    return Math.tanh(z);
}


// ============================================================================
// 14. MISSING DATA
// ============================================================================

function pairwiseCompleteCases(x, y) {
    if (x.length !== y.length) {
        throw new Error("Variables must have equal lengths.");
    }

    const cleanX = [];
    const cleanY = [];

    for (let i = 0; i < x.length; i++) {
        if (x[i] == null || y[i] == null) {
            continue;
        }

        cleanX.push(x[i]);
        cleanY.push(y[i]);
    }

    return { x: cleanX, y: cleanY };
}


// ============================================================================
// 15. EDGE CASES AND CONCEPTUAL DEMONSTRATIONS
// ============================================================================

function demonstrateOutlierSensitivity() {
    subsection("Outlier sensitivity");

    const x = [1, 2, 3, 4, 5, 6, 7];
    const normalY = [2, 4, 6, 8, 10, 12, 14];
    const outlierY = [2, 4, 6, 8, 10, 12, 100];

    console.log(
        "Without outlier:",
        pearsonCorrelation(x, normalY).toFixed(4)
    );

    console.log(
        "With outlier:   ",
        pearsonCorrelation(x, outlierY).toFixed(4)
    );
}


function demonstrateNonlinearRelationship() {
    subsection("Nonlinear relationship");

    const x = Array.from({ length: 21 }, (_, i) => i - 10);
    const y = x.map(value => value ** 2);

    console.log(
        "Pearson r for y = x^2:",
        pearsonCorrelation(x, y).toFixed(4)
    );

    console.log(
        "The U-shaped relationship is real but Pearson correlation focuses "
        + "on linear association."
    );
}


function demonstrateScaleTransformation() {
    subsection("Scale transformation");

    const x = [1, 2, 3, 4, 5];
    const y = [3, 6, 9, 12, 15];

    const original = pearsonCorrelation(x, y);

    const transformedX = x.map(value => value * 100 + 5000);
    const transformedY = y.map(value => value * -7 + 900);

    const transformed =
        pearsonCorrelation(transformedX, transformedY);

    console.log("Original:", original.toFixed(4));
    console.log("Transformed:", transformed.toFixed(4));
    console.log(
        "A negative rescaling reverses the correlation direction."
    );
}


function demonstrateZeroVariance() {
    subsection("Zero variance");

    try {
        pearsonCorrelation(
            [1, 1, 1, 1],
            [2, 3, 4, 5]
        );
    } catch (error) {
        console.log("Expected error:", error.message);
    }
}


// ============================================================================
// 16. PRACTICAL WEB-STYLE DATA PROCESSING
// ============================================================================

function analyzeEmployeeDataset(records) {
    /*
     * JavaScript is particularly useful for application-level analytics.
     * Here the input resembles records received from a web API.
     */
    if (!Array.isArray(records) || records.length < 2) {
        throw new Error("At least two records are required.");
    }

    const trainingHours = records.map(
        record => record.trainingHours
    );

    const productivity = records.map(
        record => record.productivity
    );

    const experience = records.map(
        record => record.experience
    );

    return {
        trainingProductivity: pearsonCorrelation(
            trainingHours,
            productivity
        ),
        partialTrainingProductivity: partialCorrelation(
            trainingHours,
            productivity,
            experience
        )
    };
}


// ============================================================================
// 17. TESTS
// ============================================================================

function assertClose(actual, expected, tolerance = 1e-10) {
    if (Math.abs(actual - expected) > tolerance) {
        throw new Error(
            `Expected ${expected}, received ${actual}`
        );
    }
}


function runTests() {
    subsection("Automated tests");

    const x = [1, 2, 3, 4, 5];
    const positive = [2, 4, 6, 8, 10];
    const negative = [-2, -4, -6, -8, -10];

    assertClose(
        pearsonCorrelation(x, positive),
        1
    );

    assertClose(
        pearsonCorrelation(x, negative),
        -1
    );

    assertClose(
        spearmanCorrelation(
            [10, 20, 30, 40],
            [1, 2, 3, 4]
        ),
        1
    );

    assertClose(
        kendallTau(
            [1, 2, 3],
            [10, 20, 30]
        ),
        1
    );

    const ranks = rankWithTies([30, 10, 20, 20]);
    const expected = [4, 1, 2.5, 2.5];

    for (let i = 0; i < ranks.length; i++) {
        assertClose(ranks[i], expected[i]);
    }

    const regression =
        simpleLinearRegression(x, positive);

    assertClose(regression.slope, 2);
    assertClose(regression.intercept, 0);
    assertClose(regression.rSquared, 1);

    const cleaned = pairwiseCompleteCases(
        [1, null, 3, 4],
        [2, 5, null, 8]
    );

    if (
        JSON.stringify(cleaned.x) !== JSON.stringify([1, 4]) ||
        JSON.stringify(cleaned.y) !== JSON.stringify([2, 8])
    ) {
        throw new Error("Pairwise missing-data test failed.");
    }

    console.log("All JavaScript tests passed.");
}


// ============================================================================
// 18. MAIN CASE STUDY
// ============================================================================

function main() {
    section("Correlation: Measuring Relationships Between Variables");

    subsection("Basic example");

    const studyHours = [1, 2, 3, 4, 5, 6];
    const examScores = [55, 60, 66, 72, 78, 85];

    console.log(
        "Sample covariance:",
        covarianceSample(studyHours, examScores).toFixed(4)
    );

    console.log(
        "Pearson correlation:",
        pearsonCorrelation(studyHours, examScores).toFixed(4)
    );

    subsection("Pearson, Spearman, and Kendall");

    const x = [1, 2, 3, 4, 5, 6];
    const y = [2, 3, 5, 7, 11, 13];

    console.log(
        "Pearson:",
        pearsonCorrelation(x, y).toFixed(4)
    );

    console.log(
        "Spearman:",
        spearmanCorrelation(x, y).toFixed(4)
    );

    console.log(
        "Kendall tau:",
        kendallTau(x, y).toFixed(4)
    );

    subsection("Correlation matrix");

    const businessData = {
        advertising: [12, 15, 17, 20, 22, 25, 27, 30, 34, 36],
        websiteVisits: [180, 210, 240, 260, 300, 340, 360, 410, 450, 470],
        sales: [25, 30, 32, 39, 43, 49, 52, 60, 67, 70]
    };

    printCorrelationMatrix(
        correlationMatrix(businessData)
    );

    subsection("Regression connection");

    const regression =
        simpleLinearRegression(
            businessData.advertising,
            businessData.sales
        );

    console.log("Slope:", regression.slope.toFixed(4));
    console.log("Intercept:", regression.intercept.toFixed(4));
    console.log("r:", regression.r.toFixed(4));
    console.log("R²:", regression.rSquared.toFixed(4));
    console.log(
        "Predicted sales at advertising = 40:",
        regression.predict(40).toFixed(2)
    );

    subsection("Partial correlation");

    const records = [
        { trainingHours: 2, productivity: 50, experience: 1 },
        { trainingHours: 3, productivity: 54, experience: 2 },
        { trainingHours: 4, productivity: 60, experience: 3 },
        { trainingHours: 4, productivity: 61, experience: 4 },
        { trainingHours: 6, productivity: 69, experience: 5 },
        { trainingHours: 7, productivity: 73, experience: 6 },
        { trainingHours: 8, productivity: 77, experience: 7 },
        { trainingHours: 9, productivity: 82, experience: 8 }
    ];

    const analysis = analyzeEmployeeDataset(records);

    console.log(
        "Raw training-productivity r:",
        analysis.trainingProductivity.toFixed(4)
    );

    console.log(
        "Partial correlation controlling experience:",
        analysis.partialTrainingProductivity.toFixed(4)
    );

    subsection("Bootstrap interval");

    const interval =
        bootstrapCorrelationInterval(
            studyHours,
            examScores,
            3000,
            0.95,
            42
        );

    console.log(
        `Approximate bootstrap 95% interval: `
        + `[${interval[0].toFixed(4)}, ${interval[1].toFixed(4)}]`
    );

    subsection("Permutation test");

    const permutation =
        permutationCorrelationTest(
            studyHours,
            examScores,
            3000,
            42
        );

    console.log(
        "Observed r:",
        permutation.observed.toFixed(4)
    );

    console.log(
        "Estimated two-sided p-value:",
        permutation.pValue.toFixed(4)
    );

    subsection("Fisher transformation");

    const r = pearsonCorrelation(
        studyHours,
        examScores
    );

    const z = fisherZ(r);

    console.log("r:", r.toFixed(4));
    console.log("Fisher z:", z.toFixed(4));
    console.log(
        "Inverse Fisher z:",
        inverseFisherZ(z).toFixed(4)
    );

    demonstrateOutlierSensitivity();
    demonstrateNonlinearRelationship();
    demonstrateScaleTransformation();
    demonstrateZeroVariance();

    subsection("Interpretation principles");

    console.log("Correlation measures association, not causation.");
    console.log("Pearson focuses on linear association.");
    console.log("Spearman uses ranks and captures monotonic association.");
    console.log("Kendall compares concordant and discordant pairs.");
    console.log("Outliers can substantially change correlation.");
    console.log("A zero Pearson correlation can coexist with nonlinear structure.");
    console.log("Sample size and uncertainty matter when interpreting a coefficient.");

    runTests();

    section("End of JavaScript correlation study");
}


main();
