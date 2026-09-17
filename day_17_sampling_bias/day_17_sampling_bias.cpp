/*
Sampling Bias Case Study
========================

Scenario:
A national analytics organization wants to estimate the average annual
income of adults and study employment patterns.

The program intentionally models a realistic data pipeline in which:
1. A target population exists.
2. A sampling frame covers only part of that population.
3. An online survey introduces undercoverage.
4. Nonresponse depends on income.
5. Some observations are selected with unequal probabilities.
6. Analysts compare weighted and unweighted estimates.
7. Survivorship bias is demonstrated with companies.
8. Collider bias is demonstrated with hospital admission.
9. Bootstrap uncertainty is calculated.
10. Sensitivity analysis examines the consequences of missing groups.

Compile:
    g++ -std=c++17 -O2 sampling_bias.cpp -o sampling_bias

The implementation uses only the C++ standard library.
*/

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;


// -----------------------------------------------------------------------------
// Utility functions
// -----------------------------------------------------------------------------

void printSection(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}

double mean(const vector<double>& values) {
    if (values.empty()) {
        throw invalid_argument("Mean requires a non-empty vector.");
    }

    const double total =
        accumulate(values.begin(), values.end(), 0.0);

    return total / static_cast<double>(values.size());
}

double sampleVariance(const vector<double>& values) {
    if (values.size() < 2) {
        throw invalid_argument(
            "Variance requires at least two observations."
        );
    }

    const double average = mean(values);

    double total = 0.0;

    for (double value : values) {
        total += (value - average) * (value - average);
    }

    return total / static_cast<double>(values.size() - 1);
}

double standardDeviation(const vector<double>& values) {
    return sqrt(sampleVariance(values));
}

double correlation(
    const vector<double>& x,
    const vector<double>& y
) {
    if (x.size() != y.size() || x.size() < 2) {
        throw invalid_argument(
            "Correlation requires equally sized non-trivial vectors."
        );
    }

    const double meanX = mean(x);
    const double meanY = mean(y);

    double numerator = 0.0;
    double denominatorX = 0.0;
    double denominatorY = 0.0;

    for (size_t i = 0; i < x.size(); ++i) {
        const double dx = x[i] - meanX;
        const double dy = y[i] - meanY;

        numerator += dx * dy;
        denominatorX += dx * dx;
        denominatorY += dy * dy;
    }

    if (denominatorX == 0.0 || denominatorY == 0.0) {
        throw invalid_argument(
            "Correlation is undefined for a constant variable."
        );
    }

    return numerator /
           sqrt(denominatorX * denominatorY);
}


// -----------------------------------------------------------------------------
// Domain model
// -----------------------------------------------------------------------------

struct Person {
    int age{};
    double income{};
    bool employed{};
    bool internetAccess{};
};

struct Company {
    double startingPerformance{};
    bool survived{};
};

struct Patient {
    double severity{};
    double treatmentEffect{};
    bool hospitalized{};
};

struct SelectedPerson {
    Person person;
    double inclusionProbability{};
};


// -----------------------------------------------------------------------------
// Population generation
// -----------------------------------------------------------------------------

class PopulationGenerator {
public:
    explicit PopulationGenerator(unsigned seed)
        : generator(seed),
          normalDistribution(0.0, 1.0),
          uniformDistribution(0.0, 1.0) {}

    vector<Person> generatePeople(size_t size) {
        vector<Person> people;
        people.reserve(size);

        for (size_t i = 0; i < size; ++i) {
            // The age distribution is intentionally broad.
            const int age =
                18 + static_cast<int>(
                    uniformDistribution(generator) * 62
                );

            double employmentProbability;

            if (age >= 25 && age <= 60) {
                employmentProbability = 0.85;
            } else if (age < 25) {
                employmentProbability = 0.55;
            } else {
                employmentProbability = 0.45;
            }

            const bool employed =
                uniformDistribution(generator) <
                employmentProbability;

            const double internetProbability =
                max(
                    0.25,
                    min(
                        0.98,
                        1.05 - static_cast<double>(age) / 120.0
                    )
                );

            const bool internetAccess =
                uniformDistribution(generator) <
                internetProbability;

            double incomeMean;

            if (age < 25) {
                incomeMean = 18000.0;
            } else if (age <= 60) {
                incomeMean = 55000.0;
            } else {
                incomeMean = 42000.0;
            }

            double incomeSD;

            if (age < 25) {
                incomeSD = 5000.0;
            } else if (age <= 60) {
                incomeSD = 18000.0;
            } else {
                incomeSD = 15000.0;
            }

            double income =
                incomeMean +
                incomeSD * normalDistribution(generator);

            income = max(0.0, income);

            people.push_back({
                age,
                income,
                employed,
                internetAccess
            });
        }

        return people;
    }

private:
    mt19937 generator;
    normal_distribution<double> normalDistribution;
    uniform_real_distribution<double> uniformDistribution;
};


// -----------------------------------------------------------------------------
// Sampling service
// -----------------------------------------------------------------------------

class SamplingService {
public:
    explicit SamplingService(unsigned seed)
        : generator(seed) {}

    vector<Person> simpleRandomSample(
        const vector<Person>& population,
        size_t sampleSize
    ) {
        if (sampleSize == 0 || sampleSize > population.size()) {
            throw invalid_argument(
                "Simple random sample size is invalid."
            );
        }

        vector<Person> sample = population;

        shuffle(
            sample.begin(),
            sample.end(),
            generator
        );

        sample.resize(sampleSize);

        return sample;
    }

    vector<Person> stratifiedSample(
        const vector<Person>& population,
        size_t youngSize,
        size_t middleSize,
        size_t olderSize
    ) {
        vector<Person> young;
        vector<Person> middle;
        vector<Person> older;

        for (const Person& person : population) {
            if (person.age < 35) {
                young.push_back(person);
            } else if (person.age < 60) {
                middle.push_back(person);
            } else {
                older.push_back(person);
            }
        }

        auto selectFromStratum =
            [this](vector<Person> stratum, size_t requested) {
                if (requested > stratum.size()) {
                    throw invalid_argument(
                        "Requested stratum sample exceeds stratum size."
                    );
                }

                shuffle(
                    stratum.begin(),
                    stratum.end(),
                    generator
                );

                stratum.resize(requested);
                return stratum;
            };

        vector<Person> result;

        vector<Person> selectedYoung =
            selectFromStratum(young, youngSize);

        vector<Person> selectedMiddle =
            selectFromStratum(middle, middleSize);

        vector<Person> selectedOlder =
            selectFromStratum(older, olderSize);

        result.insert(
            result.end(),
            selectedYoung.begin(),
            selectedYoung.end()
        );

        result.insert(
            result.end(),
            selectedMiddle.begin(),
            selectedMiddle.end()
        );

        result.insert(
            result.end(),
            selectedOlder.begin(),
            selectedOlder.end()
        );

        return result;
    }

private:
    mt19937 generator;
};


// -----------------------------------------------------------------------------
// Selection bias analysis
// -----------------------------------------------------------------------------

class SelectionAnalyzer {
public:
    static double incomeMean(
        const vector<Person>& people
    ) {
        vector<double> incomes;
        incomes.reserve(people.size());

        for (const Person& person : people) {
            incomes.push_back(person.income);
        }

        return mean(incomes);
    }

    static vector<Person> internetOnly(
        const vector<Person>& people
    ) {
        vector<Person> result;

        for (const Person& person : people) {
            if (person.internetAccess) {
                result.push_back(person);
            }
        }

        return result;
    }

    static vector<Person> employedOnly(
        const vector<Person>& people
    ) {
        vector<Person> result;

        for (const Person& person : people) {
            if (person.employed) {
                result.push_back(person);
            }
        }

        return result;
    }

    static void reportSelectionBias(
        const vector<Person>& population
    ) {
        printSection(
            "Selection bias and undercoverage"
        );

        const vector<Person> online =
            internetOnly(population);

        const vector<Person> employed =
            employedOnly(population);

        const double populationMean =
            incomeMean(population);

        const double onlineMean =
            incomeMean(online);

        const double employedMean =
            incomeMean(employed);

        cout << fixed << setprecision(2);

        cout << "Population size: "
             << population.size() << "\n";

        cout << "Internet-access frame: "
             << online.size() << "\n";

        cout << "Coverage rate: "
             << 100.0 *
                    static_cast<double>(online.size()) /
                    static_cast<double>(population.size())
             << "%\n";

        cout << "Population income mean: "
             << populationMean << "\n";

        cout << "Internet-only mean: "
             << onlineMean << "\n";

        cout << "Employed-only mean: "
             << employedMean << "\n";

        cout << "\nThe estimates differ because the selection rules "
             << "change the composition of the observed population.\n";
    }

    static double weightedMean(
        const vector<SelectedPerson>& selected
    ) {
        if (selected.empty()) {
            throw invalid_argument(
                "Weighted mean requires observations."
            );
        }

        double weightedTotal = 0.0;
        double totalWeight = 0.0;

        for (const SelectedPerson& observation : selected) {
            if (observation.inclusionProbability <= 0.0) {
                throw invalid_argument(
                    "Inclusion probability must be positive."
                );
            }

            const double weight =
                1.0 / observation.inclusionProbability;

            weightedTotal +=
                observation.person.income * weight;

            totalWeight += weight;
        }

        return weightedTotal / totalWeight;
    }
};


// -----------------------------------------------------------------------------
// Nonresponse simulation
// -----------------------------------------------------------------------------

class SurveySimulator {
public:
    explicit SurveySimulator(unsigned seed)
        : generator(seed),
          uniformDistribution(0.0, 1.0) {}

    pair<vector<Person>, vector<Person>> conductSurvey(
        const vector<Person>& population
    ) {
        vector<Person> respondents;
        vector<Person> nonrespondents;

        for (const Person& person : population) {
            const double normalizedIncome =
                min(person.income / 100000.0, 1.0);

            // Response probability intentionally depends on income.
            const double responseProbability =
                0.20 + 0.45 * normalizedIncome;

            if (uniformDistribution(generator) <
                responseProbability) {
                respondents.push_back(person);
            } else {
                nonrespondents.push_back(person);
            }
        }

        return {respondents, nonrespondents};
    }

private:
    mt19937 generator;
    uniform_real_distribution<double> uniformDistribution;
};


// -----------------------------------------------------------------------------
// Survivorship bias
// -----------------------------------------------------------------------------

class SurvivorshipStudy {
public:
    explicit SurvivorshipStudy(unsigned seed)
        : generator(seed),
          normalDistribution(0.0, 1.0),
          uniformDistribution(0.0, 1.0) {}

    vector<Company> generateCompanies(size_t size) {
        vector<Company> companies;
        companies.reserve(size);

        for (size_t i = 0; i < size; ++i) {
            const double performance =
                5.0 +
                20.0 * normalDistribution(generator);

            double survivalProbability =
                0.35 +
                0.015 *
                    max(
                        -10.0,
                        min(30.0, performance)
                    );

            survivalProbability =
                max(
                    0.05,
                    min(0.90, survivalProbability)
                );

            const bool survived =
                uniformDistribution(generator) <
                survivalProbability;

            companies.push_back({
                performance,
                survived
            });
        }

        return companies;
    }

    void report(
        const vector<Company>& companies
    ) const {
        printSection("Survivorship bias");

        vector<double> all;
        vector<double> survivors;
        vector<double> failures;

        for (const Company& company : companies) {
            all.push_back(company.startingPerformance);

            if (company.survived) {
                survivors.push_back(
                    company.startingPerformance
                );
            } else {
                failures.push_back(
                    company.startingPerformance
                );
            }
        }

        cout << fixed << setprecision(3);

        cout << "All companies mean: "
             << mean(all) << "\n";

        cout << "Survivors: "
             << survivors.size() << "\n";

        cout << "Failures: "
             << failures.size() << "\n";

        cout << "Survivors' mean: "
             << mean(survivors) << "\n";

        cout << "Failures' mean: "
             << mean(failures) << "\n";

        cout << "\nThe survivor-only dataset excludes failed entities "
             << "before the final analysis.\n";
    }

private:
    mt19937 generator;
    normal_distribution<double> normalDistribution;
    uniform_real_distribution<double> uniformDistribution;
};


// -----------------------------------------------------------------------------
// Collider-bias study
// -----------------------------------------------------------------------------

class ColliderStudy {
public:
    explicit ColliderStudy(unsigned seed)
        : generator(seed),
          normalDistribution(0.0, 1.0) {}

    vector<Patient> generatePatients(size_t size) {
        vector<Patient> patients;
        patients.reserve(size);

        for (size_t i = 0; i < size; ++i) {
            const double severity =
                normalDistribution(generator);

            const double treatmentEffect =
                normalDistribution(generator);

            const double hospitalizationScore =
                1.5 * severity -
                1.1 * treatmentEffect +
                normalDistribution(generator);

            patients.push_back({
                severity,
                treatmentEffect,
                hospitalizationScore > 0.5
            });
        }

        return patients;
    }

    void report(
        const vector<Patient>& patients
    ) const {
        printSection("Collider bias");

        vector<double> severityAll;
        vector<double> effectAll;

        vector<double> severityHospitalized;
        vector<double> effectHospitalized;

        for (const Patient& patient : patients) {
            severityAll.push_back(patient.severity);
            effectAll.push_back(patient.treatmentEffect);

            if (patient.hospitalized) {
                severityHospitalized.push_back(
                    patient.severity
                );

                effectHospitalized.push_back(
                    patient.treatmentEffect
                );
            }
        }

        cout << fixed << setprecision(3);

        cout << "Correlation in all patients: "
             << correlation(
                    severityAll,
                    effectAll
                )
             << "\n";

        cout << "Correlation among hospitalized: "
             << correlation(
                    severityHospitalized,
                    effectHospitalized
                )
             << "\n";

        cout << "\nHospitalization is affected by both variables. "
             << "Restricting the analysis to hospitalized patients "
             << "conditions on a common effect and can create an "
             << "association between its causes.\n";
    }

private:
    mt19937 generator;
    normal_distribution<double> normalDistribution;
};


// -----------------------------------------------------------------------------
// Bootstrap estimation
// -----------------------------------------------------------------------------

class BootstrapEstimator {
public:
    explicit BootstrapEstimator(unsigned seed)
        : generator(seed) {}

    struct Result {
        double meanEstimate;
        double lower;
        double upper;
    };

    Result estimateMean(
        const vector<double>& sample,
        size_t repetitions = 2000
    ) {
        if (sample.empty()) {
            throw invalid_argument(
                "Bootstrap requires a non-empty sample."
            );
        }

        vector<double> estimates;
        estimates.reserve(repetitions);

        uniform_int_distribution<size_t> indexDistribution(
            0,
            sample.size() - 1
        );

        for (size_t repetition = 0;
             repetition < repetitions;
             ++repetition) {

            vector<double> resample;
            resample.reserve(sample.size());

            for (size_t i = 0; i < sample.size(); ++i) {
                resample.push_back(
                    sample[indexDistribution(generator)]
                );
            }

            estimates.push_back(mean(resample));
        }

        sort(
            estimates.begin(),
            estimates.end()
        );

        const size_t lowerIndex =
            static_cast<size_t>(
                0.025 * estimates.size()
            );

        const size_t upperIndex =
            static_cast<size_t>(
                0.975 * estimates.size()
            ) - 1;

        return {
            mean(estimates),
            estimates.at(lowerIndex),
            estimates.at(upperIndex)
        };
    }

private:
    mt19937 generator;
};


// -----------------------------------------------------------------------------
// Sensitivity analysis
// -----------------------------------------------------------------------------

void sensitivityAnalysis(
    double observedMean,
    double observedFraction
) {
    printSection("Sensitivity analysis");

    const vector<double> assumedMissingMeans = {
        30, 40, 50, 60, 70, 80, 90
    };

    cout << fixed << setprecision(2);

    for (double missingMean : assumedMissingMeans) {
        const double combinedMean =
            observedFraction * observedMean +
            (1.0 - observedFraction) * missingMean;

        cout << "Missing-group assumption "
             << setw(6) << missingMean
             << " -> combined estimate "
             << combinedMean << "\n";
    }
}


// -----------------------------------------------------------------------------
// Design diagnostics
// -----------------------------------------------------------------------------

class SamplingDiagnostics {
public:
    static vector<string> validate(
        size_t populationSize,
        size_t sampleSize,
        double responseRate,
        bool hasSamplingFrame
    ) {
        vector<string> warnings;

        if (populationSize == 0) {
            warnings.push_back(
                "Population size must be positive."
            );
        }

        if (sampleSize == 0) {
            warnings.push_back(
                "Sample size must be positive."
            );
        }

        if (sampleSize > populationSize) {
            warnings.push_back(
                "Sample size cannot exceed population size."
            );
        }

        if (responseRate < 0.0 ||
            responseRate > 1.0) {
            warnings.push_back(
                "Response rate must be between zero and one."
            );
        }

        if (!hasSamplingFrame) {
            warnings.push_back(
                "Sampling frame has not been established."
            );
        }

        return warnings;
    }

    static void printChecklist() {
        printSection("Sampling-design checklist");

        const vector<string> questions = {
            "What is the exact target population?",
            "What is the sampling frame?",
            "Who is excluded from the frame?",
            "Who has a lower probability of selection?",
            "Who does not respond?",
            "Does response depend on the outcome or exposure?",
            "Are only survivors or successful entities visible?",
            "Are inclusion probabilities unequal?",
            "Should weights be used?",
            "Could conditioning create collider bias?",
            "How sensitive are estimates to assumptions about missing groups?",
            "Does the reported uncertainty account for the actual sampling design?"
        };

        for (const string& question : questions) {
            cout << "- " << question << "\n";
        }
    }
};


// -----------------------------------------------------------------------------
// Complete case-study pipeline
// -----------------------------------------------------------------------------

class SamplingBiasCaseStudy {
public:
    SamplingBiasCaseStudy()
        : populationGenerator(42),
          samplingService(123),
          surveySimulator(555),
          survivorshipStudy(99),
          colliderStudy(15),
          bootstrapEstimator(321) {}

    void run() {
        printSection(
            "Sampling Bias Case Study: National Income Survey"
        );

        const size_t populationSize = 20000;

        vector<Person> population =
            populationGenerator.generatePeople(
                populationSize
            );

        reportPopulation(population);

        SelectionAnalyzer::reportSelectionBias(
            population
        );

        runSurveyAnalysis(population);

        runStratifiedSampling(population);

        runWeightedSampling(population);

        runBootstrap(population);

        runSurvivorshipAnalysis();

        runColliderAnalysis();

        sensitivityAnalysis(70.0, 0.80);

        runValidation();

        SamplingDiagnostics::printChecklist();
    }

private:
    void reportPopulation(
        const vector<Person>& population
    ) const {
        printSection("Population construction");

        const double populationIncome =
            SelectionAnalyzer::incomeMean(
                population
            );

        size_t employedCount = 0;
        size_t internetCount = 0;

        for (const Person& person : population) {
            if (person.employed) {
                ++employedCount;
            }

            if (person.internetAccess) {
                ++internetCount;
            }
        }

        cout << fixed << setprecision(2);

        cout << "Population size: "
             << population.size() << "\n";

        cout << "Population income mean: "
             << populationIncome << "\n";

        cout << "Employment rate: "
             << 100.0 *
                    static_cast<double>(employedCount) /
                    static_cast<double>(population.size())
             << "%\n";

        cout << "Internet access rate: "
             << 100.0 *
                    static_cast<double>(internetCount) /
                    static_cast<double>(population.size())
             << "%\n";
    }

    void runSurveyAnalysis(
        const vector<Person>& population
    ) {
        printSection("Nonresponse analysis");

        const auto [respondents, nonrespondents] =
            surveySimulator.conductSurvey(
                population
            );

        const double populationMean =
            SelectionAnalyzer::incomeMean(
                population
            );

        const double respondentMean =
            SelectionAnalyzer::incomeMean(
                respondents
            );

        cout << fixed << setprecision(2);

        cout << "Respondents: "
             << respondents.size() << "\n";

        cout << "Nonrespondents: "
             << nonrespondents.size() << "\n";

        cout << "Response rate: "
             << 100.0 *
                    static_cast<double>(respondents.size()) /
                    static_cast<double>(population.size())
             << "%\n";

        cout << "Population mean: "
             << populationMean << "\n";

        cout << "Respondent mean: "
             << respondentMean << "\n";

        cout << "Observed difference: "
             << respondentMean - populationMean
             << "\n";
    }

    void runStratifiedSampling(
        const vector<Person>& population
    ) {
        printSection("Stratified sampling");

        const vector<Person> sample =
            samplingService.stratifiedSample(
                population,
                100,
                100,
                100
            );

        cout << fixed << setprecision(2);

        cout << "Stratified sample size: "
             << sample.size() << "\n";

        cout << "Stratified sample mean: "
             << SelectionAnalyzer::incomeMean(sample)
             << "\n";
    }

    void runWeightedSampling(
        const vector<Person>& population
    ) {
        printSection(
            "Unequal selection probabilities and weighting"
        );

        mt19937 generator(555);
        uniform_real_distribution<double> uniform(0.0, 1.0);

        vector<SelectedPerson> selected;

        for (const Person& person : population) {
            const double probability =
                person.age >= 60
                    ? 0.15
                    : person.age >= 35
                        ? 0.40
                        : 0.70;

            if (uniform(generator) < probability) {
                selected.push_back({
                    person,
                    probability
                });
            }
        }

        vector<Person> unweightedPeople;

        for (const SelectedPerson& item : selected) {
            unweightedPeople.push_back(item.person);
        }

        const double unweighted =
            SelectionAnalyzer::incomeMean(
                unweightedPeople
            );

        const double weighted =
            SelectionAnalyzer::weightedMean(
                selected
            );

        const double populationMean =
            SelectionAnalyzer::incomeMean(
                population
            );

        cout << fixed << setprecision(2);

        cout << "Population mean: "
             << populationMean << "\n";

        cout << "Unweighted sample mean: "
             << unweighted << "\n";

        cout << "Weighted sample mean: "
             << weighted << "\n";

        cout << "\nThe weight is 1 / inclusion probability. "
             << "Low-probability observations therefore contribute "
             << "more to the weighted estimator.\n";
    }

    void runBootstrap(
        const vector<Person>& population
    ) {
        printSection("Bootstrap uncertainty");

        const vector<Person> sample =
            samplingService.simpleRandomSample(
                population,
                100
            );

        vector<double> incomes;

        for (const Person& person : sample) {
            incomes.push_back(person.income);
        }

        const BootstrapEstimator::Result result =
            bootstrapEstimator.estimateMean(
                incomes
            );

        cout << fixed << setprecision(2);

        cout << "Sample mean: "
             << mean(incomes) << "\n";

        cout << "Bootstrap mean: "
             << result.meanEstimate << "\n";

        cout << "Approximate 95% interval: ["
             << result.lower << ", "
             << result.upper << "]\n";

        cout << "\nBootstrap quantifies variation in estimates "
             << "under repeated resampling from the observed sample. "
             << "It does not restore units that were never sampled.\n";
    }

    void runSurvivorshipAnalysis() {
        const vector<Company> companies =
            survivorshipStudy.generateCompanies(
                10000
            );

        survivorshipStudy.report(
            companies
        );
    }

    void runColliderAnalysis() {
        const vector<Patient> patients =
            colliderStudy.generatePatients(
                15000
            );

        colliderStudy.report(
            patients
        );
    }

    void runValidation() {
        printSection("Validation and failure conditions");

        const vector<string> warnings =
            SamplingDiagnostics::validate(
                1000,
                250,
                0.62,
                false
            );

        for (const string& warning : warnings) {
            cout << "Warning: "
                 << warning << "\n";
        }

        try {
            vector<double> empty;
            mean(empty);
        } catch (const exception& error) {
            cout << "Handled empty-data error: "
                 << error.what() << "\n";
        }

        try {
            samplingService.simpleRandomSample(
                vector<Person>(10),
                20
            );
        } catch (const exception& error) {
            cout << "Handled invalid-sample error: "
                 << error.what() << "\n";
        }
    }

    PopulationGenerator populationGenerator;
    SamplingService samplingService;
    SurveySimulator surveySimulator;
    SurvivorshipStudy survivorshipStudy;
    ColliderStudy colliderStudy;
    BootstrapEstimator bootstrapEstimator;
};


// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

int main() {
    try {
        SamplingBiasCaseStudy caseStudy;
        caseStudy.run();

        return 0;
    } catch (const exception& error) {
        cerr << "Fatal error: "
             << error.what()
             << "\n";

        return 1;
    }
}
