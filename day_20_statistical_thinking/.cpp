// File: cpp/statistical_decision.cpp

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

struct Summary {
    double mean;
    double median;
    double minimum;
    double maximum;
    double population_stddev;
};

double mean(const std::vector<double>& values) {
    if (values.empty()) {
        throw std::invalid_argument("The dataset cannot be empty.");
    }

    return std::accumulate(values.begin(), values.end(), 0.0) / values.size();
}

double median(std::vector<double> values) {
    if (values.empty()) {
        throw std::invalid_argument("The dataset cannot be empty.");
    }

    std::sort(values.begin(), values.end());

    const std::size_t middle = values.size() / 2;

    if (values.size() % 2 == 0) {
        return (values[middle - 1] + values[middle]) / 2.0;
    }

    return values[middle];
}

double population_standard_deviation(const std::vector<double>& values) {
    const double average = mean(values);

    double squared_difference_sum = 0.0;

    for (double value : values) {
        const double difference = value - average;
        squared_difference_sum += difference * difference;
    }

    return std::sqrt(squared_difference_sum / values.size());
}

Summary summarize(const std::vector<double>& values) {
    if (values.empty()) {
        throw std::invalid_argument("The dataset cannot be empty.");
    }

    const auto [minimum, maximum] =
        std::minmax_element(values.begin(), values.end());

    return {
        mean(values),
        median(values),
        *minimum,
        *maximum,
        population_standard_deviation(values)
    };
}

double covariance(
    const std::vector<double>& x,
    const std::vector<double>& y
) {
    if (x.size() != y.size() || x.size() < 2) {
        throw std::invalid_argument(
            "Covariance requires equally sized datasets with at least two observations."
        );
    }

    const double x_mean = mean(x);
    const double y_mean = mean(y);

    double total = 0.0;

    for (std::size_t i = 0; i < x.size(); ++i) {
        total += (x[i] - x_mean) * (y[i] - y_mean);
    }

    return total / static_cast<double>(x.size() - 1);
}

double correlation(
    const std::vector<double>& x,
    const std::vector<double>& y
) {
    if (x.size() != y.size() || x.size() < 2) {
        throw std::invalid_argument("Correlation requires equal datasets.");
    }

    const double x_sd = population_standard_deviation(x);
    const double y_sd = population_standard_deviation(y);

    if (x_sd == 0.0 || y_sd == 0.0) {
        throw std::invalid_argument(
            "Correlation is undefined when either variable has zero variation."
        );
    }

    return covariance(x, y) /
           (x_sd * y_sd) *
           static_cast<double>(x.size()) /
           static_cast<double>(x.size() - 1);
}

int main() {
    try {
        // Example business data: weekly revenue observations in thousands.
        const std::vector<double> revenue{
            120, 135, 128, 142, 155, 149, 131, 160
        };

        const Summary result = summarize(revenue);

        std::cout << std::fixed << std::setprecision(2);
        std::cout << "Business revenue statistics\n";
        std::cout << "Mean: " << result.mean << '\n';
        std::cout << "Median: " << result.median << '\n';
        std::cout << "Minimum: " << result.minimum << '\n';
        std::cout << "Maximum: " << result.maximum << '\n';
        std::cout << "Population standard deviation: "
                  << result.population_stddev << '\n';

        // Correlation is descriptive: it does not prove that one variable
        // caused the other to change.
        const std::vector<double> marketing_spend{
            10, 12, 11, 14, 16, 15, 12, 17
        };

        std::cout << "Marketing/revenue correlation: "
                  << correlation(marketing_spend, revenue) << '\n';

    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
