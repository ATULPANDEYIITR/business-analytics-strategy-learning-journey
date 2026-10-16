"use strict";

/*
 * Exploratory Data Analysis in Node.js.
 *
 * The implementation focuses on a time-series sales dataset. JavaScript is
 * used here to model event-driven analytical processing: observations arrive
 * as records, transformations produce derived metrics, and policy-like
 * anomaly events are emitted when analytical thresholds are crossed.
 */

const fs = require("node:fs/promises");
const EventEmitter = require("node:events");

class DataValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "DataValidationError";
    }
}

function validateObservation(observation) {
    if (!observation || typeof observation !== "object") {
        throw new DataValidationError("Observation must be an object.");
    }

    const timestamp = new Date(observation.timestamp);
    const value = Number(observation.value);

    if (Number.isNaN(timestamp.getTime())) {
        throw new DataValidationError("Invalid timestamp.");
    }

    if (!Number.isFinite(value)) {
        throw new DataValidationError("Value must be finite.");
    }

    if (!observation.region || !observation.category) {
        throw new DataValidationError("Region and category are required.");
    }

    return {
        timestamp,
        value,
        region: String(observation.region),
        category: String(observation.category),
    };
}

function mean(values) {
    if (!values.length) {
        throw new DataValidationError("Mean requires at least one value.");
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function median(values) {
    if (!values.length) {
        throw new DataValidationError("Median requires at least one value.");
    }

    const sorted = [...values].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);

    return sorted.length % 2 === 0
        ? (sorted[middle - 1] + sorted[middle]) / 2
        : sorted[middle];
}

function percentile(values, p) {
    if (!values.length || p < 0 || p > 100) {
        throw new DataValidationError("Invalid percentile request.");
    }

    const sorted = [...values].sort((a, b) => a - b);
    const position = (sorted.length - 1) * p / 100;
    const lower = Math.floor(position);
    const upper = Math.ceil(position);

    if (lower === upper) {
        return sorted[lower];
    }

    const fraction = position - lower;
    return sorted[lower] +
        (sorted[upper] - sorted[lower]) * fraction;
}

function standardDeviation(values) {
    if (values.length < 2) {
        return 0;
    }

    const average = mean(values);
    const variance = values.reduce(
        (sum, value) => sum + (value - average) ** 2,
        0
    ) / (values.length - 1);

    return Math.sqrt(variance);
}

function correlation(first, second) {
    if (first.length !== second.length || first.length < 2) {
        throw new DataValidationError(
            "Correlation requires paired observations."
        );
    }

    const firstMean = mean(first);
    const secondMean = mean(second);

    let numerator = 0;
    let firstSquared = 0;
    let secondSquared = 0;

    for (let index = 0; index < first.length; index++) {
        const firstDelta = first[index] - firstMean;
        const secondDelta = second[index] - secondMean;

        numerator += firstDelta * secondDelta;
        firstSquared += firstDelta ** 2;
        secondSquared += secondDelta ** 2;
    }

    const denominator = Math.sqrt(firstSquared * secondSquared);
    return denominator === 0 ? 0 : numerator / denominator;
}

function movingAverage(values, windowSize) {
    if (windowSize <= 0 || windowSize > values.length) {
        throw new DataValidationError("Invalid moving-average window.");
    }

    const result = [];

    for (let index = windowSize - 1; index < values.length; index++) {
        result.push(
            mean(values.slice(index - windowSize + 1, index + 1))
        );
    }

    return result;
}

function linearTrend(values) {
    if (values.length < 2) {
        throw new DataValidationError(
            "At least two observations are required for a trend."
        );
    }

    const xMean = (values.length - 1) / 2;
    const yMean = mean(values);

    let numerator = 0;
    let denominator = 0;

    for (let index = 0; index < values.length; index++) {
        numerator += (index - xMean) * (values[index] - yMean);
        denominator += (index - xMean) ** 2;
    }

    const slope = numerator / denominator;
    const intercept = yMean - slope * xMean;

    return { slope, intercept };
}

function detectIqrOutliers(values) {
    const q1 = percentile(values, 25);
    const q3 = percentile(values, 75);
    const iqr = q3 - q1;

    const lower = q1 - 1.5 * iqr;
    const upper = q3 + 1.5 * iqr;

    return values
        .map((value, index) => ({ index, value }))
        .filter(({ value }) => value < lower || value > upper);
}

function aggregateBy(observations, keyFunction) {
    const groups = new Map();

    for (const observation of observations) {
        const key = keyFunction(observation);

        if (!groups.has(key)) {
            groups.set(key, []);
        }

        groups.get(key).push(observation.value);
    }

    return new Map(
        [...groups.entries()].map(([key, values]) => [
            key,
            mean(values),
        ])
    );
}

class AnomalyMonitor extends EventEmitter {
    constructor(options = {}) {
        super();
        this.threshold = options.threshold ?? 2.5;
        this.window = options.window ?? 3;
    }

    analyse(values, labels) {
        if (values.length !== labels.length) {
            throw new DataValidationError("Values and labels must align.");
        }

        for (let index = 0; index < values.length; index++) {
            const start = Math.max(0, index - this.window);
            const end = Math.min(values.length, index + this.window + 1);

            const neighborhood = values.filter(
                (_, candidateIndex) =>
                    candidateIndex >= start &&
                    candidateIndex < end &&
                    candidateIndex !== index
            );

            if (neighborhood.length < 2) {
                continue;
            }

            const localMean = mean(neighborhood);
            const localStd = standardDeviation(neighborhood);

            if (localStd === 0) {
                continue;
            }

            const localScore =
                Math.abs(values[index] - localMean) / localStd;

            if (localScore >= this.threshold) {
                this.emit("anomaly", {
                    index,
                    label: labels[index],
                    value: values[index],
                    localScore,
                });
            }
        }
    }
}

function generateData() {
    const observations = [];
    const regions = ["North", "South", "West"];
    const categories = ["Enterprise", "SMB"];
    const start = new Date("2026-01-01T00:00:00Z");

    function randomNormal() {
        const first = Math.random() || Number.EPSILON;
        const second = Math.random();
        return Math.sqrt(-2 * Math.log(first)) *
            Math.cos(2 * Math.PI * second);
    }

    for (let day = 0; day < 90; day++) {
        const timestamp = new Date(start);
        timestamp.setUTCDate(start.getUTCDate() + day);

        for (let regionIndex = 0; regionIndex < regions.length; regionIndex++) {
            for (
                let categoryIndex = 0;
                categoryIndex < categories.length;
                categoryIndex++
            ) {
                const seasonal =
                    12 * Math.sin((2 * Math.PI * day) / 30);
                const growth = day * 0.18;

                let value =
                    100 +
                    regionIndex * 12 +
                    categoryIndex * 20 +
                    seasonal +
                    growth +
                    randomNormal() * 5;

                if (
                    day === 53 &&
                    regions[regionIndex] === "West" &&
                    categories[categoryIndex] === "Enterprise"
                ) {
                    value += 65;
                }

                if (
                    day === 71 &&
                    regions[regionIndex] === "South" &&
                    categories[categoryIndex] === "SMB"
                ) {
                    value -= 55;
                }

                observations.push({
                    timestamp: timestamp.toISOString(),
                    value: Number(value.toFixed(2)),
                    region: regions[regionIndex],
                    category: categories[categoryIndex],
                });
            }
        }
    }

    return observations.map(validateObservation);
}

function dailyAggregation(observations) {
    const groups = aggregateBy(
        observations,
        observation => observation.timestamp.toISOString().slice(0, 10)
    );

    return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
}

function describe(values) {
    const q1 = percentile(values, 25);
    const q3 = percentile(values, 75);

    return {
        count: values.length,
        mean: mean(values),
        median: median(values),
        minimum: Math.min(...values),
        maximum: Math.max(...values),
        q1,
        q3,
        iqr: q3 - q1,
        standardDeviation: standardDeviation(values),
    };
}

async function writeCsv(observations, path) {
    const header = "timestamp,value,region,category\n";

    const body = observations
        .map(observation =>
            [
                observation.timestamp.toISOString(),
                observation.value.toFixed(2),
                observation.region,
                observation.category,
            ].join(",")
        )
        .join("\n");

    await fs.writeFile(path, header + body + "\n", "utf8");
}

async function main() {
    const observations = generateData();
    const values = observations.map(observation => observation.value);

    console.log("Exploratory Data Analysis");
    console.log("==========================");
    console.log("Records:", observations.length);

    console.log("\nDistribution");
    console.table(describe(values));

    const daily = dailyAggregation(observations);
    const dailyLabels = daily.map(([date]) => date);
    const dailyValues = daily.map(([, value]) => value);

    const trend = linearTrend(dailyValues);
    console.log("\nTrend");
    console.log(`Slope: ${trend.slope.toFixed(4)}`);
    console.log(`Intercept: ${trend.intercept.toFixed(4)}`);

    const averages = movingAverage(dailyValues, 7);
    console.log(
        `Latest seven-day moving average: ${
            averages.at(-1).toFixed(3)
        }`
    );

    const iqrOutliers = detectIqrOutliers(values);
    console.log(`\nGlobal IQR outliers: ${iqrOutliers.length}`);

    const monitor = new AnomalyMonitor({
        threshold: 2.5,
        window: 3,
    });

    monitor.on("anomaly", event => {
        console.log(
            `Local anomaly: ${event.label} | ` +
            `value=${event.value.toFixed(2)} | ` +
            `score=${event.localScore.toFixed(2)}`
        );
    });

    console.log("\nLocal anomaly events");
    monitor.analyse(dailyValues, dailyLabels);

    console.log("\nRegional means");
    for (const [region, value] of aggregateBy(
        observations,
        observation => observation.region
    )) {
        console.log(`${region}: ${value.toFixed(2)}`);
    }

    console.log("\nCategory means");
    for (const [category, value] of aggregateBy(
        observations,
        observation => observation.category
    )) {
        console.log(`${category}: ${value.toFixed(2)}`);
    }

    const firstPeriod = dailyValues.slice(0, 45);
    const secondPeriod = dailyValues.slice(45);

    console.log("\nPeriod shift");
    console.log("First mean :", mean(firstPeriod).toFixed(2));
    console.log("Second mean:", mean(secondPeriod).toFixed(2));
    console.log(
        "Percentage change:",
        (
            (mean(secondPeriod) - mean(firstPeriod)) /
            mean(firstPeriod) *
            100
        ).toFixed(2) + "%"
    );

    const enterprise = aggregateBy(
        observations.filter(
            observation => observation.category === "Enterprise"
        ),
        observation => observation.timestamp.toISOString().slice(0, 10)
    );

    const west = aggregateBy(
        observations.filter(
            observation => observation.region === "West"
        ),
        observation => observation.timestamp.toISOString().slice(0, 10)
    );

    const dates = [...enterprise.keys()]
        .filter(date => west.has(date))
        .sort();

    const enterpriseValues = dates.map(date => enterprise.get(date));
    const westValues = dates.map(date => west.get(date));

    console.log(
        "\nEnterprise/West correlation:",
        correlation(enterpriseValues, westValues).toFixed(3)
    );

    const outputPath = "eda_sales_observations.csv";
    await writeCsv(observations, outputPath);
    console.log(`\nData written to ${outputPath}`);
}

main().catch(error => {
    console.error("EDA execution failed:", error.message);
    process.exitCode = 1;
});
