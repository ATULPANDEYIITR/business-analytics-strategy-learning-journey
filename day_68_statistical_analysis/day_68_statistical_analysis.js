"use strict";

/*
 * Statistical Analysis Engine
 *
 * Node.js standard library only.
 *
 * Features:
 * - Numerical data validation
 * - Descriptive statistics
 * - Frequency distributions
 * - Quartiles and percentiles
 * - Sample and population variance
 * - Standard deviation
 * - Pearson correlation
 * - Linear regression
 * - IQR outlier detection
 * - Bootstrap confidence intervals
 * - Asynchronous CSV processing
 * - JSON report generation
 * - Event-driven analysis
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");

class StatisticalError extends Error {
    constructor(message) {
        super(message);
        this.name = "StatisticalError";
    }
}

class DataValidator {
    static validate(data, minimum = 1) {
        if (!Array.isArray(data)) {
            throw new TypeError("Input must be an array.");
        }

        if (data.length < minimum) {
            throw new StatisticalError(
                `At least ${minimum} observations are required.`
            );
        }

        for (const value of data) {
            if (
                typeof value !== "number" ||
                !Number.isFinite(value)
            ) {
                throw new StatisticalError(
                    "All observations must be finite numbers."
                );
            }
        }

        return [...data];
    }

    static paired(x, y) {
        const first = this.validate(x, 2);
        const second = this.validate(y, 2);

        if (first.length !== second.length) {
            throw new StatisticalError(
                "Paired datasets must have equal lengths."
            );
        }

        return [first, second];
    }
}

class Statistics {
    static sum(data) {
        return data.reduce((total, value) => total + value, 0);
    }

    static mean(data) {
        const values = DataValidator.validate(data);
        return this.sum(values) / values.length;
    }

    static median(data) {
        const values = DataValidator.validate(data).sort(
            (a, b) => a - b
        );

        const middle = Math.floor(values.length / 2);

        return values.length % 2 === 0
            ? (values[middle - 1] + values[middle]) / 2
            : values[middle];
    }

    static mode(data) {
        const values = DataValidator.validate(data);
        const frequencies = new Map();

        for (const value of values) {
            frequencies.set(
                value,
                (frequencies.get(value) || 0) + 1
            );
        }

        const maximum = Math.max(...frequencies.values());

        return [...frequencies.entries()]
            .filter(([, count]) => count === maximum)
            .map(([value]) => value)
            .sort((a, b) => a - b);
    }

    static variance(data, sample = true) {
        const values = DataValidator.validate(
            data,
            sample ? 2 : 1
        );

        const average = this.mean(values);
        const squaredDifferences = values.map(
            value => (value - average) ** 2
        );

        return this.sum(squaredDifferences) /
            (values.length - (sample ? 1 : 0));
    }

    static standardDeviation(data, sample = true) {
        return Math.sqrt(this.variance(data, sample));
    }

    static percentile(data, percentage) {
        const values = DataValidator.validate(data).sort(
            (a, b) => a - b
        );

        if (
            !Number.isFinite(percentage) ||
            percentage < 0 ||
            percentage > 100
        ) {
            throw new RangeError(
                "Percentile must be between 0 and 100."
            );
        }

        const position =
            (values.length - 1) * percentage / 100;

        const lower = Math.floor(position);
        const upper = Math.ceil(position);

        if (lower === upper) {
            return values[lower];
        }

        const fraction = position - lower;

        return values[lower] +
            fraction * (values[upper] - values[lower]);
    }

    static quartiles(data) {
        return {
            q1: this.percentile(data, 25),
            q2: this.percentile(data, 50),
            q3: this.percentile(data, 75)
        };
    }

    static frequency(data) {
        const values = DataValidator.validate(data);
        const frequencies = new Map();

        for (const value of values) {
            frequencies.set(
                value,
                (frequencies.get(value) || 0) + 1
            );
        }

        return Object.fromEntries(
            [...frequencies.entries()].sort(
                ([a], [b]) => a - b
            )
        );
    }

    static covariance(x, y) {
        const [first, second] = DataValidator.paired(x, y);

        const meanX = this.mean(first);
        const meanY = this.mean(second);

        return first.reduce(
            (total, value, index) =>
                total + (value - meanX) *
                    (second[index] - meanY),
            0
        ) / (first.length - 1);
    }

    static correlation(x, y) {
        const [first, second] = DataValidator.paired(x, y);

        const stdX = this.standardDeviation(first);
        const stdY = this.standardDeviation(second);

        if (stdX === 0 || stdY === 0) {
            throw new StatisticalError(
                "Correlation is undefined for constant data."
            );
        }

        const result =
            this.covariance(first, second) / (stdX * stdY);

        return Math.max(-1, Math.min(1, result));
    }

    static regression(x, y) {
        const [first, second] = DataValidator.paired(x, y);

        const meanX = this.mean(first);
        const meanY = this.mean(second);

        const denominator = first.reduce(
            (total, value) =>
                total + (value - meanX) ** 2,
            0
        );

        if (denominator === 0) {
            throw new StatisticalError(
                "Independent variable must have variation."
            );
        }

        const numerator = first.reduce(
            (total, value, index) =>
                total + (value - meanX) *
                    (second[index] - meanY),
            0
        );

        const slope = numerator / denominator;
        const intercept = meanY - slope * meanX;

        const predictions = first.map(
            value => slope * value + intercept
        );

        const totalSS = second.reduce(
            (total, value) =>
                total + (value - meanY) ** 2,
            0
        );

        const residualSS = second.reduce(
            (total, value, index) =>
                total + (value - predictions[index]) ** 2,
            0
        );

        return {
            slope,
            intercept,
            rSquared: totalSS === 0
                ? null
                : 1 - residualSS / totalSS
        };
    }

    static outliers(data) {
        const values = DataValidator.validate(data, 2);
        const { q1, q3 } = this.quartiles(values);
        const iqr = q3 - q1;

        const lower = q1 - 1.5 * iqr;
        const upper = q3 + 1.5 * iqr;

        return values.filter(
            value => value < lower || value > upper
        );
    }

    static confidenceInterval(data, z = 1.96) {
        const values = DataValidator.validate(data, 2);

        if (!Number.isFinite(z) || z <= 0) {
            throw new RangeError(
                "Z-score must be positive and finite."
            );
        }

        const average = this.mean(values);
        const standardError =
            this.standardDeviation(values) /
            Math.sqrt(values.length);

        const margin = z * standardError;

        return {
            mean: average,
            standardError,
            lower: average - margin,
            upper: average + margin
        };
    }
}

class BootstrapAnalyzer {
    constructor(seed = 42) {
        this.seed = seed >>> 0;
    }

    // Seeded generator makes bootstrap results reproducible.
    random() {
        this.seed = (
            Math.imul(1664525, this.seed) + 1013904223
        ) >>> 0;

        return this.seed / 4294967296;
    }

    analyze(data, iterations = 2000) {
        const values = DataValidator.validate(data, 2);

        if (
            !Number.isInteger(iterations) ||
            iterations < 100 ||
            iterations > 1000000
        ) {
            throw new RangeError(
                "Iterations must be between 100 and 1,000,000."
            );
        }

        const estimates = new Array(iterations);

        for (let i = 0; i < iterations; i++) {
            let total = 0;

            for (let j = 0; j < values.length; j++) {
                const index = Math.floor(
                    this.random() * values.length
                );

                total += values[index];
            }

            estimates[i] = total / values.length;
        }

        estimates.sort((a, b) => a - b);

        return {
            bootstrapMean: Statistics.mean(estimates),
            lower95: Statistics.percentile(estimates, 2.5),
            upper95: Statistics.percentile(estimates, 97.5),
            iterations
        };
    }
}

class AnalysisService extends EventEmitter {
    constructor() {
        super();
        this.completedReports = new Map();
    }

    async analyze(name, data) {
        if (
            typeof name !== "string" ||
            name.trim().length === 0
        ) {
            throw new StatisticalError(
                "Dataset name cannot be empty."
            );
        }

        const values = DataValidator.validate(data, 2);

        this.emit("analysisStarted", {
            name,
            observations: values.length
        });

        try {
            const quartiles = Statistics.quartiles(values);

            const report = {
                name,
                observations: values.length,
                mean: Statistics.mean(values),
                median: Statistics.median(values),
                mode: Statistics.mode(values),
                minimum: Math.min(...values),
                maximum: Math.max(...values),
                range: Math.max(...values) - Math.min(...values),
                sampleVariance: Statistics.variance(values),
                populationVariance: Statistics.variance(
                    values,
                    false
                ),
                sampleStandardDeviation:
                    Statistics.standardDeviation(values),
                populationStandardDeviation:
                    Statistics.standardDeviation(values, false),
                quartiles,
                frequency: Statistics.frequency(values),
                outliers: Statistics.outliers(values),
                confidenceInterval:
                    Statistics.confidenceInterval(values)
            };

            this.completedReports.set(name, report);

            this.emit("analysisCompleted", report);

            return report;
        } catch (error) {
            this.emit("analysisFailed", { name, error });
            throw error;
        }
    }

    getReport(name) {
        return this.completedReports.get(name) || null;
    }
}

class CSVReader {
    static async readColumn(filename, columnName) {
        const content = await fs.readFile(filename, "utf8");
        const lines = content.trim().split(/\r?\n/);

        if (lines.length < 2) {
            throw new StatisticalError(
                "CSV must contain a header and observations."
            );
        }

        const headers = lines[0].split(",").map(
            value => value.trim()
        );

        const columnIndex = headers.indexOf(columnName);

        if (columnIndex === -1) {
            throw new StatisticalError(
                `Column '${columnName}' does not exist.`
            );
        }

        const values = [];

        for (let i = 1; i < lines.length; i++) {
            const fields = lines[i].split(",");
            const raw = fields[columnIndex]?.trim();

            if (raw === undefined || raw === "") {
                throw new StatisticalError(
                    `Missing value on CSV line ${i + 1}.`
                );
            }

            const value = Number(raw);

            if (!Number.isFinite(value)) {
                throw new StatisticalError(
                    `Invalid numeric value on CSV line ${i + 1}.`
                );
            }

            values.push(value);
        }

        return DataValidator.validate(values, 2);
    }
}

async function exportReport(report, filename) {
    const destination = path.resolve(filename);

    await fs.writeFile(
        destination,
        JSON.stringify(report, null, 2),
        { encoding: "utf8", mode: 0o600 }
    );

    return destination;
}

function runTests() {
    const data = [10, 20, 20, 30, 40];

    console.assert(Statistics.mean(data) === 24);
    console.assert(Statistics.median(data) === 20);
    console.assert(Statistics.mode(data)[0] === 20);

    console.assert(
        Math.abs(
            Statistics.correlation([1, 2, 3], [2, 4, 6]) - 1
        ) < 1e-10
    );

    let rejected = false;

    try {
        Statistics.mean([1, NaN, 3]);
    } catch (error) {
        rejected = error instanceof StatisticalError;
    }

    if (!rejected) {
        throw new Error("Invalid data test failed.");
    }

    console.log("All statistical tests passed.");
}

async function main() {
    const service = new AnalysisService();

    service.on("analysisStarted", event => {
        console.log(
            `Started: ${event.name} (${event.observations} observations)`
        );
    });

    service.on("analysisCompleted", report => {
        console.log(`Completed: ${report.name}`);
    });

    service.on("analysisFailed", event => {
        console.error(
            `Failed: ${event.name}: ${event.error.message}`
        );
    });

    const scores = [
        45, 52, 56, 60, 62, 65, 67, 68,
        70, 72, 72, 75, 78, 80, 82, 85,
        88, 90, 92, 95, 98, 100, 105, 150
    ];

    const report = await service.analyze(
        "Examination Scores",
        scores
    );

    console.log("\nDESCRIPTIVE REPORT");
    console.log(JSON.stringify(report, null, 2));

    const hours = [
        1, 2, 2, 3, 3, 4, 4, 5,
        5, 6, 6, 7, 7, 8, 8, 9
    ];

    const performance = [
        35, 42, 45, 48, 52, 55, 58, 62,
        65, 68, 70, 74, 77, 81, 85, 90
    ];

    console.log("\nCORRELATION");
    console.log(Statistics.correlation(hours, performance));

    console.log("\nREGRESSION");
    console.log(
        JSON.stringify(
            Statistics.regression(hours, performance),
            null,
            2
        )
    );

    console.log("\nBOOTSTRAP");
    console.log(
        new BootstrapAnalyzer(42).analyze(scores, 2000)
    );

    const output = await exportReport(
        report,
        "statistical_report.json"
    );

    console.log(`\nReport saved: ${output}`);

    runTests();
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
