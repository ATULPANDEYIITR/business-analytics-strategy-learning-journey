"use strict";

/*
 * Regression Basics: Understanding Relationships and Prediction
 *
 * A self-contained JavaScript study file.
 *
 * The examples demonstrate:
 * - statistical foundations
 * - simple linear regression
 * - residuals and evaluation metrics
 * - multiple linear regression
 * - matrix operations
 * - gradient descent
 * - polynomial regression
 * - ridge regression
 * - categorical encoding
 * - transformations
 * - logistic regression
 * - validation
 * - train/test evaluation
 * - edge cases
 * - production-oriented considerations
 */

// ============================================================
// 1. BASIC UTILITIES
// ============================================================

function section(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function subsection(title) {
    console.log("\n" + "-".repeat(60));
    console.log(title);
    console.log("-".repeat(60));
}

function mean(values) {
    if (values.length === 0) {
        throw new Error("Cannot calculate the mean of an empty array.");
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function sampleVariance(values) {
    if (values.length < 2) {
        throw new Error("At least two observations are required.");
    }

    const average = mean(values);

    return values.reduce(
        (sum, value) => sum + (value - average) ** 2,
        0
    ) / (values.length - 1);
}

function covariance(x, y) {
    if (x.length !== y.length) {
        throw new Error("x and y must have equal lengths.");
    }

    if (x.length < 2) {
        throw new Error("At least two observations are required.");
    }

    const xMean = mean(x);
    const yMean = mean(y);

    return x.reduce(
        (sum, value, index) =>
            sum + (value - xMean) * (y[index] - yMean),
        0
    ) / (x.length - 1);
}

function correlation(x, y) {
    const denominator = Math.sqrt(
        sampleVariance(x) * sampleVariance(y)
    );

    if (denominator === 0) {
        throw new Error(
            "Correlation is undefined when a variable has zero variance."
        );
    }

    return covariance(x, y) / denominator;
}


// ============================================================
// 2. SIMPLE LINEAR REGRESSION
// ============================================================

class SimpleLinearRegression {
    constructor(slope, intercept) {
        this.slope = slope;
        this.intercept = intercept;
    }

    predictOne(x) {
        return this.intercept + this.slope * x;
    }

    predict(values) {
        return values.map(value => this.predictOne(value));
    }

    equation() {
        return `y_hat = ${this.intercept.toFixed(4)} + ` +
            `${this.slope.toFixed(4)} * x`;
    }
}

function fitSimpleLinearRegression(x, y) {
    if (x.length !== y.length) {
        throw new Error("x and y must contain the same number of observations.");
    }

    if (x.length < 2) {
        throw new Error("At least two observations are required.");
    }

    const xMean = mean(x);
    const yMean = mean(y);

    const denominator = x.reduce(
        (sum, value) => sum + (value - xMean) ** 2,
        0
    );

    if (denominator === 0) {
        throw new Error(
            "The predictor has zero variance, so the slope cannot be estimated."
        );
    }

    const slope = x.reduce(
        (sum, value, index) =>
            sum + (value - xMean) * (y[index] - yMean),
        0
    ) / denominator;

    const intercept = yMean - slope * xMean;

    return new SimpleLinearRegression(slope, intercept);
}


// ============================================================
// 3. ERROR METRICS
// ============================================================

function validateEqualLengths(actual, predicted) {
    if (actual.length !== predicted.length) {
        throw new Error("Arrays must have equal lengths.");
    }

    if (actual.length === 0) {
        throw new Error("Arrays cannot be empty.");
    }
}

function mae(actual, predicted) {
    validateEqualLengths(actual, predicted);

    return mean(
        actual.map(
            (value, index) => Math.abs(value - predicted[index])
        )
    );
}

function mse(actual, predicted) {
    validateEqualLengths(actual, predicted);

    return mean(
        actual.map(
            (value, index) => (value - predicted[index]) ** 2
        )
    );
}

function rmse(actual, predicted) {
    return Math.sqrt(mse(actual, predicted));
}

function rSquared(actual, predicted) {
    validateEqualLengths(actual, predicted);

    const actualMean = mean(actual);

    const totalSumOfSquares = actual.reduce(
        (sum, value) => sum + (value - actualMean) ** 2,
        0
    );

    if (totalSumOfSquares === 0) {
        throw new Error(
            "R-squared is undefined when the target has zero variance."
        );
    }

    const residualSumOfSquares = actual.reduce(
        (sum, value, index) =>
            sum + (value - predicted[index]) ** 2,
        0
    );

    return 1 - residualSumOfSquares / totalSumOfSquares;
}


// ============================================================
// 4. BASIC EXAMPLE
// ============================================================

section("REGRESSION FUNDAMENTALS");

const hoursStudied = [1, 2, 3, 4, 5, 6, 7, 8];
const examScores = [52, 55, 61, 66, 70, 74, 79, 85];

console.log("Hours:", hoursStudied);
console.log("Scores:", examScores);
console.log("Mean hours:", mean(hoursStudied).toFixed(4));
console.log("Mean score:", mean(examScores).toFixed(4));
console.log("Correlation:", correlation(
    hoursStudied,
    examScores
).toFixed(4));

const model = fitSimpleLinearRegression(
    hoursStudied,
    examScores
);

console.log("Model:", model.equation());

const predictions = model.predict(hoursStudied);

console.log("MAE:", mae(examScores, predictions).toFixed(4));
console.log("MSE:", mse(examScores, predictions).toFixed(4));
console.log("RMSE:", rmse(examScores, predictions).toFixed(4));
console.log("R²:", rSquared(examScores, predictions).toFixed(4));

console.log("\nNew predictions:");

for (const hours of [2.5, 5.5, 9]) {
    console.log(
        `${hours} hours -> ${model.predictOne(hours).toFixed(2)}`
    );
}


// ============================================================
// 5. RESIDUALS
// ============================================================

section("RESIDUAL ANALYSIS");

const residuals = examScores.map(
    (actual, index) => actual - predictions[index]
);

for (let i = 0; i < hoursStudied.length; i++) {
    console.log(
        `x=${hoursStudied[i]}, actual=${examScores[i]}, ` +
        `predicted=${predictions[i].toFixed(2)}, ` +
        `residual=${residuals[i].toFixed(2)}`
    );
}


// ============================================================
// 6. MATRIX OPERATIONS
// ============================================================

section("MULTIPLE LINEAR REGRESSION FROM FIRST PRINCIPLES");

function transpose(matrix) {
    if (matrix.length === 0) {
        return [];
    }

    return matrix[0].map(
        (_, columnIndex) =>
            matrix.map(row => row[columnIndex])
    );
}

function matrixMultiply(a, b) {
    if (a.length === 0 || b.length === 0) {
        throw new Error("Matrices cannot be empty.");
    }

    if (a[0].length !== b.length) {
        throw new Error("Matrix dimensions are incompatible.");
    }

    const result = Array.from(
        { length: a.length },
        () => Array(b[0].length).fill(0)
    );

    for (let i = 0; i < a.length; i++) {
        for (let j = 0; j < b[0].length; j++) {
            for (let k = 0; k < b.length; k++) {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }

    return result;
}

function identityMatrix(size) {
    return Array.from(
        { length: size },
        (_, row) =>
            Array.from(
                { length: size },
                (_, column) => row === column ? 1 : 0
            )
    );
}

function inverseMatrix(matrix) {
    const n = matrix.length;

    if (
        n === 0 ||
        matrix.some(row => row.length !== n)
    ) {
        throw new Error("Matrix must be non-empty and square.");
    }

    const identity = identityMatrix(n);

    const augmented = matrix.map(
        (row, index) => [...row, ...identity[index]]
    );

    for (let column = 0; column < n; column++) {
        let pivotRow = column;

        for (let row = column + 1; row < n; row++) {
            if (
                Math.abs(augmented[row][column]) >
                Math.abs(augmented[pivotRow][column])
            ) {
                pivotRow = row;
            }
        }

        if (Math.abs(augmented[pivotRow][column]) < 1e-12) {
            throw new Error(
                "Matrix is singular or numerically unstable."
            );
        }

        [augmented[column], augmented[pivotRow]] =
            [augmented[pivotRow], augmented[column]];

        const pivot = augmented[column][column];

        for (let j = 0; j < 2 * n; j++) {
            augmented[column][j] /= pivot;
        }

        for (let row = 0; row < n; row++) {
            if (row === column) {
                continue;
            }

            const factor = augmented[row][column];

            for (let j = 0; j < 2 * n; j++) {
                augmented[row][j] -=
                    factor * augmented[column][j];
            }
        }
    }

    return augmented.map(
        row => row.slice(n)
    );
}

function fitMultipleLinearRegression(features, targets) {
    if (
        features.length === 0 ||
        features.length !== targets.length
    ) {
        throw new Error("Invalid training data.");
    }

    const featureCount = features[0].length;

    if (
        featureCount === 0 ||
        features.some(row => row.length !== featureCount)
    ) {
        throw new Error("Feature dimensions are inconsistent.");
    }

    // Add a column of ones for the intercept.
    const design = features.map(
        row => [1, ...row]
    );

    const xTranspose = transpose(design);

    // Normal equation:
    // beta = (X'X)^(-1) X'y
    const xtx = matrixMultiply(
        xTranspose,
        design
    );

    const xty = matrixMultiply(
        xTranspose,
        targets.map(value => [value])
    );

    const inverse = inverseMatrix(xtx);

    return matrixMultiply(inverse, xty)
        .map(row => row[0]);
}

function predictMultiple(features, coefficients) {
    const expectedFeatures = coefficients.length - 1;

    if (
        features.some(
            row => row.length !== expectedFeatures
        )
    ) {
        throw new Error("Feature dimensions do not match coefficients.");
    }

    return features.map(row =>
        coefficients[0] +
        row.reduce(
            (sum, value, index) =>
                sum + value * coefficients[index + 1],
            0
        )
    );
}

const houseFeatures = [
    [1200, 2, 20],
    [1400, 3, 15],
    [1600, 3, 10],
    [1800, 4, 8],
    [2000, 4, 5],
    [2200, 5, 3]
];

const housePrices = [
    210000,
    250000,
    290000,
    330000,
    370000,
    410000
];

const houseCoefficients = fitMultipleLinearRegression(
    houseFeatures,
    housePrices
);

console.log(
    "Multiple regression coefficients:",
    houseCoefficients.map(value => value.toFixed(4))
);

const housePredictions = predictMultiple(
    houseFeatures,
    houseCoefficients
);

console.log(
    "House RMSE:",
    rmse(housePrices, housePredictions).toFixed(4)
);


// ============================================================
// 7. STANDARDIZATION
// ============================================================

section("FEATURE STANDARDIZATION");

function standardize(values) {
    const average = mean(values);

    const variance = values.reduce(
        (sum, value) =>
            sum + (value - average) ** 2,
        0
    ) / values.length;

    const standardDeviation = Math.sqrt(variance);

    if (standardDeviation === 0) {
        throw new Error(
            "Cannot standardize a constant feature."
        );
    }

    return values.map(
        value =>
            (value - average) / standardDeviation
    );
}

console.log(
    "Standardized hours:",
    standardize(hoursStudied).map(
        value => value.toFixed(3)
    )
);


// ============================================================
// 8. GRADIENT DESCENT
// ============================================================

section("GRADIENT DESCENT");

function gradientDescentLinearRegression(
    x,
    y,
    learningRate = 0.05,
    epochs = 5000
) {
    if (x.length !== y.length || x.length === 0) {
        throw new Error("Invalid training data.");
    }

    if (learningRate <= 0 || epochs <= 0) {
        throw new Error(
            "Learning rate and epochs must be positive."
        );
    }

    const averageX = mean(x);

    const standardDeviation = Math.sqrt(
        x.reduce(
            (sum, value) =>
                sum + (value - averageX) ** 2,
            0
        ) / x.length
    );

    if (standardDeviation === 0) {
        throw new Error(
            "Cannot optimize a constant predictor."
        );
    }

    const scaledX = x.map(
        value =>
            (value - averageX) / standardDeviation
    );

    let weight = 0;
    let bias = mean(y);

    const losses = [];

    for (let epoch = 0; epoch < epochs; epoch++) {
        const predictions = scaledX.map(
            value => weight * value + bias
        );

        const errors = predictions.map(
            (prediction, index) =>
                prediction - y[index]
        );

        const loss = mean(
            errors.map(error => error ** 2)
        );

        losses.push(loss);

        const weightGradient =
            (2 / x.length) *
            errors.reduce(
                (sum, error, index) =>
                    sum + error * scaledX[index],
                0
            );

        const biasGradient =
            (2 / x.length) *
            errors.reduce(
                (sum, error) => sum + error,
                0
            );

        weight -= learningRate * weightGradient;
        bias -= learningRate * biasGradient;
    }

    const originalSlope =
        weight / standardDeviation;

    const originalIntercept =
        bias - originalSlope * averageX;

    return {
        slope: originalSlope,
        intercept: originalIntercept,
        losses
    };
}

const gradientResult =
    gradientDescentLinearRegression(
        hoursStudied,
        examScores
    );

console.log(
    "Gradient descent slope:",
    gradientResult.slope.toFixed(4)
);

console.log(
    "Gradient descent intercept:",
    gradientResult.intercept.toFixed(4)
);

console.log(
    "Final loss:",
    gradientResult.losses.at(-1).toFixed(6)
);


// ============================================================
// 9. POLYNOMIAL REGRESSION
// ============================================================

section("POLYNOMIAL REGRESSION");

function polynomialFeatures(values, degree) {
    if (!Number.isInteger(degree) || degree < 1) {
        throw new Error("Degree must be a positive integer.");
    }

    return values.map(
        value =>
            Array.from(
                { length: degree },
                (_, index) =>
                    value ** (index + 1)
            )
    );
}

const curvedX = [0, 1, 2, 3, 4, 5];
const curvedY = [1.1, 2.8, 6.9, 13.2, 21.1, 31.3];

const curvedFeatures =
    polynomialFeatures(curvedX, 2);

const curvedCoefficients =
    fitMultipleLinearRegression(
        curvedFeatures,
        curvedY
    );

const curvedPredictions =
    predictMultiple(
        curvedFeatures,
        curvedCoefficients
    );

console.log(
    "Polynomial coefficients:",
    curvedCoefficients.map(
        value => value.toFixed(4)
    )
);

console.log(
    "Polynomial RMSE:",
    rmse(curvedY, curvedPredictions).toFixed(4)
);


// ============================================================
// 10. RIDGE REGRESSION
// ============================================================

section("RIDGE REGRESSION");

function ridgeRegression(features, targets, alpha = 1) {
    if (alpha < 0) {
        throw new Error("alpha must be non-negative.");
    }

    const design = features.map(
        row => [1, ...row]
    );

    const xTranspose = transpose(design);

    const xtx = matrixMultiply(
        xTranspose,
        design
    );

    const xty = matrixMultiply(
        xTranspose,
        targets.map(value => [value])
    );

    // L2 penalty is applied to feature coefficients,
    // not the intercept.
    for (let index = 1; index < xtx.length; index++) {
        xtx[index][index] += alpha;
    }

    const inverse = inverseMatrix(xtx);

    return matrixMultiply(
        inverse,
        xty
    ).map(row => row[0]);
}

const ridgeCoefficients =
    ridgeRegression(
        houseFeatures,
        housePrices,
        10
    );

console.log(
    "Ridge coefficients:",
    ridgeCoefficients.map(
        value => value.toFixed(4)
    )
);


// ============================================================
// 11. LOGISTIC REGRESSION CONCEPT
// ============================================================

section("LOGISTIC REGRESSION");

function sigmoid(value) {
    // This branch avoids unnecessary overflow for large negative values.
    if (value >= 0) {
        const exponent = Math.exp(-value);
        return 1 / (1 + exponent);
    }

    const exponent = Math.exp(value);
    return exponent / (1 + exponent);
}

for (const value of [-5, -1, 0, 1, 5]) {
    console.log(
        `sigmoid(${value}) = ${sigmoid(value).toFixed(6)}`
    );
}

console.log(
    "For binary targets, logistic regression models probability " +
    "rather than an unrestricted numeric response."
);


// ============================================================
// 12. CATEGORICAL VARIABLES
// ============================================================

section("ONE-HOT ENCODING");

function oneHotEncode(values, categories = null) {
    const actualCategories =
        categories ??
        [...new Set(values)].sort();

    for (const value of values) {
        if (!actualCategories.includes(value)) {
            throw new Error(
                `Unknown category: ${value}`
            );
        }
    }

    return {
        categories: actualCategories,
        encoded: values.map(
            value =>
                actualCategories.map(
                    category =>
                        value === category ? 1 : 0
                )
        )
    };
}

const cities = [
    "Delhi",
    "Mumbai",
    "Lucknow",
    "Delhi"
];

const encodedCities =
    oneHotEncode(cities);

console.log("Categories:", encodedCities.categories);
console.log("Encoded:", encodedCities.encoded);


// ============================================================
// 13. TRAIN/TEST SPLIT
// ============================================================

section("TRAIN/TEST EVALUATION");

function seededRandom(seed) {
    let state = seed >>> 0;

    return function () {
        state = (
            1664525 * state +
            1013904223
        ) >>> 0;

        return state / 4294967296;
    };
}

function shuffledIndices(length, seed = 42) {
    const indices = Array.from(
        { length },
        (_, index) => index
    );

    const random = seededRandom(seed);

    for (let i = indices.length - 1; i > 0; i--) {
        const j = Math.floor(random() * (i + 1));

        [indices[i], indices[j]] =
            [indices[j], indices[i]];
    }

    return indices;
}

function trainTestSplit(
    x,
    y,
    testRatio = 0.25,
    seed = 42
) {
    if (x.length !== y.length) {
        throw new Error("x and y lengths must match.");
    }

    if (!(testRatio > 0 && testRatio < 1)) {
        throw new Error(
            "testRatio must be between 0 and 1."
        );
    }

    const indices =
        shuffledIndices(x.length, seed);

    const testSize =
        Math.max(
            1,
            Math.round(x.length * testRatio)
        );

    const testIndices =
        indices.slice(0, testSize);

    const trainIndices =
        indices.slice(testSize);

    return {
        xTrain: trainIndices.map(index => x[index]),
        xTest: testIndices.map(index => x[index]),
        yTrain: trainIndices.map(index => y[index]),
        yTest: testIndices.map(index => y[index])
    };
}

const split =
    trainTestSplit(
        hoursStudied,
        examScores,
        0.25,
        42
    );

const splitModel =
    fitSimpleLinearRegression(
        split.xTrain,
        split.yTrain
    );

const trainPredictions =
    splitModel.predict(split.xTrain);

const testPredictions =
    splitModel.predict(split.xTest);

console.log(
    "Train RMSE:",
    rmse(split.yTrain, trainPredictions).toFixed(4)
);

console.log(
    "Test RMSE:",
    rmse(split.yTest, testPredictions).toFixed(4)
);


// ============================================================
// 14. DATA VALIDATION
// ============================================================

section("REGRESSION DATA VALIDATION");

function validateRegressionData(x, y) {
    if (x.length === 0 || y.length === 0) {
        throw new Error("Data cannot be empty.");
    }

    if (x.length !== y.length) {
        throw new Error("x and y lengths must match.");
    }

    for (const value of [...x, ...y]) {
        if (
            typeof value !== "number" ||
            !Number.isFinite(value)
        ) {
            throw new Error(
                "All regression values must be finite numbers."
            );
        }
    }
}

validateRegressionData(
    hoursStudied,
    examScores
);

console.log("Data validation passed.");


// ============================================================
// 15. LOG TRANSFORMATION
// ============================================================

section("LOG TRANSFORMATION");

function logTransform(values) {
    if (values.some(value => value <= 0)) {
        throw new Error(
            "Logarithm requires positive values."
        );
    }

    return values.map(value => Math.log(value));
}

console.log(
    "Log-transformed values:",
    logTransform([1, 2, 4, 8, 16]).map(
        value => value.toFixed(4)
    )
);


// ============================================================
// 16. ASYNCHRONOUS MODEL SCORING
// ============================================================

section("EVENT-DRIVEN / ASYNCHRONOUS JAVASCRIPT");

function scoreModelAsync(model, x, y) {
    /*
     * JavaScript is frequently used in web applications.
     * A model may be loaded from a server or executed after an
     * asynchronous event. This Promise demonstrates how regression
     * output can participate in asynchronous application workflows.
     */
    return new Promise(resolve => {
        setTimeout(() => {
            const predicted = model.predict(x);

            resolve({
                mae: mae(y, predicted),
                rmse: rmse(y, predicted),
                r2: rSquared(y, predicted)
            });
        }, 10);
    });
}

scoreModelAsync(
    model,
    hoursStudied,
    examScores
).then(metrics => {
    console.log(
        "Asynchronous metrics:",
        {
            MAE: metrics.mae.toFixed(4),
            RMSE: metrics.rmse.toFixed(4),
            R2: metrics.r2.toFixed(4)
        }
    );
});


// ============================================================
// 17. EDGE CASES
// ============================================================

section("EDGE CASES");

const edgeCases = [
    [
        "empty data",
        "No model can be estimated."
    ],
    [
        "constant predictor",
        "Slope denominator becomes zero."
    ],
    [
        "constant target",
        "Standard R² is undefined."
    ],
    [
        "perfect multicollinearity",
        "Coefficients may not be uniquely identifiable."
    ],
    [
        "outliers",
        "Least-squares estimates can be strongly affected."
    ],
    [
        "extrapolation",
        "Predictions outside the observed range may be unreliable."
    ],
    [
        "data leakage",
        "Validation performance may become unrealistically optimistic."
    ]
];

for (const [condition, explanation] of edgeCases) {
    console.log(`${condition}: ${explanation}`);
}


// ============================================================
// 18. INTERPRETATION
// ============================================================

section("INTERPRETATION PRINCIPLES");

console.log(`
A slope describes the expected change in the modeled target associated
with a one-unit increase in the predictor, conditional on the model
specification.

An intercept is the predicted target when all predictors are zero.
That value may have little practical meaning if zero is outside the
meaningful feature range.

R² describes explained variation relative to a mean-only baseline.
It does not prove causation and does not guarantee future accuracy.

MAE gives an average absolute error in the target's original units.

RMSE gives greater influence to larger errors because residuals are squared.

Test-set metrics estimate generalization only under the assumptions of
the evaluation design and the representativeness of the test data.
`);


// ============================================================
// 19. FINAL MODEL REPORT
// ============================================================

section("FINAL MODEL REPORT");

function regressionReport(
    model,
    x,
    y
) {
    const predicted = model.predict(x);

    return {
        equation: model.equation(),
        observations: x.length,
        mae: mae(y, predicted),
        mse: mse(y, predicted),
        rmse: rmse(y, predicted),
        r2: rSquared(y, predicted)
    };
}

const report =
    regressionReport(
        model,
        hoursStudied,
        examScores
    );

console.table({
    equation: report.equation,
    observations: report.observations,
    MAE: report.mae.toFixed(4),
    MSE: report.mse.toFixed(4),
    RMSE: report.rmse.toFixed(4),
    R2: report.r2.toFixed(4)
});

console.log("\nRegression study completed.");
