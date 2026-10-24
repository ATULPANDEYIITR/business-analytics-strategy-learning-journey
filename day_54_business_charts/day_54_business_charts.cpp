#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

enum class ChartType {
    Bar,
    Line,
    Scatter,
    Histogram,
    Box
};

struct SalesRecord {
    std::string month;
    std::string region;
    double revenue;
    int orders;
    double marketingSpend;
    double deliveryDays;
};

struct StatusCheck {
    std::string name;
    bool passed;
};

struct ChartPolicy {
    bool requirePositiveValues;
    bool requireMultipleObservations;
    std::size_t minimumObservations;
};

class GovernanceError : public std::runtime_error {
public:
    explicit GovernanceError(const std::string& message)
        : std::runtime_error(message) {}
};

class BusinessChartEngine {
private:
    std::vector<SalesRecord> records;

    static void validateRecord(const SalesRecord& record) {
        if (record.month.empty() || record.region.empty()) {
            throw GovernanceError("Month and region are required.");
        }

        if (record.revenue < 0.0 ||
            record.orders < 0 ||
            record.marketingSpend < 0.0 ||
            record.deliveryDays < 0.0) {
            throw GovernanceError(
                "Business measures cannot contain negative values."
            );
        }
    }

    static double percentile(
        std::vector<double> sorted,
        double fraction
    ) {
        if (sorted.empty()) {
            throw GovernanceError("Percentile requires observations.");
        }

        std::sort(sorted.begin(), sorted.end());

        const double position =
            (sorted.size() - 1) * fraction;

        const std::size_t lower =
            static_cast<std::size_t>(std::floor(position));

        const std::size_t upper =
            static_cast<std::size_t>(std::ceil(position));

        if (lower == upper) {
            return sorted[lower];
        }

        const double weight = position - lower;

        return sorted[lower] * (1.0 - weight)
             + sorted[upper] * weight;
    }

public:
    explicit BusinessChartEngine(std::vector<SalesRecord> input)
        : records(std::move(input)) {
        if (records.empty()) {
            throw GovernanceError("Chart engine requires records.");
        }

        for (const auto& record : records) {
            validateRecord(record);
        }
    }

    std::map<std::string, double> revenueByRegion() const {
        std::map<std::string, double> totals;

        for (const auto& record : records) {
            totals[record.region] += record.revenue;
        }

        return totals;
    }

    std::map<std::string, double> revenueByMonth() const {
        std::map<std::string, double> totals;

        for (const auto& record : records) {
            totals[record.month] += record.revenue;
        }

        return totals;
    }

    double correlation() const {
        if (records.size() < 2) {
            throw GovernanceError(
                "Scatter analysis requires at least two observations."
            );
        }

        const double xMean =
            std::accumulate(
                records.begin(),
                records.end(),
                0.0,
                [](double sum, const SalesRecord& record) {
                    return sum + record.marketingSpend;
                }
            ) / records.size();

        const double yMean =
            std::accumulate(
                records.begin(),
                records.end(),
                0.0,
                [](double sum, const SalesRecord& record) {
                    return sum + record.revenue;
                }
            ) / records.size();

        double numerator = 0.0;
        double xVariance = 0.0;
        double yVariance = 0.0;

        for (const auto& record : records) {
            const double dx = record.marketingSpend - xMean;
            const double dy = record.revenue - yMean;

            numerator += dx * dy;
            xVariance += dx * dx;
            yVariance += dy * dy;
        }

        const double denominator =
            std::sqrt(xVariance * yVariance);

        if (denominator == 0.0) {
            throw GovernanceError(
                "Scatter correlation is undefined for zero variance."
            );
        }

        return numerator / denominator;
    }

    std::vector<int> histogram(double binWidth) const {
        if (binWidth <= 0.0) {
            throw GovernanceError(
                "Histogram bin width must be positive."
            );
        }

        std::vector<double> values;
        values.reserve(records.size());

        for (const auto& record : records) {
            values.push_back(record.revenue);
        }

        const auto [minimumIt, maximumIt] =
            std::minmax_element(values.begin(), values.end());

        const double minimum = *minimumIt;
        const double maximum = *maximumIt;

        const std::size_t binCount =
            minimum == maximum
                ? 1
                : static_cast<std::size_t>(
                    std::floor((maximum - minimum) / binWidth)
                ) + 1;

        std::vector<int> counts(binCount, 0);

        for (double value : values) {
            std::size_t index =
                static_cast<std::size_t>(
                    std::floor((value - minimum) / binWidth)
                );

            if (index >= counts.size()) {
                index = counts.size() - 1;
            }

            ++counts[index];
        }

        return counts;
    }

    void printBoxStatistics() const {
        std::vector<double> values;

        for (const auto& record : records) {
            values.push_back(record.deliveryDays);
        }

        const double q1 = percentile(values, 0.25);
        const double median = percentile(values, 0.50);
        const double q3 = percentile(values, 0.75);
        const double iqr = q3 - q1;

        const double lowerFence = q1 - 1.5 * iqr;
        const double upperFence = q3 + 1.5 * iqr;

        std::vector<double> regular;
        std::vector<double> outliers;

        for (double value : values) {
            if (value < lowerFence || value > upperFence) {
                outliers.push_back(value);
            } else {
                regular.push_back(value);
            }
        }

        const auto [minimumIt, maximumIt] =
            std::minmax_element(
                regular.begin(),
                regular.end()
            );

        std::cout << "\nBOX PLOT - DELIVERY DAYS\n"
                  << "Minimum : " << *minimumIt << '\n'
                  << "Q1      : " << q1 << '\n'
                  << "Median  : " << median << '\n'
                  << "Q3      : " << q3 << '\n'
                  << "Maximum : " << *maximumIt << '\n'
                  << "Outliers:";

        for (double value : outliers) {
            std::cout << ' ' << value;
        }

        std::cout << '\n';
    }

    static std::string chartName(ChartType type) {
        switch (type) {
            case ChartType::Bar: return "bar";
            case ChartType::Line: return "line";
            case ChartType::Scatter: return "scatter";
            case ChartType::Histogram: return "histogram";
            case ChartType::Box: return "box";
        }

        throw GovernanceError("Unknown chart type.");
    }

    static ChartPolicy policyFor(ChartType type) {
        switch (type) {
            case ChartType::Bar:
                return {true, false, 1};
            case ChartType::Line:
                return {false, true, 2};
            case ChartType::Scatter:
                return {false, true, 2};
            case ChartType::Histogram:
                return {false, true, 2};
            case ChartType::Box:
                return {false, true, 5};
        }

        throw GovernanceError("Unknown chart policy.");
    }

    bool eligible(ChartType type) const {
        const ChartPolicy policy = policyFor(type);

        if (records.size() < policy.minimumObservations) {
            return false;
        }

        if (policy.requirePositiveValues) {
            const bool positive = std::any_of(
                records.begin(),
                records.end(),
                [](const SalesRecord& record) {
                    return record.revenue > 0.0;
                }
            );

            if (!positive) {
                return false;
            }
        }

        return true;
    }

    void printBarChart() const {
        const auto totals = revenueByRegion();

        const double maximum = std::max_element(
            totals.begin(),
            totals.end(),
            [](const auto& left, const auto& right) {
                return left.second < right.second;
            }
        )->second;

        std::cout << "BAR CHART - REVENUE BY REGION\n";

        for (const auto& [region, value] : totals) {
            const int width = static_cast<int>(
                std::round((value / maximum) * 45.0)
            );

            std::cout << std::setw(8)
                      << region
                      << " | "
                      << std::string(width, '#')
                      << " "
                      << std::fixed
                      << std::setprecision(0)
                      << value
                      << '\n';
        }
    }

    void printLineData() const {
        std::cout << "\nLINE CHART - MONTHLY REVENUE\n";

        for (const auto& [month, revenue] : revenueByMonth()) {
            std::cout << month
                      << " -> "
                      << std::fixed
                      << std::setprecision(0)
                      << revenue
                      << '\n';
        }
    }
};

int main() {
    try {
        const std::vector<SalesRecord> records = {
            {"2026-01", "North", 72000, 410, 11000, 3.2},
            {"2026-01", "South", 64000, 390, 9500, 4.1},
            {"2026-01", "West", 81000, 450, 12500, 2.8},
            {"2026-02", "North", 76000, 425, 11500, 3.4},
            {"2026-02", "South", 68000, 402, 10200, 4.0},
            {"2026-02", "West", 87000, 478, 13100, 2.6},
            {"2026-03", "North", 83000, 440, 12000, 3.6},
            {"2026-03", "South", 70000, 410, 10500, 4.4},
            {"2026-03", "West", 92000, 495, 13800, 2.9},
            {"2026-04", "North", 88000, 462, 12700, 3.5},
            {"2026-04", "South", 73000, 421, 10800, 4.2},
            {"2026-04", "West", 97000, 510, 14500, 2.7},
            {"2026-05", "North", 91000, 475, 13000, 3.8},
            {"2026-05", "South", 76000, 430, 11100, 4.5},
            {"2026-05", "West", 103000, 535, 15100, 2.5},
            {"2026-06", "North", 96000, 490, 13600, 3.7},
            {"2026-06", "South", 79000, 442, 11400, 4.3},
            {"2026-06", "West", 108000, 552, 15700, 2.8},
            {"2026-06", "West", 155000, 600, 22000, 9.5}
        };

        BusinessChartEngine engine(records);

        std::cout << "BUSINESS CHART ANALYSIS ENGINE\n\n";

        engine.printBarChart();
        engine.printLineData();

        std::cout << "\nSCATTER ANALYSIS\n"
                  << "Marketing spend vs revenue correlation: "
                  << std::fixed
                  << std::setprecision(3)
                  << engine.correlation()
                  << '\n';

        const auto histogram = engine.histogram(20000.0);

        std::cout << "\nHISTOGRAM - REVENUE DISTRIBUTION\n";
        for (std::size_t i = 0; i < histogram.size(); ++i) {
            std::cout << "Bin " << i + 1
                      << " | "
                      << std::string(histogram[i], '*')
                      << " "
                      << histogram[i]
                      << '\n';
        }

        engine.printBoxStatistics();

        std::cout << "\nCHART ELIGIBILITY\n";

        for (const ChartType type : {
            ChartType::Bar,
            ChartType::Line,
            ChartType::Scatter,
            ChartType::Histogram,
            ChartType::Box
        }) {
            std::cout << std::setw(10)
                      << BusinessChartEngine::chartName(type)
                      << " : "
                      << (engine.eligible(type) ? "eligible" : "rejected")
                      << '\n';
        }

        return 0;
    }
    catch (const GovernanceError& error) {
        std::cerr << "Validation failure: "
                  << error.what()
                  << '\n';
        return 2;
    }
    catch (const std::exception& error) {
        std::cerr << "Unexpected failure: "
                  << error.what()
                  << '\n';
        return 1;
    }
}
