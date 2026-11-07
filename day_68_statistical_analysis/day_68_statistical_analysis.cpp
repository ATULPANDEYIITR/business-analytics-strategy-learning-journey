#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

class StatisticalException : public runtime_error {
public:
    explicit StatisticalException(const string& message)
        : runtime_error(message) {}
};

struct RegressionResult {
    double slope;
    double intercept;
    double r_squared;
};

struct ConfidenceInterval {
    double mean;
    double lower;
    double upper;
    double standard_error;
};

struct StatisticalReport {
    size_t observations;
    double mean;
    double median;
    double minimum;
    double maximum;
    double range;
    double sample_variance;
    double population_variance;
    double sample_std;
    double population_std;
    double q1;
    double q3;
    vector<double> modes;
    vector<double> outliers;
};

class StatisticalEngine {
private:
    static vector<double> validate(
        const vector<double>& data,
        size_t minimum = 1
    ) {
        if (data.size() < minimum) {
            throw StatisticalException(
                "Insufficient observations."
            );
        }

        for (double value : data) {
            if (!isfinite(value)) {
                throw StatisticalException(
                    "Non-finite observations are prohibited."
                );
            }
        }

        return data;
    }

    static double interpolate(
        const vector<double>& sorted,
        double position
    ) {
        size_t lower = static_cast<size_t>(floor(position));
        size_t upper = static_cast<size_t>(ceil(position));

        if (lower == upper) {
            return sorted[lower];
        }

        double fraction = position - lower;

        return sorted[lower] +
            fraction * (sorted[upper] - sorted[lower]);
    }

public:
    static double mean(const vector<double>& data) {
        auto values = validate(data);

        return accumulate(
            values.begin(), values.end(), 0.0
        ) / values.size();
    }

    static double median(const vector<double>& data) {
        auto values = validate(data);
        sort(values.begin(), values.end());

        size_t middle = values.size() / 2;

        if (values.size() % 2 == 0) {
            return (
                values[middle - 1] + values[middle]
            ) / 2.0;
        }

        return values[middle];
    }

    static double percentile(
        const vector<double>& data,
        double percentage
    ) {
        auto values = validate(data);
        sort(values.begin(), values.end());

        if (
            !isfinite(percentage) ||
            percentage < 0 ||
            percentage > 100
        ) {
            throw StatisticalException(
                "Invalid percentile."
            );
        }

        double position =
            (values.size() - 1) * percentage / 100.0;

        return interpolate(values, position);
    }

    static double variance(
        const vector<double>& data,
        bool sample = true
    ) {
        auto values = validate(data, sample ? 2 : 1);

        double average = mean(values);

        double sum = 0.0;

        for (double value : values) {
            sum += (value - average) * (value - average);
        }

        return sum / (
            values.size() - (sample ? 1 : 0)
        );
    }

    static double standardDeviation(
        const vector<double>& data,
        bool sample = true
    ) {
        return sqrt(variance(data, sample));
    }

    static map<double, int> frequency(
        const vector<double>& data
    ) {
        auto values = validate(data);
        map<double, int> counts;

        for (double value : values) {
            counts[value]++;
        }

        return counts;
    }

    static vector<double> mode(
        const vector<double>& data
    ) {
        auto counts = frequency(data);

        int maximum = 0;

        for (const auto& item : counts) {
            maximum = max(maximum, item.second);
        }

        vector<double> result;

        for (const auto& item : counts) {
            if (item.second == maximum) {
                result.push_back(item.first);
            }
        }

        return result;
    }

    static pair<double, double> quartiles(
        const vector<double>& data
    ) {
        return {
            percentile(data, 25),
            percentile(data, 75)
        };
    }

    static vector<double> outliers(
        const vector<double>& data
    ) {
        auto values = validate(data, 2);
        auto [q1, q3] = quartiles(values);

        double iqr = q3 - q1;
        double lower = q1 - 1.5 * iqr;
        double upper = q3 + 1.5 * iqr;

        vector<double> result;

        for (double value : values) {
            if (value < lower || value > upper) {
                result.push_back(value);
            }
        }

        return result;
    }

    static double covariance(
        const vector<double>& x,
        const vector<double>& y
    ) {
        auto first = validate(x, 2);
        auto second = validate(y, 2);

        if (first.size() != second.size()) {
            throw StatisticalException(
                "Paired datasets must have equal lengths."
            );
        }

        double mean_x = mean(first);
        double mean_y = mean(second);
        double total = 0.0;

        for (size_t i = 0; i < first.size(); i++) {
            total +=
                (first[i] - mean_x) *
                (second[i] - mean_y);
        }

        return total / (first.size() - 1);
    }

    static double correlation(
        const vector<double>& x,
        const vector<double>& y
    ) {
        double std_x = standardDeviation(x);
        double std_y = standardDeviation(y);

        if (std_x == 0 || std_y == 0) {
            throw StatisticalException(
                "Correlation is undefined for constant data."
            );
        }

        double result =
            covariance(x, y) / (std_x * std_y);

        return clamp(result, -1.0, 1.0);
    }

    static RegressionResult regression(
        const vector<double>& x,
        const vector<double>& y
    ) {
        auto first = validate(x, 2);
        auto second = validate(y, 2);

        if (first.size() != second.size()) {
            throw StatisticalException(
                "Paired datasets must have equal lengths."
            );
        }

        double mean_x = mean(first);
        double mean_y = mean(second);

        double numerator = 0.0;
        double denominator = 0.0;

        for (size_t i = 0; i < first.size(); i++) {
            numerator +=
                (first[i] - mean_x) *
                (second[i] - mean_y);

            denominator +=
                (first[i] - mean_x) *
                (first[i] - mean_x);
        }

        if (denominator == 0) {
            throw StatisticalException(
                "Regression requires varying independent data."
            );
        }

        double slope = numerator / denominator;
        double intercept = mean_y - slope * mean_x;

        double total_ss = 0.0;
        double residual_ss = 0.0;

        for (size_t i = 0; i < first.size(); i++) {
            double prediction =
                slope * first[i] + intercept;

            total_ss += pow(second[i] - mean_y, 2);
            residual_ss += pow(
                second[i] - prediction, 2
            );
        }

        double r_squared = total_ss == 0
            ? numeric_limits<double>::quiet_NaN()
            : 1.0 - residual_ss / total_ss;

        return {slope, intercept, r_squared};
    }

    static ConfidenceInterval confidenceInterval(
        const vector<double>& data,
        double z = 1.96
    ) {
        auto values = validate(data, 2);

        if (!isfinite(z) || z <= 0) {
            throw StatisticalException(
                "Z-score must be positive and finite."
            );
        }

        double average = mean(values);
        double standard_error =
            standardDeviation(values) /
            sqrt(static_cast<double>(values.size()));

        double margin = z * standard_error;

        return {
            average,
            average - margin,
            average + margin,
            standard_error
        };
    }

    static StatisticalReport analyze(
        const vector<double>& data
    ) {
        auto values = validate(data, 2);

        double minimum = *min_element(
            values.begin(), values.end()
        );

        double maximum = *max_element(
            values.begin(), values.end()
        );

        auto [q1, q3] = quartiles(values);

        return {
            values.size(),
            mean(values),
            median(values),
            minimum,
            maximum,
            maximum - minimum,
            variance(values),
            variance(values, false),
            standardDeviation(values),
            standardDeviation(values, false),
            q1,
            q3,
            mode(values),
            outliers(values)
        };
    }
};

class BootstrapAnalyzer {
public:
    static ConfidenceInterval analyze(
        const vector<double>& data,
        int iterations = 2000,
        unsigned int seed = 42
    ) {
        if (iterations < 100 || iterations > 1000000) {
            throw StatisticalException(
                "Invalid bootstrap iteration count."
            );
        }

        auto values = data;

        if (values.size() < 2) {
            throw StatisticalException(
                "Bootstrap requires at least two observations."
            );
        }

        for (double value : values) {
            if (!isfinite(value)) {
                throw StatisticalException(
                    "Invalid bootstrap observation."
                );
            }
        }

        mt19937 generator(seed);
        uniform_int_distribution<size_t> distribution(
            0, values.size() - 1
        );

        vector<double> estimates;
        estimates.reserve(iterations);

        for (int i = 0; i < iterations; i++) {
            double total = 0;

            for (size_t j = 0; j < values.size(); j++) {
                total += values[distribution(generator)];
            }

            estimates.push_back(total / values.size());
        }

        sort(estimates.begin(), estimates.end());

        return {
            StatisticalEngine::mean(estimates),
            StatisticalEngine::percentile(estimates, 2.5),
            StatisticalEngine::percentile(estimates, 97.5),
            0.0
        };
    }
};

void runTests() {
    vector<double> values = {10, 20, 20, 30, 40};

    if (abs(StatisticalEngine::mean(values) - 24.0) > 1e-9) {
        throw StatisticalException("Mean test failed.");
    }

    if (StatisticalEngine::median(values) != 20) {
        throw StatisticalException("Median test failed.");
    }

    if (StatisticalEngine::mode(values).front() != 20) {
        throw StatisticalException("Mode test failed.");
    }

    bool rejected = false;

    try {
        StatisticalEngine::correlation(
            {1, 1, 1}, {2, 3, 4}
        );
    } catch (const StatisticalException&) {
        rejected = true;
    }

    if (!rejected) {
        throw StatisticalException(
            "Constant-data validation test failed."
        );
    }

    cout << "All statistical tests passed.\n";
}

int main() {
    try {
        cout << fixed << setprecision(4);

        vector<double> scores = {
            45, 52, 56, 60, 62, 65, 67, 68,
            70, 72, 72, 75, 78, 80, 82, 85,
            88, 90, 92, 95, 98, 100, 105, 150
        };

        cout << "STATISTICAL ANALYSIS ENGINE\n";
        cout << "===========================\n";

        StatisticalReport report =
            StatisticalEngine::analyze(scores);

        cout << "\nDESCRIPTIVE STATISTICS\n";
        cout << "Observations: "
             << report.observations << '\n';
        cout << "Mean: " << report.mean << '\n';
        cout << "Median: " << report.median << '\n';
        cout << "Minimum: " << report.minimum << '\n';
        cout << "Maximum: " << report.maximum << '\n';
        cout << "Range: " << report.range << '\n';
        cout << "Sample variance: "
             << report.sample_variance << '\n';
        cout << "Population variance: "
             << report.population_variance << '\n';
        cout << "Sample standard deviation: "
             << report.sample_std << '\n';
        cout << "Population standard deviation: "
             << report.population_std << '\n';
        cout << "Q1: " << report.q1 << '\n';
        cout << "Q3: " << report.q3 << '\n';

        cout << "Modes: ";

        for (double value : report.modes) {
            cout << value << " ";
        }

        cout << "\nOutliers: ";

        for (double value : report.outliers) {
            cout << value << " ";
        }

        cout << '\n';

        vector<double> hours = {
            1, 2, 2, 3, 3, 4, 4, 5,
            5, 6, 6, 7, 7, 8, 8, 9
        };

        vector<double> performance = {
            35, 42, 45, 48, 52, 55, 58, 62,
            65, 68, 70, 74, 77, 81, 85, 90
        };

        cout << "\nCORRELATION\n";
        cout << StatisticalEngine::correlation(
            hours, performance
        ) << '\n';

        cout << "\nLINEAR REGRESSION\n";

        RegressionResult regression =
            StatisticalEngine::regression(
                hours, performance
            );

        cout << "Slope: " << regression.slope << '\n';
        cout << "Intercept: " << regression.intercept << '\n';
        cout << "R-squared: " << regression.r_squared << '\n';

        cout << "\nMEAN CONFIDENCE INTERVAL\n";

        auto interval =
            StatisticalEngine::confidenceInterval(scores);

        cout << "Mean: " << interval.mean << '\n';
        cout << "Lower: " << interval.lower << '\n';
        cout << "Upper: " << interval.upper << '\n';

        cout << "\nBOOTSTRAP ESTIMATION\n";

        auto bootstrap =
            BootstrapAnalyzer::analyze(scores);

        cout << "Bootstrap mean: "
             << bootstrap.mean << '\n';
        cout << "Lower 95%: "
             << bootstrap.lower << '\n';
        cout << "Upper 95%: "
             << bootstrap.upper << '\n';

        cout << "\nVALIDATION\n";
        runTests();

        cout << "\nAnalysis completed successfully.\n";

    } catch (const exception& error) {
        cerr << "Analysis error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
