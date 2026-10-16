#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

struct PullFreeObservation {
    std::string day;
    double value;
    std::string region;
    std::string category;
};

class GovernanceAnalytics {
private:
    std::vector<PullFreeObservation> observations;

    static double mean(const std::vector<double>& values) {
        if (values.empty()) {
            throw std::invalid_argument("Mean requires observations.");
        }

        return std::accumulate(values.begin(), values.end(), 0.0) /
               static_cast<double>(values.size());
    }

    static double percentile(
        std::vector<double> values,
        double percentage
    ) {
        if (values.empty() || percentage < 0 || percentage > 100) {
            throw std::invalid_argument("Invalid percentile request.");
        }

        std::sort(values.begin(), values.end());

        double position =
            (values.size() - 1) * percentage / 100.0;

        std::size_t lower =
            static_cast<std::size_t>(std::floor(position));
        std::size_t upper =
            static_cast<std::size_t>(std::ceil(position));

        if (lower == upper) {
            return values[lower];
        }

        double fraction = position - lower;

        return values[lower] +
               (values[upper] - values[lower]) * fraction;
    }

    static double standardDeviation(
        const std::vector<double>& values
    ) {
        if (values.size() < 2) {
            return 0.0;
        }

        double average = mean(values);
        double squaredError = 0.0;

        for (double value : values) {
            squaredError += std::pow(value - average, 2);
        }

        return std::sqrt(
            squaredError / static_cast<double>(values.size() - 1)
        );
    }

public:
    explicit GovernanceAnalytics(
        std::vector<PullFreeObservation> data
    )
        : observations(std::move(data)) {}

    std::vector<double> values() const {
        std::vector<double> result;
        result.reserve(observations.size());

        for (const auto& observation : observations) {
            result.push_back(observation.value);
        }

        return result;
    }

    void validate() const {
        for (const auto& observation : observations) {
            if (observation.day.empty()) {
                throw std::invalid_argument(
                    "Observation has no date."
                );
            }

            if (!std::isfinite(observation.value)) {
                throw std::invalid_argument(
                    "Observation contains a non-finite value."
                );
            }

            if (observation.region.empty() ||
                observation.category.empty()) {
                throw std::invalid_argument(
                    "Observation requires region and category."
                );
            }
        }
    }

    void describe() const {
        auto data = values();

        double q1 = percentile(data, 25);
        double median = percentile(data, 50);
        double q3 = percentile(data, 75);

        std::cout << "\nDistribution\n";
        std::cout << "Count: " << data.size() << '\n';
        std::cout << "Mean: " << mean(data) << '\n';
        std::cout << "Median: " << median << '\n';
        std::cout << "Q1: " << q1 << '\n';
        std::cout << "Q3: " << q3 << '\n';
        std::cout << "IQR: " << q3 - q1 << '\n';
        std::cout << "Std Dev: " << standardDeviation(data) << '\n';
        std::cout << "Minimum: "
                  << *std::min_element(data.begin(), data.end())
                  << '\n';
        std::cout << "Maximum: "
                  << *std::max_element(data.begin(), data.end())
                  << '\n';
    }

    std::vector<std::pair<std::size_t, double>>
    detectGlobalOutliers() const {
        auto data = values();

        double q1 = percentile(data, 25);
        double q3 = percentile(data, 75);
        double iqr = q3 - q1;

        double lower = q1 - 1.5 * iqr;
        double upper = q3 + 1.5 * iqr;

        std::vector<std::pair<std::size_t, double>> result;

        for (std::size_t index = 0; index < data.size(); ++index) {
            if (data[index] < lower || data[index] > upper) {
                result.emplace_back(index, data[index]);
            }
        }

        return result;
    }

    std::map<std::string, double> averageBy(
        const std::string& dimension
    ) const {
        std::map<std::string, std::vector<double>> groups;

        for (const auto& observation : observations) {
            if (dimension == "region") {
                groups[observation.region].push_back(
                    observation.value
                );
            } else if (dimension == "category") {
                groups[observation.category].push_back(
                    observation.value
                );
            } else {
                throw std::invalid_argument(
                    "Unsupported analytical dimension."
                );
            }
        }

        std::map<std::string, double> result;

        for (const auto& [key, values] : groups) {
            result[key] = mean(values);
        }

        return result;
    }

    double linearTrendSlope() const {
        auto data = values();

        if (data.size() < 2) {
            throw std::invalid_argument(
                "Trend requires at least two observations."
            );
        }

        double xMean =
            static_cast<double>(data.size() - 1) / 2.0;
        double yMean = mean(data);

        double numerator = 0.0;
        double denominator = 0.0;

        for (std::size_t index = 0; index < data.size(); ++index) {
            double x = static_cast<double>(index);

            numerator +=
                (x - xMean) * (data[index] - yMean);

            denominator +=
                std::pow(x - xMean, 2);
        }

        return numerator / denominator;
    }

    std::optional<std::string> strongestCategory() const {
        auto categoryMeans = averageBy("category");

        if (categoryMeans.empty()) {
            return std::nullopt;
        }

        auto best = std::max_element(
            categoryMeans.begin(),
            categoryMeans.end(),
            [](const auto& left, const auto& right) {
                return left.second < right.second;
            }
        );

        return best->first;
    }

    void localAnomalies(std::size_t window = 3) const {
        if (window < 2) {
            throw std::invalid_argument(
                "Local anomaly window is too small."
            );
        }

        auto data = values();

        std::cout << "\nLocal anomalies\n";

        for (std::size_t index = 0; index < data.size(); ++index) {
            std::size_t start =
                index > window ? index - window : 0;

            std::size_t end =
                std::min(data.size(), index + window + 1);

            std::vector<double> neighbors;

            for (std::size_t candidate = start;
                 candidate < end;
                 ++candidate) {
                if (candidate != index) {
                    neighbors.push_back(data[candidate]);
                }
            }

            if (neighbors.size() < 2) {
                continue;
            }

            double localMean = mean(neighbors);
            double localStd = standardDeviation(neighbors);

            if (localStd == 0.0) {
                continue;
            }

            double score =
                std::abs(data[index] - localMean) /
                localStd;

            if (score >= 2.5) {
                std::cout
                    << observations[index].day
                    << " value=" << data[index]
                    << " local-z=" << score
                    << '\n';
            }
        }
    }
};

std::vector<PullFreeObservation> buildInspectionData() {
    return {
        {"2026-09-01", 101.0, "North", "Network"},
        {"2026-09-02", 104.0, "North", "Network"},
        {"2026-09-03", 106.0, "North", "Network"},
        {"2026-09-04", 109.0, "North", "Network"},
        {"2026-09-05", 112.0, "North", "Network"},
        {"2026-09-06", 114.0, "North", "Network"},
        {"2026-09-07", 116.0, "North", "Network"},
        {"2026-09-08", 118.0, "North", "Network"},
        {"2026-09-09", 119.0, "North", "Network"},
        {"2026-09-10", 121.0, "North", "Network"},
        {"2026-09-11", 123.0, "North", "Network"},
        {"2026-09-12", 125.0, "North", "Network"},
        {"2026-09-13", 127.0, "North", "Network"},
        {"2026-09-14", 128.0, "North", "Network"},
        {"2026-09-15", 130.0, "North", "Network"},
        {"2026-09-16", 132.0, "North", "Network"},
        {"2026-09-17", 134.0, "North", "Network"},
        {"2026-09-18", 136.0, "North", "Network"},
        {"2026-09-19", 138.0, "North", "Network"},
        {"2026-09-20", 140.0, "North", "Network"},
        {"2026-09-21", 142.0, "North", "Network"},
        {"2026-09-22", 145.0, "North", "Network"},
        {"2026-09-23", 147.0, "North", "Network"},
        {"2026-09-24", 149.0, "North", "Network"},
        {"2026-09-25", 151.0, "North", "Network"},
        {"2026-09-26", 154.0, "North", "Network"},
        {"2026-09-27", 157.0, "North", "Network"},
        {"2026-09-28", 159.0, "North", "Network"},
        {"2026-09-29", 162.0, "North", "Network"},
        {"2026-09-30", 220.0, "North", "Network"},
        {"2026-10-01", 165.0, "South", "Security"},
        {"2026-10-02", 168.0, "South", "Security"},
        {"2026-10-03", 170.0, "South", "Security"},
        {"2026-10-04", 173.0, "South", "Security"},
        {"2026-10-05", 176.0, "South", "Security"},
        {"2026-10-06", 178.0, "South", "Security"},
        {"2026-10-07", 181.0, "South", "Security"},
        {"2026-10-08", 184.0, "South", "Security"},
        {"2026-10-09", 186.0, "South", "Security"},
        {"2026-10-10", 189.0, "South", "Security"},
        {"2026-10-11", 191.0, "South", "Security"},
        {"2026-10-12", 194.0, "South", "Security"},
        {"2026-10-13", 197.0, "South", "Security"},
        {"2026-10-14", 199.0, "South", "Security"},
        {"2026-10-15", 202.0, "South", "Security"},
        {"2026-10-16", 205.0, "South", "Security"},
        {"2026-10-17", 207.0, "South", "Security"},
        {"2026-10-18", 210.0, "South", "Security"},
        {"2026-10-19", 212.0, "South", "Security"},
        {"2026-10-20", 215.0, "South", "Security"},
        {"2026-10-21", 217.0, "South", "Security"},
        {"2026-10-22", 219.0, "South", "Security"},
        {"2026-10-23", 222.0, "South", "Security"},
        {"2026-10-24", 225.0, "South", "Security"},
        {"2026-10-25", 228.0, "South", "Security"},
        {"2026-10-26", 230.0, "South", "Security"},
        {"2026-10-27", 233.0, "South", "Security"},
        {"2026-10-28", 235.0, "South", "Security"},
        {"2026-10-29", 238.0, "South", "Security"},
        {"2026-10-30", 150.0, "South", "Security"},
    };
}

int main() {
    try {
        GovernanceAnalytics analytics(buildInspectionData());

        analytics.validate();
        analytics.describe();

        std::cout << "\nIQR outliers\n";

        for (const auto& [index, value] :
             analytics.detectGlobalOutliers()) {
            std::cout
                << "index=" << index
                << " value=" << value
                << '\n';
        }

        std::cout << "\nRegional pattern\n";

        for (const auto& [region, average] :
             analytics.averageBy("region")) {
            std::cout
                << region
                << " mean=" << average
                << '\n';
        }

        std::cout << "\nCategory pattern\n";

        for (const auto& [category, average] :
             analytics.averageBy("category")) {
            std::cout
                << category
                << " mean=" << average
                << '\n';
        }

        std::cout << "\nTrend slope: "
                  << analytics.linearTrendSlope()
                  << '\n';

        auto strongest = analytics.strongestCategory();

        if (strongest.has_value()) {
            std::cout
                << "Highest-mean category: "
                << *strongest
                << '\n';
        }

        analytics.localAnomalies();

        /*
         * The case study deliberately separates global and local anomalies.
         * A value can be globally unusual because it lies outside the IQR
         * fences, while a local anomaly is detected relative to nearby
         * observations. This distinction prevents a single global threshold
         * from being treated as a universal definition of abnormal behavior.
         */
    } catch (const std::exception& error) {
        std::cerr
            << "EDA failure: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
