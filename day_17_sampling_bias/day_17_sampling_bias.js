/*
Sampling Bias: Selection Bias, Survivorship Bias, and Sampling Errors
======================================================================

Self-contained JavaScript study program covering:
- population, sample, parameter, statistic
- sampling error
- selection bias
- undercoverage
- convenience sampling
- nonresponse bias
- survivorship bias
- collider bias
- bias versus variance
- stratified sampling
- inverse-probability weighting
- bootstrap uncertainty
- sensitivity analysis
- validation and edge cases

Run with:
    node sampling_bias.js
*/

"use strict";

// -----------------------------------------------------------------------------
// 1. Utility functions
// -----------------------------------------------------------------------------

function printSection(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function mean(values) {
    if (values.length === 0) {
        throw new Error("Mean requires at least one value.");
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function variance(values) {
    if (values.length < 2) {
        throw new Error("Variance requires at least two observations.");
    }

    const average = mean(values);
    return (
        values.reduce(
            (sum, value) => sum + (value - average) ** 2,
            0
        ) / (values.length - 1)
    );
}

function standardDeviation(values) {
    return Math.sqrt(variance(values));
}

function randomNormal(random) {
    // Box-Muller transformation converts uniform random variables into
    // approximately standard-normal random variables.
    let u1 = 0;
    let u2 = 0;

    while (u1 === 0) {
        u1 = random();
    }

    while (u2 === 0) {
        u2 = random();
    }

    return Math.sqrt(-2 * Math.log(u1)) *
        Math.cos(2 * Math.PI * u2);
}

function normal(random, meanValue, standardDeviationValue) {
    return meanValue + standardDeviationValue * randomNormal(random);
}

// A small deterministic pseudo-random generator keeps examples reproducible.
function createRandom(seed = 123456789) {
    let state = seed >>> 0;

    return function random() {
        state = (1664525 * state + 1013904223) >>> 0;
        return state / 4294967296;
    };
}

function sampleWithoutReplacement(values, sampleSize, random) {
    if (sampleSize < 1 || sampleSize > values.length) {
        throw new Error("Invalid sample size.");
    }

    const copy = [...values];

    for (let index = copy.length - 1; index > 0; index--) {
        const swapIndex = Math.floor(random() * (index + 1));
        [copy[index], copy[swapIndex]] = [copy[swapIndex], copy[index]];
    }

    return copy.slice(0, sampleSize);
}

function pearsonCorrelation(x, y) {
    if (x.length !== y.length || x.length < 2) {
        throw new Error("Correlation requires equal non-trivial arrays.");
    }

    const meanX = mean(x);
    const meanY = mean(y);

    let numerator = 0;
    let denominatorX = 0;
    let denominatorY = 0;

    for (let index = 0; index < x.length; index++) {
        const dx = x[index] - meanX;
        const dy = y[index] - meanY;

        numerator += dx * dy;
        denominatorX += dx ** 2;
        denominatorY += dy ** 2;
    }

    if (denominatorX === 0 || denominatorY === 0) {
        throw new Error("Correlation is undefined for constant data.");
    }

    return numerator / Math.sqrt(denominatorX * denominatorY);
}


// -----------------------------------------------------------------------------
// 2. Fundamental concepts
// -----------------------------------------------------------------------------

function explainFundamentals() {
    printSection("1. Fundamental concepts");

    const concepts = {
        Population:
            "The complete group about which a study intends to make claims.",
        Sample:
            "The observations actually collected from the population.",
        Parameter:
            "A numerical property of the target population.",
        Statistic:
            "A numerical quantity calculated from a sample.",
        SamplingError:
            "Random difference between a statistic and the population parameter.",
        SelectionBias:
            "Systematic distortion caused by the mechanism that determines who enters the sample.",
        SurvivorshipBias:
            "Selection bias created by analyzing only entities that remain visible.",
        NonresponseBias:
            "Distortion caused when respondents differ systematically from nonrespondents.",
        Undercoverage:
            "Failure of the sampling frame to represent some population members.",
    };

    for (const [name, description] of Object.entries(concepts)) {
        console.log(`${name}: ${description}`);
    }

    console.log(
        "\nA larger sample can reduce random sampling error without correcting "
        + "systematic selection bias."
    );
}


// -----------------------------------------------------------------------------
// 3. Synthetic population
// -----------------------------------------------------------------------------

function createPopulation(size = 10000, seed = 42) {
    const random = createRandom(seed);
    const population = [];

    for (let index = 0; index < size; index++) {
        const value = random() < 0.8
            ? normal(random, 50, 10)
            : normal(random, 80, 8);

        population.push(value);
    }

    return population;
}

function demonstrateSamplingError(population) {
    printSection("2. Sampling error");

    const populationMean = mean(population);
    console.log(`Population mean: ${populationMean.toFixed(3)}`);

    for (const sampleSize of [10, 50, 200, 1000]) {
        const errors = [];

        for (let repetition = 0; repetition < 100; repetition++) {
            const random = createRandom(repetition + sampleSize);
            const sample = sampleWithoutReplacement(
                population,
                sampleSize,
                random
            );

            errors.push(mean(sample) - populationMean);
        }

        const absoluteError = mean(errors.map(error => Math.abs(error)));

        console.log(
            `n=${String(sampleSize).padStart(4)} | ` +
            `mean absolute error=${absoluteError.toFixed(3)} | ` +
            `error SD=${standardDeviation(errors).toFixed(3)}`
        );
    }
}


// -----------------------------------------------------------------------------
// 4. Selection bias and undercoverage
// -----------------------------------------------------------------------------

function createPeople(size = 20000, seed = 7) {
    const random = createRandom(seed);
    const people = [];

    for (let index = 0; index < size; index++) {
        const age = Math.floor(
            18 + random() * 62
        );

        const employmentProbability =
            age >= 25 && age <= 60
                ? 0.85
                : age < 25
                    ? 0.55
                    : 0.45;

        const employed = random() < employmentProbability;

        const internetProbability =
            Math.max(0.25, Math.min(0.98, 1.05 - age / 120));

        const internetAccess =
            random() < internetProbability;

        let income;

        if (age < 25) {
            income = Math.max(0, normal(random, 18000, 5000));
        } else if (age <= 60) {
            income = Math.max(0, normal(random, 55000, 18000));
        } else {
            income = Math.max(0, normal(random, 42000, 15000));
        }

        people.push({
            age,
            employed,
            internetAccess,
            income
        });
    }

    return people;
}

function demonstrateSelectionBias(people) {
    printSection("3. Selection bias");

    const populationMean = mean(
        people.map(person => person.income)
    );

    const onlineOnly = people.filter(
        person => person.internetAccess
    );

    const employedOnly = people.filter(
        person => person.employed
    );

    console.log(
        `Population income mean:      ${populationMean.toFixed(2)}`
    );

    console.log(
        `Internet-only mean:          ${
            mean(onlineOnly.map(person => person.income)).toFixed(2)
        }`
    );

    console.log(
        `Employed-only mean:          ${
            mean(employedOnly.map(person => person.income)).toFixed(2)
        }`
    );

    console.log(
        "\nThe sample-selection mechanism changes who is observed. "
        + "The difference from the population mean is not automatically "
        + "sampling error."
    );
}

function demonstrateUndercoverage(people) {
    printSection("4. Undercoverage and convenience sampling");

    const frame = people.filter(
        person => person.internetAccess
    );

    console.log(`Population:       ${people.length}`);
    console.log(`Frame:             ${frame.length}`);
    console.log(
        `Coverage rate:     ${(frame.length / people.length * 100).toFixed(2)}%`
    );

    const highIncomeConvenienceSample = [...frame]
        .sort((a, b) => b.income - a.income)
        .slice(0, 100);

    console.log(
        `Convenience subset mean: ${
            mean(highIncomeConvenienceSample.map(p => p.income)).toFixed(2)
        }`
    );
}


// -----------------------------------------------------------------------------
// 5. Nonresponse bias
// -----------------------------------------------------------------------------

function simulateSurvey(people, responseProbability, seed = 123) {
    const random = createRandom(seed);
    const respondents = [];
    const nonrespondents = [];

    for (const person of people) {
        const probability = Math.max(
            0,
            Math.min(1, responseProbability(person))
        );

        if (random() < probability) {
            respondents.push(person);
        } else {
            nonrespondents.push(person);
        }
    }

    return {
        respondents,
        nonrespondents
    };
}

function demonstrateNonresponseBias(people) {
    printSection("5. Nonresponse bias");

    const result = simulateSurvey(
        people,
        person => {
            const normalizedIncome =
                Math.min(person.income / 100000, 1);

            return 0.20 + 0.45 * normalizedIncome;
        }
    );

    const populationMean = mean(
        people.map(person => person.income)
    );

    const respondentMean = mean(
        result.respondents.map(person => person.income)
    );

    console.log(`Response rate: ${
        (result.respondents.length / people.length * 100).toFixed(2)
    }%`);

    console.log(`Population mean: ${
        populationMean.toFixed(2)
    }`);

    console.log(`Respondent mean: ${
        respondentMean.toFixed(2)
    }`);

    console.log(`Observed bias: ${
        (respondentMean - populationMean).toFixed(2)
    }`);
}


// -----------------------------------------------------------------------------
// 6. Survivorship bias
// -----------------------------------------------------------------------------

function createCompanies(size = 10000, seed = 99) {
    const random = createRandom(seed);
    const companies = [];

    for (let index = 0; index < size; index++) {
        const performance = normal(random, 5, 20);

        let survivalProbability =
            0.35 + 0.015 * Math.max(
                -10,
                Math.min(30, performance)
            );

        survivalProbability =
            Math.max(0.05, Math.min(0.90, survivalProbability));

        companies.push({
            performance,
            survived: random() < survivalProbability
        });
    }

    return companies;
}

function demonstrateSurvivorshipBias(companies) {
    printSection("6. Survivorship bias");

    const allMean = mean(
        companies.map(company => company.performance)
    );

    const survivors = companies.filter(company => company.survived);
    const failures = companies.filter(company => !company.survived);

    console.log(`All companies mean: ${
        allMean.toFixed(3)
    }`);

    console.log(`Survivors: ${survivors.length}`);
    console.log(`Failures:  ${failures.length}`);

    console.log(`Survivors' mean: ${
        mean(survivors.map(company => company.performance)).toFixed(3)
    }`);

    console.log(`Failures' mean: ${
        mean(failures.map(company => company.performance)).toFixed(3)
    }`);

    console.log(
        "\nRemoving failures before analysis can make the observed survivor "
        + "population appear more successful than the original population."
    );
}


// -----------------------------------------------------------------------------
// 7. Collider bias
// -----------------------------------------------------------------------------

function createPatients(size = 15000, seed = 15) {
    const random = createRandom(seed);
    const patients = [];

    for (let index = 0; index < size; index++) {
        const severity = normal(random, 0, 1);
        const treatmentEffect = normal(random, 0, 1);

        const hospitalizationScore =
            1.5 * severity -
            1.1 * treatmentEffect +
            normal(random, 0, 1);

        patients.push({
            severity,
            treatmentEffect,
            hospitalized: hospitalizationScore > 0.5
        });
    }

    return patients;
}

function demonstrateColliderBias(patients) {
    printSection("7. Collider bias");

    const hospitalized = patients.filter(
        patient => patient.hospitalized
    );

    console.log(
        "Correlation in all patients:",
        pearsonCorrelation(
            patients.map(p => p.severity),
            patients.map(p => p.treatmentEffect)
        ).toFixed(3)
    );

    console.log(
        "Correlation among hospitalized patients:",
        pearsonCorrelation(
            hospitalized.map(p => p.severity),
            hospitalized.map(p => p.treatmentEffect)
        ).toFixed(3)
    );

    console.log(
        "\nConditioning on a variable affected by two other variables can "
        + "induce an association between those variables."
    );
}


// -----------------------------------------------------------------------------
// 8. Stratified sampling
// -----------------------------------------------------------------------------

function stratifiedSample(people, strata, sampleSizes, seed = 42) {
    if (strata.length !== sampleSizes.length) {
        throw new Error("Every stratum needs a sample size.");
    }

    const random = createRandom(seed);
    const selected = [];
    const assigned = new Set();

    for (let stratumIndex = 0; stratumIndex < strata.length; stratumIndex++) {
        const members = [];

        for (let index = 0; index < people.length; index++) {
            if (!assigned.has(index) && strata[stratumIndex](people[index])) {
                members.push({
                    index,
                    person: people[index]
                });
            }
        }

        if (sampleSizes[stratumIndex] > members.length) {
            throw new Error("Requested stratum sample is too large.");
        }

        const selectedMembers = sampleWithoutReplacement(
            members,
            sampleSizes[stratumIndex],
            random
        );

        for (const item of selectedMembers) {
            selected.push(item.person);
            assigned.add(item.index);
        }
    }

    return selected;
}

function demonstrateStratification(people) {
    printSection("8. Stratified sampling");

    const sample = stratifiedSample(
        people,
        [
            person => person.age < 35,
            person => person.age >= 35 && person.age < 60,
            person => person.age >= 60
        ],
        [100, 100, 100]
    );

    console.log(`Sample size: ${sample.length}`);
    console.log(
        `Sample income mean: ${
            mean(sample.map(person => person.income)).toFixed(2)
        }`
    );

    console.log(
        "Under 35:",
        sample.filter(person => person.age < 35).length
    );

    console.log(
        "35-59:",
        sample.filter(
            person => person.age >= 35 && person.age < 60
        ).length
    );

    console.log(
        "60+:",
        sample.filter(person => person.age >= 60).length
    );
}


// -----------------------------------------------------------------------------
// 9. Inverse-probability weighting
// -----------------------------------------------------------------------------

function demonstrateWeighting(people) {
    printSection("9. Inverse-probability weighting");

    const random = createRandom(555);
    const selected = [];

    for (const person of people) {
        const probability =
            person.age >= 60
                ? 0.15
                : person.age >= 35
                    ? 0.40
                    : 0.70;

        if (random() < probability) {
            selected.push({
                person,
                probability
            });
        }
    }

    const unweightedMean = mean(
        selected.map(item => item.person.income)
    );

    let numerator = 0;
    let denominator = 0;

    for (const item of selected) {
        const weight = 1 / item.probability;

        numerator += item.person.income * weight;
        denominator += weight;
    }

    const weightedMean = numerator / denominator;

    console.log(
        `Population mean:        ${
            mean(people.map(p => p.income)).toFixed(2)
        }`
    );

    console.log(
        `Unweighted mean:        ${unweightedMean.toFixed(2)}`
    );

    console.log(
        `Weighted mean:          ${weightedMean.toFixed(2)}`
    );

    console.log(
        "\nInverse-probability weighting compensates for unequal inclusion "
        + "probabilities when those probabilities are known or estimated."
    );
}


// -----------------------------------------------------------------------------
// 10. Bootstrap
// -----------------------------------------------------------------------------

function bootstrapMean(sample, repetitions = 2000, seed = 1234) {
    if (sample.length === 0) {
        throw new Error("Bootstrap requires a non-empty sample.");
    }

    const random = createRandom(seed);
    const estimates = [];

    for (let repetition = 0; repetition < repetitions; repetition++) {
        const bootstrapSample = [];

        for (let index = 0; index < sample.length; index++) {
            const selectedIndex = Math.floor(
                random() * sample.length
            );

            bootstrapSample.push(sample[selectedIndex]);
        }

        estimates.push(mean(bootstrapSample));
    }

    estimates.sort((a, b) => a - b);

    const lower = estimates[
        Math.floor(0.025 * estimates.length)
    ];

    const upper = estimates[
        Math.floor(0.975 * estimates.length) - 1
    ];

    return {
        estimate: mean(estimates),
        lower,
        upper
    };
}

function demonstrateBootstrap(population) {
    printSection("10. Bootstrap uncertainty");

    const sample = sampleWithoutReplacement(
        population,
        100,
        createRandom(321)
    );

    const result = bootstrapMean(sample);

    console.log(`Sample mean: ${mean(sample).toFixed(3)}`);
    console.log(`Bootstrap mean: ${result.estimate.toFixed(3)}`);
    console.log(
        `Approximate 95% interval: [` +
        `${result.lower.toFixed(3)}, ${result.upper.toFixed(3)}]`
    );

    console.log(
        "\nBootstrap methods reproduce the information contained in the "
        + "observed sample. They do not repair systematic sample-selection bias."
    );
}


// -----------------------------------------------------------------------------
// 11. Sensitivity analysis
// -----------------------------------------------------------------------------

function demonstrateSensitivityAnalysis() {
    printSection("11. Sensitivity analysis");

    const observedMean = 70;
    const observedFraction = 0.80;

    for (const missingMean of [30, 40, 50, 60, 70, 80, 90]) {
        const correctedMean =
            observedFraction * observedMean +
            (1 - observedFraction) * missingMean;

        console.log(
            `Assumed missing mean ${String(missingMean).padStart(3)} ` +
            `-> combined mean ${correctedMean.toFixed(2)}`
        );
    }
}


// -----------------------------------------------------------------------------
// 12. Validation and edge cases
// -----------------------------------------------------------------------------

function validateSamplingDesign({
    populationSize,
    sampleSize,
    responseRate,
    hasSamplingFrame
}) {
    const warnings = [];

    if (populationSize <= 0) {
        warnings.push("Population must be positive.");
    }

    if (sampleSize <= 0) {
        warnings.push("Sample size must be positive.");
    }

    if (sampleSize > populationSize) {
        warnings.push("Sample size cannot exceed population size.");
    }

    if (responseRate < 0 || responseRate > 1) {
        warnings.push("Response rate must be between zero and one.");
    }

    if (!hasSamplingFrame) {
        warnings.push(
            "The sampling frame has not been established."
        );
    }

    return warnings;
}

function demonstrateEdgeCases() {
    printSection("12. Edge cases");

    try {
        mean([]);
    } catch (error) {
        console.log("Empty mean check:", error.message);
    }

    try {
        sampleWithoutReplacement([1, 2, 3], 4, createRandom(1));
    } catch (error) {
        console.log("Invalid sample-size check:", error.message);
    }

    try {
        pearsonCorrelation([1, 1, 1], [1, 2, 3]);
    } catch (error) {
        console.log("Constant-variable check:", error.message);
    }

    const warnings = validateSamplingDesign({
        populationSize: 1000,
        sampleSize: 250,
        responseRate: 0.62,
        hasSamplingFrame: false
    });

    for (const warning of warnings) {
        console.log("Design warning:", warning);
    }
}


// -----------------------------------------------------------------------------
// 13. Integrated execution
// -----------------------------------------------------------------------------

function main() {
    explainFundamentals();

    const population = createPopulation();
    demonstrateSamplingError(population);

    const people = createPeople();
    demonstrateSelectionBias(people);
    demonstrateUndercoverage(people);
    demonstrateNonresponseBias(people);

    const companies = createCompanies();
    demonstrateSurvivorshipBias(companies);

    const patients = createPatients();
    demonstrateColliderBias(patients);

    demonstrateStratification(people);
    demonstrateWeighting(people);
    demonstrateBootstrap(population);
    demonstrateSensitivityAnalysis();
    demonstrateEdgeCases();

    printSection("13. Diagnostic checklist");

    const checklist = [
        "Define the target population before collecting observations.",
        "Identify the sampling frame and its coverage limitations.",
        "Ask who can enter the sample and who cannot.",
        "Examine response and dropout mechanisms.",
        "Check whether selection depends on outcomes or exposures.",
        "Do not analyze only successful survivors when failures are relevant.",
        "Account for unequal inclusion probabilities.",
        "Distinguish random sampling error from systematic bias.",
        "Use sensitivity analysis when missing groups cannot be characterized precisely.",
        "Do not assume a large sample is representative merely because it is large."
    ];

    for (const item of checklist) {
        console.log("- " + item);
    }
}

main();
