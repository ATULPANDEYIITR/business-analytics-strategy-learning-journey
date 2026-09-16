/*
 * Sampling: Population, Samples and Sampling Techniques
 *
 * C++17 case study:
 * A municipal research department wants to estimate average monthly
 * household income across a large city without surveying every household.
 *
 * The program models:
 * - A finite population
 * - Geographic clusters
 * - Stratification by region
 * - Simple random sampling
 * - Multistage sampling
 * - Estimation
 * - Sampling error
 * - Confidence intervals
 * - Sample-size planning
 * - Validation and failure conditions
 *
 * Compile:
 *   g++ -std=c++17 -O2 sampling_case_study.cpp -o sampling_case_study
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

struct Household {
    int id;
    int age;
    std::string region;
    std::string employment;
    double monthlyIncome;
    std::string cluster;
};

using Population = std::vector<Household>;

class SamplingEngine {
private:
    std::mt19937 generator;

public:
    explicit SamplingEngine(unsigned seed = 42)
        : generator(seed) {}

    // Generate an integer from an inclusive range.
    int randomInteger(int minimum, int maximum) {
        std::uniform_int_distribution<int> distribution(
            minimum,
            maximum
        );

        return distribution(generator);
    }

    // Select k distinct elements without replacement.
    template <typename T>
    std::vector<T> randomSample(
        const std::vector<T>& source,
        std::size_t k
    ) {
        if (k > source.size()) {
            throw std::invalid_argument(
                "Sample size exceeds source size."
            );
        }

        std::vector<T> copy = source;

        std::shuffle(
            copy.begin(),
            copy.end(),
            generator
        );

        copy.resize(k);
        return copy;
    }
};

// ---------------------------------------------------------------------------
// Basic statistics
// ---------------------------------------------------------------------------

double mean(const std::vector<double>& values) {
    if (values.empty()) {
        throw std::invalid_argument(
            "Cannot calculate mean of empty data."
        );
    }

    return std::accumulate(
        values.begin(),
        values.end(),
        0.0
    ) / static_cast<double>(values.size());
}

double sampleStandardDeviation(
    const std::vector<double>& values
) {
    if (values.size() < 2) {
        return 0.0;
    }

    const double average = mean(values);

    double squaredDeviation = 0.0;

    for (double value : values) {
        squaredDeviation +=
            std::pow(value - average, 2);
    }

    return std::sqrt(
        squaredDeviation
        / static_cast<double>(values.size() - 1)
    );
}

std::vector<double> incomes(
    const std::vector<Household>& households
) {
    std::vector<double> values;
    values.reserve(households.size());

    for (const auto& household : households) {
        values.push_back(household.monthlyIncome);
    }

    return values;
}

// ---------------------------------------------------------------------------
// Synthetic city population
// ---------------------------------------------------------------------------

Population createPopulation(
    std::size_t size,
    unsigned seed
) {
    if (size == 0) {
        throw std::invalid_argument(
            "Population cannot be empty."
        );
    }

    SamplingEngine random(seed);

    const std::vector<std::string> regions = {
        "North",
        "South",
        "East",
        "West"
    };

    const std::vector<std::string> employmentTypes = {
        "Student",
        "Employed",
        "Self-employed",
        "Unemployed"
    };

    Population population;
    population.reserve(size);

    std::mt19937 normalGenerator(seed + 1);

    for (std::size_t i = 0; i < size; ++i) {
        const int age =
            random.randomInteger(18, 75);

        const std::string region =
            regions[i % regions.size()];

        const std::string employment =
            employmentTypes[
                random.randomInteger(
                    0,
                    static_cast<int>(employmentTypes.size()) - 1
                )
            ];

        double baseIncome = 0.0;

        if (employment == "Student") {
            baseIncome = 12000.0;
        } else if (employment == "Employed") {
            baseIncome = 50000.0;
        } else if (employment == "Self-employed") {
            baseIncome = 65000.0;
        } else {
            baseIncome = 10000.0;
        }

        std::normal_distribution<double> incomeDistribution(
            baseIncome,
            baseIncome * 0.25
        );

        double income =
            std::max(
                0.0,
                incomeDistribution(normalGenerator)
            );

        const int clusterNumber =
            static_cast<int>(i % 20) + 1;

        population.push_back(
            Household{
                static_cast<int>(i + 1),
                age,
                region,
                employment,
                income,
                "Ward-" +
                    std::to_string(clusterNumber)
            }
        );
    }

    return population;
}

// ---------------------------------------------------------------------------
// Simple random sampling
// ---------------------------------------------------------------------------

Population simpleRandomSample(
    const Population& population,
    std::size_t sampleSize,
    unsigned seed
) {
    if (sampleSize == 0 ||
        sampleSize > population.size()) {
        throw std::invalid_argument(
            "Invalid simple random sample size."
        );
    }

    SamplingEngine engine(seed);

    return engine.randomSample(
        population,
        sampleSize
    );
}

// ---------------------------------------------------------------------------
// Stratified random sampling
// ---------------------------------------------------------------------------

Population stratifiedSample(
    const Population& population,
    std::size_t sampleSize,
    unsigned seed
) {
    if (sampleSize == 0 ||
        sampleSize > population.size()) {
        throw std::invalid_argument(
            "Invalid stratified sample size."
        );
    }

    std::map<std::string, Population> strata;

    for (const auto& household : population) {
        strata[household.region].push_back(
            household
        );
    }

    SamplingEngine engine(seed);

    Population result;

    /*
     * Proportionate allocation:
     *
     * n_h = (N_h / N) * n
     *
     * The remaining observations after integer rounding are assigned
     * to the largest strata that still have capacity.
     */
    std::map<std::string, std::size_t> allocation;

    std::size_t allocated = 0;

    for (const auto& [region, units] : strata) {
        const double exactAllocation =
            static_cast<double>(units.size())
            / static_cast<double>(population.size())
            * static_cast<double>(sampleSize);

        const std::size_t count =
            static_cast<std::size_t>(
                std::floor(exactAllocation)
            );

        allocation[region] = count;
        allocated += count;
    }

    while (allocated < sampleSize) {
        auto candidate = std::max_element(
            allocation.begin(),
            allocation.end(),
            [&](const auto& left, const auto& right) {
                const double leftRate =
                    static_cast<double>(
                        strata.at(left.first).size()
                    ) / population.size();

                const double rightRate =
                    static_cast<double>(
                        strata.at(right.first).size()
                    ) / population.size();

                return leftRate < rightRate;
            }
        );

        if (candidate == allocation.end()) {
            break;
        }

        if (candidate->second <
            strata.at(candidate->first).size()) {
            ++candidate->second;
            ++allocated;
        } else {
            break;
        }
    }

    for (const auto& [region, units] : strata) {
        const std::size_t count =
            allocation[region];

        const Population selected =
            engine.randomSample(units, count);

        result.insert(
            result.end(),
            selected.begin(),
            selected.end()
        );
    }

    std::shuffle(
        result.begin(),
        result.end(),
        std::mt19937(seed + 100)
    );

    return result;
}

// ---------------------------------------------------------------------------
// Two-stage cluster sampling
// ---------------------------------------------------------------------------

Population multistageSample(
    const Population& population,
    std::size_t numberOfClusters,
    std::size_t householdsPerCluster,
    unsigned seed
) {
    if (numberOfClusters == 0 ||
        householdsPerCluster == 0) {
        throw std::invalid_argument(
            "Stage sizes must be positive."
        );
    }

    std::map<std::string, Population> clusters;

    for (const auto& household : population) {
        clusters[household.cluster].push_back(
            household
        );
    }

    if (numberOfClusters > clusters.size()) {
        throw std::invalid_argument(
            "Requested more clusters than exist."
        );
    }

    SamplingEngine engine(seed);

    std::vector<std::string> clusterNames;

    for (const auto& [name, units] : clusters) {
        clusterNames.push_back(name);
    }

    clusterNames =
        engine.randomSample(
            clusterNames,
            numberOfClusters
        );

    Population result;

    for (const auto& clusterName : clusterNames) {
        const auto& units =
            clusters.at(clusterName);

        const std::size_t count =
            std::min(
                householdsPerCluster,
                units.size()
            );

        const Population selected =
            engine.randomSample(units, count);

        result.insert(
            result.end(),
            selected.begin(),
            selected.end()
        );
    }

    return result;
}

// ---------------------------------------------------------------------------
// Estimation
// ---------------------------------------------------------------------------

double estimateMeanIncome(
    const Population& sample
) {
    return mean(incomes(sample));
}

double samplingError(
    double populationMean,
    double estimate
) {
    return estimate - populationMean;
}

double standardErrorOfMean(
    const Population& sample
) {
    const std::vector<double> values =
        incomes(sample);

    return sampleStandardDeviation(values)
        / std::sqrt(
            static_cast<double>(values.size())
        );
}

struct ConfidenceInterval {
    double estimate;
    double standardError;
    double lower;
    double upper;
};

ConfidenceInterval confidenceInterval(
    const Population& sample,
    double zValue = 1.96
) {
    if (sample.size() < 2) {
        throw std::invalid_argument(
            "At least two observations are required."
        );
    }

    const double estimate =
        estimateMeanIncome(sample);

    const double standardError =
        standardErrorOfMean(sample);

    const double margin =
        zValue * standardError;

    return {
        estimate,
        standardError,
        estimate - margin,
        estimate + margin
    };
}

// ---------------------------------------------------------------------------
// Cochran sample-size calculation
// ---------------------------------------------------------------------------

std::size_t cochranSampleSize(
    double z,
    double proportion,
    double marginOfError,
    std::size_t populationSize
) {
    if (z <= 0 ||
        proportion <= 0 ||
        proportion >= 1 ||
        marginOfError <= 0 ||
        marginOfError >= 1 ||
        populationSize == 0) {
        throw std::invalid_argument(
            "Invalid sample-size parameters."
        );
    }

    const double n0 =
        (z * z * proportion * (1.0 - proportion))
        / (marginOfError * marginOfError);

    const double corrected =
        n0
        / (
            1.0
            + (n0 - 1.0)
            / static_cast<double>(populationSize)
        );

    return std::min(
        populationSize,
        static_cast<std::size_t>(
            std::ceil(corrected)
        )
    );
}

// ---------------------------------------------------------------------------
// Repeated-sampling experiment
// ---------------------------------------------------------------------------

std::vector<double> repeatedSampling(
    const Population& population,
    std::size_t sampleSize,
    std::size_t repetitions
) {
    if (repetitions == 0) {
        throw std::invalid_argument(
            "Repetitions must be positive."
        );
    }

    std::vector<double> estimates;
    estimates.reserve(repetitions);

    for (std::size_t i = 0; i < repetitions; ++i) {
        const Population sample =
            simpleRandomSample(
                population,
                sampleSize,
                static_cast<unsigned>(1000 + i)
            );

        estimates.push_back(
            estimateMeanIncome(sample)
        );
    }

    return estimates;
}

// ---------------------------------------------------------------------------
// Utility display
// ---------------------------------------------------------------------------

void printResult(
    const std::string& name,
    double populationMean,
    const Population& sample
) {
    const double estimate =
        estimateMeanIncome(sample);

    std::cout
        << std::left
        << std::setw(28)
        << name
        << "n = "
        << std::setw(5)
        << sample.size()
        << " estimate = "
        << std::fixed
        << std::setprecision(2)
        << estimate
        << " error = "
        << samplingError(
            populationMean,
            estimate
        )
        << '\n';
}

// ---------------------------------------------------------------------------
// Main industry-style case study
// ---------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << "SAMPLING CASE STUDY\n"
            << "Municipal household income survey\n"
            << "========================================\n\n";

        // The full population is available to the simulation but would
        // represent a costly census in the real-world scenario.
        const Population population =
            createPopulation(10000, 42);

        const double truePopulationMean =
            mean(incomes(population));

        std::cout
            << "Population size: "
            << population.size()
            << '\n'
            << "True population mean income: "
            << std::fixed
            << std::setprecision(2)
            << truePopulationMean
            << "\n\n";

        // Strategy 1: simple random sample.
        const Population randomSample =
            simpleRandomSample(
                population,
                400,
                10
            );

        printResult(
            "Simple random sampling",
            truePopulationMean,
            randomSample
        );

        // Strategy 2: stratified sample.
        const Population stratified =
            stratifiedSample(
                population,
                400,
                20
            );

        printResult(
            "Stratified sampling",
            truePopulationMean,
            stratified
        );

        // Strategy 3: two-stage cluster sample.
        const Population multistage =
            multistageSample(
                population,
                8,
                50,
                30
            );

        printResult(
            "Two-stage cluster sampling",
            truePopulationMean,
            multistage
        );

        // Confidence interval for the stratified sample.
        const ConfidenceInterval interval =
            confidenceInterval(stratified);

        std::cout
            << "\nAPPROXIMATE 95% CONFIDENCE INTERVAL\n"
            << "Estimate: "
            << interval.estimate
            << '\n'
            << "Standard error: "
            << interval.standardError
            << '\n'
            << "Lower bound: "
            << interval.lower
            << '\n'
            << "Upper bound: "
            << interval.upper
            << "\n\n";

        // Sample-size planning.
        const std::size_t plannedSampleSize =
            cochranSampleSize(
                1.96,
                0.50,
                0.05,
                population.size()
            );

        std::cout
            << "PLANNED SAMPLE SIZE\n"
            << "For 95% confidence, p=0.50, "
               "and 5% margin of error: "
            << plannedSampleSize
            << "\n\n";

        // Repeated sampling shows the sampling distribution of the mean.
        const auto estimates =
            repeatedSampling(
                population,
                100,
                300
            );

        const double averageEstimate =
            mean(estimates);

        const double distributionSD =
            sampleStandardDeviation(estimates);

        std::cout
            << "SAMPLING DISTRIBUTION EXPERIMENT\n"
            << "Repeated samples: "
            << estimates.size()
            << '\n'
            << "Mean of sample means: "
            << averageEstimate
            << '\n'
            << "SD of sample means: "
            << distributionSD
            << '\n';

        /*
         * Edge-case validation:
         *
         * A production sampling system must reject invalid designs instead
         * of silently producing misleading results.
         */
        std::cout
            << "\nVALIDATION TEST\n";

        try {
            simpleRandomSample(
                population,
                population.size() + 1,
                99
            );
        } catch (const std::exception& error) {
            std::cout
                << "Invalid sample correctly rejected: "
                << error.what()
                << '\n';
        }

        /*
         * Design trade-off:
         *
         * Simple random sampling is conceptually clean but may be expensive
         * when sampled units are geographically dispersed.
         *
         * Stratification can improve representation and precision when
         * strata are appropriately defined.
         *
         * Cluster sampling can reduce travel and operational cost, but
         * observations inside clusters may be correlated. That correlation
         * can increase variance relative to a simple random sample of the
         * same nominal size.
         *
         * Multistage sampling combines operational efficiency with
         * probability-based selection, but its variance calculation requires
         * accounting for the complete design rather than treating the final
         * observations as a simple random sample.
         */

        std::cout
            << "\nDESIGN INTERPRETATION\n"
            << "Population -> sampling frame -> clusters/strata -> "
               "selected units -> measurements -> estimator\n";

        std::cout
            << "\nCASE STUDY COMPLETE\n";
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
