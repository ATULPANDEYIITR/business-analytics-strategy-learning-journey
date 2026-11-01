#include <algorithm>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

class Matrix {
public:
    Matrix(std::size_t rows, std::size_t cols)
        : rows_(rows), cols_(cols), data_(rows * cols, 0.0) {
        if (rows == 0 || cols == 0) {
            throw std::invalid_argument("Matrix dimensions must be positive");
        }
    }

    Matrix(std::size_t rows, std::size_t cols, std::vector<double> data)
        : rows_(rows), cols_(cols), data_(std::move(data)) {
        if (rows == 0 || cols == 0) {
            throw std::invalid_argument("Matrix dimensions must be positive");
        }
        if (data_.size() != rows * cols) {
            throw std::invalid_argument("Data size does not match matrix dimensions");
        }
    }

    double& at(std::size_t row, std::size_t col) {
        return data_.at(index(row, col));
    }

    const double& at(std::size_t row, std::size_t col) const {
        return data_.at(index(row, col));
    }

    std::size_t rows() const noexcept {
        return rows_;
    }

    std::size_t cols() const noexcept {
        return cols_;
    }

    std::vector<double> column(std::size_t col) const {
        if (col >= cols_) {
            throw std::out_of_range("Column index out of range");
        }

        std::vector<double> result(rows_);

        for (std::size_t row = 0; row < rows_; ++row) {
            result[row] = at(row, col);
        }

        return result;
    }

    std::vector<double> row(std::size_t rowIndex) const {
        if (rowIndex >= rows_) {
            throw std::out_of_range("Row index out of range");
        }

        std::vector<double> result(cols_);

        for (std::size_t col = 0; col < cols_; ++col) {
            result[col] = at(rowIndex, col);
        }

        return result;
    }

    Matrix broadcastAdd(const std::vector<double>& vector) const {
        if (vector.size() != cols_) {
            throw std::invalid_argument(
                "Broadcast vector size must equal matrix column count"
            );
        }

        Matrix result(rows_, cols_);

        for (std::size_t row = 0; row < rows_; ++row) {
            for (std::size_t col = 0; col < cols_; ++col) {
                result.at(row, col) = at(row, col) + vector[col];
            }
        }

        return result;
    }

    std::vector<double> meanByColumn() const {
        std::vector<double> means(cols_, 0.0);

        for (std::size_t row = 0; row < rows_; ++row) {
            for (std::size_t col = 0; col < cols_; ++col) {
                means[col] += at(row, col);
            }
        }

        for (double& mean : means) {
            mean /= static_cast<double>(rows_);
        }

        return means;
    }

    std::vector<double> minByColumn() const {
        std::vector<double> minimums(cols_, std::numeric_limits<double>::infinity());

        for (std::size_t row = 0; row < rows_; ++row) {
            for (std::size_t col = 0; col < cols_; ++col) {
                minimums[col] = std::min(minimums[col], at(row, col));
            }
        }

        return minimums;
    }

    std::vector<double> maxByColumn() const {
        std::vector<double> maximums(
            cols_, -std::numeric_limits<double>::infinity()
        );

        for (std::size_t row = 0; row < rows_; ++row) {
            for (std::size_t col = 0; col < cols_; ++col) {
                maximums[col] = std::max(maximums[col], at(row, col));
            }
        }

        return maximums;
    }

    Matrix normalizeColumns() const {
        const auto minimums = minByColumn();
        const auto maximums = maxByColumn();

        Matrix result(rows_, cols_);

        for (std::size_t row = 0; row < rows_; ++row) {
            for (std::size_t col = 0; col < cols_; ++col) {
                const double range = maximums[col] - minimums[col];

                result.at(row, col) =
                    range == 0.0
                        ? 0.0
                        : (at(row, col) - minimums[col]) / range;
            }
        }

        return result;
    }

private:
    std::size_t index(std::size_t row, std::size_t col) const {
        if (row >= rows_ || col >= cols_) {
            throw std::out_of_range("Matrix index out of range");
        }
        return row * cols_ + col;
    }

    std::size_t rows_;
    std::size_t cols_;
    std::vector<double> data_;
};

class NumericalAnalyticsEngine {
public:
    explicit NumericalAnalyticsEngine(Matrix measurements)
        : measurements_(std::move(measurements)) {}

    std::vector<double> weightedScores(
        const std::vector<double>& weights
    ) const {
        if (weights.size() != measurements_.cols()) {
            throw std::invalid_argument("Weight count must match feature count");
        }

        Matrix normalized = measurements_.normalizeColumns();
        std::vector<double> scores(measurements_.rows(), 0.0);

        for (std::size_t row = 0; row < measurements_.rows(); ++row) {
            for (std::size_t col = 0; col < measurements_.cols(); ++col) {
                scores[row] += normalized.at(row, col) * weights[col];
            }
        }

        return scores;
    }

    std::vector<bool> detectAnomalies(double threshold) const {
        if (threshold <= 0.0 || !std::isfinite(threshold)) {
            throw std::invalid_argument("Threshold must be finite and positive");
        }

        const auto means = measurements_.meanByColumn();
        std::vector<double> deviations(measurements_.cols(), 0.0);

        for (std::size_t col = 0; col < measurements_.cols(); ++col) {
            double squared = 0.0;

            for (std::size_t row = 0; row < measurements_.rows(); ++row) {
                const double difference =
                    measurements_.at(row, col) - means[col];
                squared += difference * difference;
            }

            deviations[col] = std::sqrt(
                squared / static_cast<double>(measurements_.rows())
            );
        }

        std::vector<bool> result(measurements_.rows(), false);

        for (std::size_t row = 0; row < measurements_.rows(); ++row) {
            for (std::size_t col = 0; col < measurements_.cols(); ++col) {
                const double safeDeviation =
                    deviations[col] == 0.0 ? 1.0 : deviations[col];

                const double z =
                    (measurements_.at(row, col) - means[col]) /
                    safeDeviation;

                if (std::abs(z) >= threshold) {
                    result[row] = true;
                    break;
                }
            }
        }

        return result;
    }

private:
    Matrix measurements_;
};

void printVector(const std::vector<double>& values) {
    std::cout << "[";

    for (std::size_t i = 0; i < values.size(); ++i) {
        std::cout << std::fixed << std::setprecision(4) << values[i];
        if (i + 1 < values.size()) {
            std::cout << ", ";
        }
    }

    std::cout << "]\n";
}

void demonstrateMatrixOperations(const Matrix& matrix) {
    std::cout << "=== Matrix dimensions ===\n";
    std::cout << "Rows: " << matrix.rows()
              << " Columns: " << matrix.cols() << "\n";

    std::cout << "\n=== First row ===\n";
    printVector(matrix.row(0));

    std::cout << "\n=== Temperature column ===\n";
    printVector(matrix.column(0));

    std::cout << "\n=== Column means ===\n";
    printVector(matrix.meanByColumn());

    std::cout << "\n=== Column minima ===\n";
    printVector(matrix.minByColumn());

    std::cout << "\n=== Column maxima ===\n";
    printVector(matrix.maxByColumn());

    std::cout << "\n=== Broadcasting ===\n";
    Matrix adjusted = matrix.broadcastAdd({1.0, -2.0, 0.5, 0.0});
    printVector(adjusted.row(0));
}

void demonstrateRandomSampling() {
    std::cout << "\n=== Random sampling ===\n";

    std::mt19937 generator(20261101);
    std::normal_distribution<double> distribution(100.0, 15.0);

    std::vector<double> samples(10);

    std::generate(
        samples.begin(),
        samples.end(),
        [&]() { return distribution(generator); }
    );

    printVector(samples);
}

int main() {
    try {
        Matrix measurements(
            8,
            4,
            {
                22.4, 45.0, 1012.3, 0.12,
                23.1, 46.5, 1011.8, 0.15,
                24.8, 49.2, 1010.4, 0.18,
                26.7, 54.0, 1008.9, 0.31,
                28.4, 58.1, 1007.5, 0.42,
                29.1, 61.0, 1006.2, 0.55,
                27.8, 57.3, 1007.1, 0.38,
                25.6, 51.4, 1009.2, 0.22
            }
        );

        demonstrateMatrixOperations(measurements);

        NumericalAnalyticsEngine engine(measurements);

        std::cout << "\n=== Anomaly detection ===\n";
        const auto anomalies = engine.detectAnomalies(2.0);

        for (std::size_t i = 0; i < anomalies.size(); ++i) {
            std::cout << "Record " << i + 1
                      << ": " << (anomalies[i] ? "ANOMALY" : "NORMAL")
                      << "\n";
        }

        std::cout << "\n=== Weighted normalized scoring ===\n";
        const std::vector<double> weights{0.35, 0.20, 0.25, 0.20};
        const auto scores = engine.weightedScores(weights);
        printVector(scores);

        std::cout << "\n=== Highest scoring record ===\n";
        const auto maximum = std::max_element(scores.begin(), scores.end());
        const auto maximumIndex =
            static_cast<std::size_t>(std::distance(scores.begin(), maximum));

        std::cout << "Record: " << maximumIndex + 1
                  << " Score: " << std::fixed << std::setprecision(4)
                  << *maximum << "\n";

        demonstrateRandomSampling();

        std::cout << "\n=== Edge-case validation ===\n";

        Matrix constant(3, 2, {5.0, 5.0, 5.0, 5.0, 5.0, 5.0});
        Matrix normalizedConstant = constant.normalizeColumns();

        for (std::size_t row = 0; row < normalizedConstant.rows(); ++row) {
            for (std::size_t col = 0; col < normalizedConstant.cols(); ++col) {
                assert(normalizedConstant.at(row, col) == 0.0);
            }
        }

        std::cout << "Zero-range normalization handled safely.\n";

        try {
            measurements.at(100, 0);
        } catch (const std::out_of_range& error) {
            std::cout << "Invalid indexing rejected: "
                      << error.what() << "\n";
        }

        try {
            engine.weightedScores({1.0, 2.0});
        } catch (const std::invalid_argument& error) {
            std::cout << "Invalid weights rejected: "
                      << error.what() << "\n";
        }

        std::cout << "\nNumerical computing workflow completed successfully.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal numerical processing error: "
                  << error.what() << "\n";
        return 1;
    }
}
