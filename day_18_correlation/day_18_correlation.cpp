/*
 * Correlation: Measuring Relationships Between Variables
 * ========================================================
 *
 * C++17 industry-style case study:
 *
 * A business analytics service receives paired observations describing
 * advertising expenditure, website traffic, customer conversions, and sales.
 *
 * The program progressively develops:
 *   - typed observations
 *   - validation
 *   - covariance
 *   - Pearson correlation
 *   - ranking
 *   - Spearman correlation
 *   - Kendall-style concordance
 *   - correlation matrices
 *   - simple linear regression
 *   - partial correlation
 *   - bootstrap estimation
 *   - permutation testing
 *   - practical reporting
 *
 * Compile:
 *   g++ -std=c++17 -O2 correlation_case_study.cpp -o correlation_case_study
 *
 * Run:
 *   ./correlation_case_study
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using std::cout;
using std::endl;
using std::invalid_argument;
using std::map;
using std::size_t;
using std::string;
using std::vector;


// ============================================================================
// 1. DATA MODEL
// ============================================================================

struct Observation {
    double advertising;
    double websiteVisits;
    double conversions;
    double sales;
};

struct RegressionResult {
    double intercept;
    double slope;
    double correlation;
    double rSquared;

    double predict(double x) const {
        return intercept + slope * x;
    }
};


// ============================================================================
// 2. VALIDATION
// ============================================================================

void validatePair(
    const vector<double>& x,
    const vector<double>& y
) {
    if (x.size() != y.size()) {
        throw invalid_argument(
            "Correlation variables must contain equal numbers of observations."
        );
    }

    if (x.size() < 2) {
        throw invalid_argument(
            "At least two paired observations are required."
        );
    }

    for (double value : x) {
        if (!std::isfinite(value)) {
            throw invalid_argument(
                "X contains a non-finite value."
            );
        }
    }

    for (double value : y) {
        if (!std::isfinite(value)) {
            throw invalid_argument(
                "Y contains a non-finite value."
            );
        }
    }
}


double mean(const vector<double>& values) {
    if (values.empty()) {
        throw invalid_argument("Mean requires observations.");
    }

    return std::accumulate(
        values.begin(),
        values.end(),
        0.0
    ) / static_cast<double>(values.size());
}


// ============================================================================
// 3. COVARIANCE
// ============================================================================

double sampleCovariance(
    const vector<double>& x,
    const vector<double>& y
) {
    validatePair(x, y);

    const double xMean = mean(x);
    const double yMean = mean(y);

    double crossDeviation = 0.0;

    for (size_t i = 0; i < x.size(); ++i) {
        crossDeviation +=
            (x[i] - xMean) * (y[i] - yMean);
    }

    return crossDeviation /
        static_cast<double>(x.size() - 1);
}


// ============================================================================
// 4. PEARSON CORRELATION
// ============================================================================

double pearsonCorrelation(
    const vector<double>& x,
    const vector<double>& y
) {
    validatePair(x, y);

    const double xMean = mean(x);
    const double yMean = mean(y);

    double numerator = 0.0;
    double xSquared = 0.0;
    double ySquared = 0.0;

    for (size_t i = 0; i < x.size(); ++i) {
        const double centeredX = x[i] - xMean;
        const double centeredY = y[i] - yMean;

        numerator += centeredX * centeredY;
        xSquared += centeredX * centeredX;
        ySquared += centeredY * centeredY;
    }

    const double denominator =
        std::sqrt(xSquared * ySquared);

    if (denominator == 0.0) {
        throw invalid_argument(
            "Pearson correlation is undefined when a variable has zero variance."
        );
    }

    return numerator / denominator;
}


// ============================================================================
// 5. RANKING WITH TIES
// ============================================================================

vector<double> rankWithTies(
    const vector<double>& values
) {
    vector<std::pair<double, size_t>> indexed;

    for (size_t i = 0; i < values.size(); ++i) {
        indexed.emplace_back(values[i], i);
    }

    std::sort(
        indexed.begin(),
        indexed.end(),
        [](const auto& left, const auto& right) {
            return left.first < right.first;
        }
    );

    vector<double> ranks(values.size());

    size_t position = 0;

    while (position < indexed.size()) {
        size_t end = position + 1;

        while (
            end < indexed.size() &&
            indexed[end].first == indexed[position].first
        ) {
            ++end;
        }

        // Statistical ranks are one-based. For example, positions 1 and 2
        // tied together receive average rank 1.5.
        const double averageRank =
            (
                static_cast<double>(position + 1) +
                static_cast<double>(end)
            ) / 2.0;

        for (size_t i = position; i < end; ++i) {
            ranks[indexed[i].second] = averageRank;
        }

        position = end;
    }

    return ranks;
}


// ============================================================================
// 6. SPEARMAN CORRELATION
// ============================================================================

double spearmanCorrelation(
    const vector<double>& x,
    const vector<double>& y
) {
    validatePair(x, y);

    const vector<double> xRanks =
        rankWithTies(x);

    const vector<double> yRanks =
        rankWithTies(y);

    return pearsonCorrelation(xRanks, yRanks);
}


// ============================================================================
// 7. KENDALL TAU-B
// ============================================================================

double kendallTauB(
    const vector<double>& x,
    const vector<double>& y
) {
    validatePair(x, y);

    long long concordant = 0;
    long long discordant = 0;
    long long tiesXOnly = 0;
    long long tiesYOnly = 0;

    for (size_t i = 0; i + 1 < x.size(); ++i) {
        for (size_t j = i + 1; j < x.size(); ++j) {
            const double dx = x[j] - x[i];
            const double dy = y[j] - y[i];

            if (dx == 0.0 && dy == 0.0) {
                continue;
            }

            if (dx == 0.0) {
                ++tiesXOnly;
            } else if (dy == 0.0) {
                ++tiesYOnly;
            } else if (dx * dy > 0.0) {
                ++concordant;
            } else {
                ++discordant;
            }
        }
    }

    const double denominator = std::sqrt(
        static_cast<double>(
            concordant + discordant + tiesXOnly
        ) *
        static_cast<double>(
            concordant + discordant + tiesYOnly
        )
    );

    if (denominator == 0.0) {
        throw invalid_argument(
            "Kendall tau-b is undefined for this data."
        );
    }

    return static_cast<double>(
        concordant - discordant
    ) / denominator;
}


// ============================================================================
// 8. LINEAR REGRESSION
// ============================================================================

RegressionResult simpleLinearRegression(
    const vector<double>& x,
    const vector<double>& y
) {
    validatePair(x, y);

    const double xMean = mean(x);
    const double yMean = mean(y);

    double numerator = 0.0;
    double denominator = 0.0;

    for (size_t i = 0; i < x.size(); ++i) {
        numerator +=
            (x[i] - xMean) * (y[i] - yMean);

        denominator +=
            (x[i] - xMean) * (x[i] - xMean);
    }

    if (denominator == 0.0) {
        throw invalid_argument(
            "Regression predictor has zero variance."
        );
    }

    const double slope =
        numerator / denominator;

    const double intercept =
        yMean - slope * xMean;

    const double r =
        pearsonCorrelation(x, y);

    return {
        intercept,
        slope,
        r,
        r * r
    };
}


// ============================================================================
// 9. RESIDUALS AND PARTIAL CORRELATION
// ============================================================================

vector<double> residualsAfterRegression(
    const vector<double>& target,
    const vector<double>& control
) {
    const RegressionResult regression =
        simpleLinearRegression(control, target);

    vector<double> residuals;

    residuals.reserve(target.size());

    for (size_t i = 0; i < target.size(); ++i) {
        const double predicted =
            regression.predict(control[i]);

        residuals.push_back(
            target[i] - predicted
        );
    }

    return residuals;
}


double partialCorrelation(
    const vector<double>& x,
    const vector<double>& y,
    const vector<double>& control
) {
    validatePair(x, y);
    validatePair(x, control);

    const vector<double> xResiduals =
        residualsAfterRegression(x, control);

    const vector<double> yResiduals =
        residualsAfterRegression(y, control);

    return pearsonCorrelation(
        xResiduals,
        yResiduals
    );
}


// ============================================================================
// 10. CORRELATION MATRIX
// ============================================================================

class CorrelationMatrix {
private:
    map<string, vector<double>> data;

public:
    void addVariable(
        const string& name,
        const vector<double>& values
    ) {
        if (values.empty()) {
            throw invalid_argument(
                "Cannot add an empty variable."
            );
        }

        data[name] = values;
    }

    vector<string> variableNames() const {
        vector<string> names;

        for (const auto& entry : data) {
            names.push_back(entry.first);
        }

        return names;
    }

    double get(
        const string& first,
        const string& second
    ) const {
        const auto firstIt = data.find(first);
        const auto secondIt = data.find(second);

        if (
            firstIt == data.end() ||
            secondIt == data.end()
        ) {
            throw invalid_argument(
                "Unknown variable in correlation matrix."
            );
        }

        return pearsonCorrelation(
            firstIt->second,
            secondIt->second
        );
    }

    void print() const {
        const vector<string> names =
            variableNames();

        cout << std::setw(18) << "";

        for (const string& name : names) {
            cout << std::setw(16)
                 << name;
        }

        cout << '\n';

        for (const string& row : names) {
            cout << std::setw(18)
                 << row;

            for (const string& column : names) {
                cout << std::setw(16)
                     << std::fixed
                     << std::setprecision(3)
                     << get(row, column);
            }

            cout << '\n';
        }
    }
};


// ============================================================================
// 11. ANALYTICS SERVICE
// ============================================================================

class CorrelationAnalyticsService {
public:
    static void validateRecords(
        const vector<Observation>& records
    ) {
        if (records.size() < 2) {
            throw invalid_argument(
                "The analytics service needs at least two observations."
            );
        }

        for (const Observation& record : records) {
            if (
                !std::isfinite(record.advertising) ||
                !std::isfinite(record.websiteVisits) ||
                !std::isfinite(record.conversions) ||
                !std::isfinite(record.sales)
            ) {
                throw invalid_argument(
                    "Records contain non-finite numeric values."
                );
            }

            if (
                record.advertising < 0 ||
                record.websiteVisits < 0 ||
                record.conversions < 0 ||
                record.sales < 0
            ) {
                throw invalid_argument(
                    "Business measurements cannot be negative."
                );
            }
        }
    }

    static CorrelationMatrix buildMatrix(
        const vector<Observation>& records
    ) {
        validateRecords(records);

        vector<double> advertising;
        vector<double> websiteVisits;
        vector<double> conversions;
        vector<double> sales;

        advertising.reserve(records.size());
        websiteVisits.reserve(records.size());
        conversions.reserve(records.size());
        sales.reserve(records.size());

        for (const Observation& record : records) {
            advertising.push_back(record.advertising);
            websiteVisits.push_back(record.websiteVisits);
            conversions.push_back(record.conversions);
            sales.push_back(record.sales);
        }

        CorrelationMatrix matrix;

        matrix.addVariable(
            "Advertising",
            advertising
        );

        matrix.addVariable(
            "Visits",
            websiteVisits
        );

        matrix.addVariable(
            "Conversions",
            conversions
        );

        matrix.addVariable(
            "Sales",
            sales
        );

        return matrix;
    }
};


// ============================================================================
// 12. BOOTSTRAP ESTIMATION
// ============================================================================

class BootstrapEstimator {
public:
    static std::pair<double, double> confidenceInterval(
        const vector<double>& x,
        const vector<double>& y,
        size_t repetitions = 3000,
        double confidence = 0.95,
        unsigned int seed = 42
    ) {
        validatePair(x, y);

        if (repetitions < 100) {
            throw invalid_argument(
                "Bootstrap needs at least 100 repetitions."
            );
        }

        if (!(confidence > 0.0 && confidence < 1.0)) {
            throw invalid_argument(
                "Confidence must be between 0 and 1."
            );
        }

        std::mt19937 generator(seed);

        std::uniform_int_distribution<size_t>
            indexDistribution(0, x.size() - 1);

        vector<double> estimates;
        estimates.reserve(repetitions);

        for (size_t repetition = 0;
             repetition < repetitions;
             ++repetition) {

            vector<double> sampleX;
            vector<double> sampleY;

            sampleX.reserve(x.size());
            sampleY.reserve(y.size());

            for (size_t i = 0; i < x.size(); ++i) {
                const size_t index =
                    indexDistribution(generator);

                sampleX.push_back(x[index]);
                sampleY.push_back(y[index]);
            }

            try {
                estimates.push_back(
                    pearsonCorrelation(
                        sampleX,
                        sampleY
                    )
                );
            } catch (const invalid_argument&) {
                // Constant bootstrap samples can occur with small datasets.
            }
        }

        if (estimates.empty()) {
            throw invalid_argument(
                "No valid bootstrap estimates were generated."
            );
        }

        std::sort(
            estimates.begin(),
            estimates.end()
        );

        const double alpha =
            1.0 - confidence;

        const size_t lowerIndex =
            static_cast<size_t>(
                (alpha / 2.0) *
                static_cast<double>(estimates.size() - 1)
            );

        const size_t upperIndex =
            static_cast<size_t>(
                (1.0 - alpha / 2.0) *
                static_cast<double>(estimates.size() - 1)
            );

        return {
            estimates[lowerIndex],
            estimates[upperIndex]
        };
    }
};


// ============================================================================
// 13. PERMUTATION TEST
// ============================================================================

class PermutationTest {
public:
    static double pValue(
        const vector<double>& x,
        const vector<double>& y,
        size_t repetitions = 3000,
        unsigned int seed = 42
    ) {
        validatePair(x, y);

        if (repetitions < 100) {
            throw invalid_argument(
                "Permutation testing needs at least 100 repetitions."
            );
        }

        const double observed =
            pearsonCorrelation(x, y);

        vector<double> shuffledY = y;

        std::mt19937 generator(seed);

        size_t extreme = 0;

        for (size_t repetition = 0;
             repetition < repetitions;
             ++repetition) {

            std::shuffle(
                shuffledY.begin(),
                shuffledY.end(),
                generator
            );

            const double permuted =
                pearsonCorrelation(
                    x,
                    shuffledY
                );

            if (
                std::abs(permuted) >=
                std::abs(observed)
            ) {
                ++extreme;
            }
        }

        return (
            static_cast<double>(extreme + 1)
            /
            static_cast<double>(repetitions + 1)
        );
    }
};


// ============================================================================
// 14. REPORTING
// ============================================================================

class CorrelationReport {
public:
    static string strength(double r) {
        const double magnitude =
            std::abs(r);

        if (magnitude < 0.10) {
            return "negligible";
        }

        if (magnitude < 0.30) {
            return "weak";
        }

        if (magnitude < 0.50) {
            return "moderate";
        }

        if (magnitude < 0.70) {
            return "substantial";
        }

        if (magnitude < 0.90) {
            return "strong";
        }

        return "very strong";
    }

    static void print(
        const string& firstVariable,
        const string& secondVariable,
        double r
    ) {
        cout
            << firstVariable
            << " vs "
            << secondVariable
            << ": r = "
            << std::fixed
            << std::setprecision(4)
            << r
            << " ("
            << strength(r)
            << " ";

        if (r > 0.0) {
            cout << "positive";
        } else if (r < 0.0) {
            cout << "negative";
        } else {
            cout << "linear";
        }

        cout << " association)\n";
    }
};


// ============================================================================
// 15. TESTS
// ============================================================================

void assertClose(
    double actual,
    double expected,
    double tolerance = 1e-10
) {
    if (std::abs(actual - expected) > tolerance) {
        throw std::runtime_error(
            "Numerical assertion failed."
        );
    }
}


void runTests() {
    cout << "\n--- Automated Tests ---\n";

    const vector<double> x{
        1, 2, 3, 4, 5
    };

    const vector<double> positive{
        2, 4, 6, 8, 10
    };

    const vector<double> negative{
        -2, -4, -6, -8, -10
    };

    assertClose(
        pearsonCorrelation(x, positive),
        1.0
    );

    assertClose(
        pearsonCorrelation(x, negative),
        -1.0
    );

    assertClose(
        spearmanCorrelation(
            x,
            positive
        ),
        1.0
    );

    assertClose(
        kendallTauB(
            x,
            positive
        ),
        1.0
    );

    const RegressionResult regression =
        simpleLinearRegression(
            x,
            positive
        );

    assertClose(
        regression.slope,
        2.0
    );

    assertClose(
        regression.intercept,
        0.0
    );

    assertClose(
        regression.rSquared,
        1.0
    );

    cout << "All C++ tests passed.\n";
}


// ============================================================================
// 16. EDGE CASE DEMONSTRATIONS
// ============================================================================

void demonstrateEdgeCases() {
    cout << "\n--- Edge Cases ---\n";

    try {
        pearsonCorrelation(
            {1, 1, 1, 1},
            {2, 3, 4, 5}
        );
    } catch (const invalid_argument& error) {
        cout << "Constant-variable error: "
             << error.what()
             << '\n';
    }

    try {
        pearsonCorrelation(
            {1, 2, 3},
            {1, 2}
        );
    } catch (const invalid_argument& error) {
        cout << "Length mismatch error: "
             << error.what()
             << '\n';
    }

    try {
        pearsonCorrelation(
            {1, 2, std::numeric_limits<double>::quiet_NaN()},
            {2, 3, 4}
        );
    } catch (const invalid_argument& error) {
        cout << "Non-finite-value error: "
             << error.what()
             << '\n';
    }
}


// ============================================================================
// 17. MAIN INDUSTRY CASE STUDY
// ============================================================================

int main() {
    try {
        cout << "============================================================\n";
        cout << "Correlation Analytics Service\n";
        cout << "============================================================\n";

        /*
         * Each record represents a time period. The data are synthetic and
         * intentionally small so the statistical mechanisms remain visible.
         */
        const vector<Observation> records{
            {12, 180, 12, 25},
            {15, 210, 14, 30},
            {17, 240, 16, 32},
            {20, 260, 18, 39},
            {22, 300, 21, 43},
            {25, 340, 24, 49},
            {27, 360, 26, 52},
            {30, 410, 30, 60},
            {34, 450, 34, 67},
            {36, 470, 36, 70}
        };

        CorrelationMatrix matrix =
            CorrelationAnalyticsService::buildMatrix(
                records
            );

        cout << "\n--- Correlation Matrix ---\n";
        matrix.print();

        vector<double> advertising;
        vector<double> visits;
        vector<double> conversions;
        vector<double> sales;

        for (const Observation& record : records) {
            advertising.push_back(
                record.advertising
            );

            visits.push_back(
                record.websiteVisits
            );

            conversions.push_back(
                record.conversions
            );

            sales.push_back(
                record.sales
            );
        }

        cout << "\n--- Selected Relationships ---\n";

        const double advertisingSales =
            pearsonCorrelation(
                advertising,
                sales
            );

        CorrelationReport::print(
            "Advertising",
            "Sales",
            advertisingSales
        );

        const double visitsSales =
            pearsonCorrelation(
                visits,
                sales
            );

        CorrelationReport::print(
            "Website visits",
            "Sales",
            visitsSales
        );

        const double conversionsSales =
            pearsonCorrelation(
                conversions,
                sales
            );

        CorrelationReport::print(
            "Conversions",
            "Sales",
            conversionsSales
        );

        cout << "\n--- Rank-Based Measures ---\n";

        cout
            << "Spearman advertising-sales: "
            << spearmanCorrelation(
                advertising,
                sales
            )
            << '\n';

        cout
            << "Kendall tau-b advertising-sales: "
            << kendallTauB(
                advertising,
                sales
            )
            << '\n';

        cout << "\n--- Regression ---\n";

        const RegressionResult regression =
            simpleLinearRegression(
                advertising,
                sales
            );

        cout
            << "Intercept: "
            << regression.intercept
            << '\n';

        cout
            << "Slope: "
            << regression.slope
            << '\n';

        cout
            << "Correlation: "
            << regression.correlation
            << '\n';

        cout
            << "R-squared: "
            << regression.rSquared
            << '\n';

        cout
            << "Predicted sales at advertising=40: "
            << regression.predict(40)
            << '\n';

        cout << "\n--- Partial Correlation ---\n";

        /*
         * Treat website traffic as a control variable. This asks whether
         * advertising and sales remain linearly associated after removing
         * their linear relationships with website traffic.
         */
        const double partial =
            partialCorrelation(
                advertising,
                sales,
                visits
            );

        cout
            << "Advertising-sales partial correlation "
               "controlling for visits: "
            << partial
            << '\n';

        cout << "\n--- Bootstrap Confidence Interval ---\n";

        const auto interval =
            BootstrapEstimator::confidenceInterval(
                advertising,
                sales,
                3000,
                0.95,
                42
            );

        cout
            << "Approximate bootstrap 95% interval: ["
            << interval.first
            << ", "
            << interval.second
            << "]\n";

        cout << "\n--- Permutation Test ---\n";

        const double pValue =
            PermutationTest::pValue(
                advertising,
                sales,
                3000,
                42
            );

        cout
            << "Estimated two-sided permutation p-value: "
            << pValue
            << '\n';

        cout << "\n--- Interpretation Constraints ---\n";

        cout
            << "1. Correlation describes association and does not establish "
               "causation.\n";

        cout
            << "2. Pearson correlation specifically measures linear "
               "association.\n";

        cout
            << "3. Strong correlation can be produced by confounding "
               "variables or common trends.\n";

        cout
            << "4. Outliers can materially change Pearson correlation.\n";

        cout
            << "5. A correlation matrix does not automatically provide a "
               "causal model.\n";

        cout
            << "6. Historical correlations can change when the data-generating "
               "process changes.\n";

        demonstrateEdgeCases();
        runTests();

        cout << "\n============================================================\n";
        cout << "Case study completed successfully.\n";
        cout << "============================================================\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
