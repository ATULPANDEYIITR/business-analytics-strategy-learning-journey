/*
 * Sampling: Population, Samples and Sampling Techniques
 *
 * This self-contained JavaScript program demonstrates:
 * - Population and sample
 * - Parameters and statistics
 * - Simple random sampling
 * - Systematic sampling
 * - Stratified sampling
 * - Cluster and multistage sampling
 * - Convenience and quota sampling
 * - Sample-size estimation
 * - Sampling error
 * - Confidence intervals
 * - Weighted estimation
 * - Repeated sampling and sampling distributions
 * - Validation and edge cases
 *
 * Compatible with modern Node.js.
 */

"use strict";

// ---------------------------------------------------------------------------
// 1. REPRODUCIBLE RANDOM NUMBER GENERATOR
// ---------------------------------------------------------------------------

// JavaScript's Math.random() cannot be seeded directly.
// A small deterministic generator makes demonstrations reproducible.
class SeededRandom {
    constructor(seed = 42) {
        this.state = seed >>> 0;
    }

    next() {
        this.state = (1664525 * this.state + 1013904223) >>> 0;
        return this.state / 4294967296;
    }

    integer(min, max) {
        return Math.floor(this.next() * (max - min + 1)) + min;
    }

    choice(array) {
        return array[this.integer(0, array.length - 1)];
    }

    shuffle(array) {
        const copy = [...array];

        for (let i = copy.length - 1; i > 0; i--) {
            const j = this.integer(0, i);
            [copy[i], copy[j]] = [copy[j], copy[i]];
        }

        return copy;
    }

    sample(array, size) {
        if (size < 0 || size > array.length) {
            throw new RangeError("Invalid sample size.");
        }

        return this.shuffle(array).slice(0, size);
    }
}

// ---------------------------------------------------------------------------
// 2. POPULATION MODEL
// ---------------------------------------------------------------------------

function buildPopulation(size = 3000, seed = 42) {
    if (!Number.isInteger(size) || size <= 0) {
        throw new RangeError("Population size must be positive.");
    }

    const random = new SeededRandom(seed);
    const regions = ["North", "South", "East", "West"];
    const employmentTypes = [
        "Student",
        "Employed",
        "Self-employed",
        "Unemployed"
    ];
    const population = [];

    for (let id = 1; id <= size; id++) {
        const region = weightedChoice(
            random,
            regions,
            [0.35, 0.25, 0.20, 0.20]
        );

        const employment = weightedChoice(
            random,
            employmentTypes,
            [0.15, 0.50, 0.25, 0.10]
        );

        const age = random.integer(18, 70);

        const incomeBase = {
            Student: 12000,
            Employed: 50000,
            "Self-employed": 60000,
            Unemployed: 10000
        }[employment];

        // Uniform noise is sufficient for this educational simulation.
        const income = Math.max(
            0,
            incomeBase + (random.next() - 0.5) * incomeBase
        );

        const satisfaction = clamp(
            6 + income / 200000 + (random.next() - 0.5) * 3,
            1,
            10
        );

        const cluster = `District-${String(((id - 1) % 15) + 1).padStart(2, "0")}`;

        population.push({
            id,
            age,
            region,
            employment,
            income,
            satisfaction,
            cluster
        });
    }

    return population;
}

function weightedChoice(random, values, weights) {
    const total = weights.reduce((sum, weight) => sum + weight, 0);
    let target = random.next() * total;

    for (let i = 0; i < values.length; i++) {
        target -= weights[i];

        if (target <= 0) {
            return values[i];
        }
    }

    return values[values.length - 1];
}

function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
}

// ---------------------------------------------------------------------------
// 3. BASIC STATISTICS
// ---------------------------------------------------------------------------

function arithmeticMean(values) {
    if (values.length === 0) {
        throw new Error("Cannot calculate a mean of an empty array.");
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function sampleStandardDeviation(values) {
    if (values.length < 2) {
        return 0;
    }

    const average = arithmeticMean(values);
    const squaredDifferences = values.map(
        value => (value - average) ** 2
    );

    return Math.sqrt(
        squaredDifferences.reduce((sum, value) => sum + value, 0)
        / (values.length - 1)
    );
}

function median(values) {
    if (values.length === 0) {
        throw new Error("Cannot calculate a median of an empty array.");
    }

    const sorted = [...values].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);

    return sorted.length % 2 === 0
        ? (sorted[middle - 1] + sorted[middle]) / 2
        : sorted[middle];
}

function validateSampleSize(populationSize, sampleSize) {
    if (!Number.isInteger(sampleSize) || sampleSize <= 0) {
        throw new RangeError("Sample size must be a positive integer.");
    }

    if (sampleSize > populationSize) {
        throw new RangeError(
            "Sample size cannot exceed population size."
        );
    }
}

// ---------------------------------------------------------------------------
// 4. SIMPLE RANDOM SAMPLING
// ---------------------------------------------------------------------------

function simpleRandomSample(population, sampleSize, seed = 42) {
    validateSampleSize(population.length, sampleSize);

    const random = new SeededRandom(seed);
    return random.sample(population, sampleSize);
}

// ---------------------------------------------------------------------------
// 5. SYSTEMATIC SAMPLING
// ---------------------------------------------------------------------------

function systematicSample(population, sampleSize, seed = 42) {
    validateSampleSize(population.length, sampleSize);

    const random = new SeededRandom(seed);
    const interval = population.length / sampleSize;
    const start = random.next() * interval;

    const result = [];

    for (let i = 0; i < sampleSize; i++) {
        const index = Math.min(
            population.length - 1,
            Math.floor(start + i * interval)
        );

        result.push(population[index]);
    }

    return result;
}

// ---------------------------------------------------------------------------
// 6. STRATIFIED SAMPLING
// ---------------------------------------------------------------------------

function stratifiedSample(
    population,
    sampleSize,
    attributeFunction,
    seed = 42
) {
    validateSampleSize(population.length, sampleSize);

    const random = new SeededRandom(seed);
    const strata = new Map();

    for (const person of population) {
        const key = attributeFunction(person);

        if (!strata.has(key)) {
            strata.set(key, []);
        }

        strata.get(key).push(person);
    }

    const allocations = new Map();
    let allocated = 0;

    for (const [key, units] of strata.entries()) {
        const allocation = Math.floor(
            units.length / population.length * sampleSize
        );

        allocations.set(key, allocation);
        allocated += allocation;
    }

    // Distribute rounding remainder.
    const keys = [...strata.keys()];
    let cursor = 0;

    while (allocated < sampleSize) {
        const key = keys[cursor % keys.length];

        if (allocations.get(key) < strata.get(key).length) {
            allocations.set(key, allocations.get(key) + 1);
            allocated++;
        }

        cursor++;
    }

    const result = [];

    for (const [key, units] of strata.entries()) {
        result.push(
            ...random.sample(units, allocations.get(key))
        );
    }

    return random.shuffle(result);
}

// ---------------------------------------------------------------------------
// 7. CLUSTER SAMPLING
// ---------------------------------------------------------------------------

function groupBy(population, keyFunction) {
    const groups = new Map();

    for (const item of population) {
        const key = keyFunction(item);

        if (!groups.has(key)) {
            groups.set(key, []);
        }

        groups.get(key).push(item);
    }

    return groups;
}

function clusterSample(population, clusterCount, seed = 42) {
    const clusters = groupBy(population, person => person.cluster);

    if (clusterCount <= 0 || clusterCount > clusters.size) {
        throw new RangeError("Invalid cluster count.");
    }

    const random = new SeededRandom(seed);
    const names = random.sample([...clusters.keys()], clusterCount);
    const result = [];

    for (const name of names) {
        result.push(...clusters.get(name));
    }

    return result;
}

// ---------------------------------------------------------------------------
// 8. MULTISTAGE SAMPLING
// ---------------------------------------------------------------------------

function multistageSample(
    population,
    clusterCount,
    peoplePerCluster,
    seed = 42
) {
    const clusters = groupBy(population, person => person.cluster);

    if (clusterCount <= 0 || clusterCount > clusters.size) {
        throw new RangeError("Invalid cluster count.");
    }

    if (peoplePerCluster <= 0) {
        throw new RangeError("People per cluster must be positive.");
    }

    const random = new SeededRandom(seed);
    const selectedNames = random.sample(
        [...clusters.keys()],
        clusterCount
    );

    const result = [];

    for (const name of selectedNames) {
        const units = clusters.get(name);
        const count = Math.min(peoplePerCluster, units.length);

        result.push(...random.sample(units, count));
    }

    return result;
}

// ---------------------------------------------------------------------------
// 9. NON-PROBABILITY SAMPLING
// ---------------------------------------------------------------------------

function convenienceSample(population, sampleSize) {
    validateSampleSize(population.length, sampleSize);

    // Accessibility is the selection mechanism rather than randomization.
    return population.slice(0, sampleSize);
}

function quotaSample(population, sampleSize, attributeFunction, quotas) {
    const quotaTotal = Object.values(quotas)
        .reduce((sum, value) => sum + value, 0);

    if (quotaTotal !== sampleSize) {
        throw new RangeError("Quota total must equal sample size.");
    }

    const result = [];

    for (const [category, quota] of Object.entries(quotas)) {
        const candidates = population.filter(
            person => attributeFunction(person) === category
        );

        if (candidates.length < quota) {
            throw new RangeError(
                `Not enough units for quota ${category}.`
            );
        }

        result.push(...candidates.slice(0, quota));
    }

    return result;
}

// ---------------------------------------------------------------------------
// 10. ESTIMATION
// ---------------------------------------------------------------------------

function meanIncome(sample) {
    return arithmeticMean(sample.map(person => person.income));
}

function samplingError(populationMean, estimate) {
    return estimate - populationMean;
}

function weightedMean(observations) {
    if (observations.length === 0) {
        throw new Error("Observations cannot be empty.");
    }

    const totalWeight = observations
        .reduce((sum, observation) => sum + observation.weight, 0);

    if (totalWeight <= 0) {
        throw new Error("Total weight must be positive.");
    }

    return observations.reduce(
        (sum, observation) =>
            sum + observation.value * observation.weight,
        0
    ) / totalWeight;
}

// ---------------------------------------------------------------------------
// 11. SAMPLE SIZE
// ---------------------------------------------------------------------------

function cochranSampleSize(
    z,
    proportion,
    marginOfError,
    populationSize = null
) {
    if (z <= 0) {
        throw new RangeError("Z value must be positive.");
    }

    if (proportion <= 0 || proportion >= 1) {
        throw new RangeError("Proportion must be between 0 and 1.");
    }

    if (marginOfError <= 0 || marginOfError >= 1) {
        throw new RangeError(
            "Margin of error must be between 0 and 1."
        );
    }

    const n0 =
        (z ** 2 * proportion * (1 - proportion))
        / marginOfError ** 2;

    if (populationSize === null) {
        return Math.ceil(n0);
    }

    if (populationSize <= 0) {
        throw new RangeError("Population size must be positive.");
    }

    const corrected =
        n0 / (1 + (n0 - 1) / populationSize);

    return Math.min(populationSize, Math.ceil(corrected));
}

// ---------------------------------------------------------------------------
// 12. CONFIDENCE INTERVAL
// ---------------------------------------------------------------------------

function confidenceIntervalForMean(values, z = 1.96) {
    if (values.length < 2) {
        throw new Error(
            "At least two observations are required."
        );
    }

    const average = arithmeticMean(values);
    const standardError =
        sampleStandardDeviation(values) / Math.sqrt(values.length);

    const margin = z * standardError;

    return {
        mean: average,
        standardError,
        lower: average - margin,
        upper: average + margin
    };
}

// ---------------------------------------------------------------------------
// 13. SAMPLING DISTRIBUTION
// ---------------------------------------------------------------------------

function simulateSamplingDistribution(
    population,
    sampleSize,
    repetitions = 200
) {
    if (repetitions <= 0) {
        throw new RangeError("Repetitions must be positive.");
    }

    const estimates = [];

    for (let i = 0; i < repetitions; i++) {
        const sample = simpleRandomSample(
            population,
            sampleSize,
            100 + i
        );

        estimates.push(meanIncome(sample));
    }

    return {
        meanOfEstimates: arithmeticMean(estimates),
        standardDeviationOfEstimates:
            sampleStandardDeviation(estimates),
        minimum: Math.min(...estimates),
        maximum: Math.max(...estimates)
    };
}

// ---------------------------------------------------------------------------
// 14. REPORTING
// ---------------------------------------------------------------------------

function printSection(title) {
    console.log(`\n${"=".repeat(60)}`);
    console.log(title);
    console.log("=".repeat(60));
}

function run() {
    const population = buildPopulation(3000, 42);
    const populationMean = arithmeticMean(
        population.map(person => person.income)
    );

    printSection("POPULATION");
    console.log(`Population size: ${population.length}`);
    console.log(
        `Population mean income: ${populationMean.toFixed(2)}`
    );

    printSection("SIMPLE RANDOM SAMPLING");
    const randomSample = simpleRandomSample(population, 200, 10);
    const randomEstimate = meanIncome(randomSample);

    console.log(`Sample size: ${randomSample.length}`);
    console.log(`Estimate: ${randomEstimate.toFixed(2)}`);
    console.log(
        `Sampling error: ${
            samplingError(populationMean, randomEstimate).toFixed(2)
        }`
    );

    printSection("SYSTEMATIC SAMPLING");
    const systematic = systematicSample(population, 200, 20);
    console.log(
        `Estimate: ${meanIncome(systematic).toFixed(2)}`
    );

    printSection("STRATIFIED SAMPLING");
    const stratified = stratifiedSample(
        population,
        200,
        person => person.region,
        30
    );

    console.log(
        `Estimate: ${meanIncome(stratified).toFixed(2)}`
    );

    const regionalComposition = groupBy(
        stratified,
        person => person.region
    );

    for (const [region, units] of regionalComposition) {
        console.log(`${region}: ${units.length}`);
    }

    printSection("CLUSTER SAMPLING");
    const clusters = clusterSample(population, 3, 40);
    console.log(`Observed units: ${clusters.length}`);
    console.log(
        `Estimate: ${meanIncome(clusters).toFixed(2)}`
    );

    printSection("MULTISTAGE SAMPLING");
    const multistage = multistageSample(
        population,
        5,
        20,
        50
    );

    console.log(`Final sample size: ${multistage.length}`);
    console.log(
        `Estimate: ${meanIncome(multistage).toFixed(2)}`
    );

    printSection("NON-PROBABILITY SAMPLING");
    const convenience = convenienceSample(
        population,
        100
    );

    console.log(
        `Convenience estimate: ${meanIncome(convenience).toFixed(2)}`
    );

    const quota = quotaSample(
        population,
        100,
        person => person.region,
        {
            North: 35,
            South: 25,
            East: 20,
            West: 20
        }
    );

    console.log(
        `Quota estimate: ${meanIncome(quota).toFixed(2)}`
    );

    printSection("SAMPLE SIZE");
    console.log(
        `Required sample: ${cochranSampleSize(
            1.96,
            0.5,
            0.05,
            population.length
        )}`
    );

    printSection("CONFIDENCE INTERVAL");
    const interval = confidenceIntervalForMean(
        randomSample.map(person => person.income)
    );

    console.log(`Mean: ${interval.mean.toFixed(2)}`);
    console.log(`SE: ${interval.standardError.toFixed(2)}`);
    console.log(
        `Approximate 95% CI: ${
            interval.lower.toFixed(2)
        } to ${
            interval.upper.toFixed(2)
        }`
    );

    printSection("WEIGHTED ESTIMATION");
    const weighted = weightedMean([
        { value: 100, weight: 1 },
        { value: 200, weight: 2 },
        { value: 300, weight: 1 }
    ]);

    console.log(`Weighted mean: ${weighted.toFixed(2)}`);

    printSection("SAMPLING DISTRIBUTION");
    const distribution = simulateSamplingDistribution(
        population,
        100,
        200
    );

    console.log(
        `Mean of sample means: ${
            distribution.meanOfEstimates.toFixed(2)
        }`
    );
    console.log(
        `SD of sample means: ${
            distribution.standardDeviationOfEstimates.toFixed(2)
        }`
    );

    printSection("EDGE CASE");
    try {
        simpleRandomSample(population, population.length + 1);
    } catch (error) {
        console.log(`Validation caught: ${error.message}`);
    }

    printSection("INTERPRETATION");
    console.log(
        "A sample statistic estimates a population parameter."
    );
    console.log(
        "Randomization controls selection probability; it does not eliminate every source of error."
    );
    console.log(
        "A representative-looking sample is not automatically a probability sample."
    );
}

run();
