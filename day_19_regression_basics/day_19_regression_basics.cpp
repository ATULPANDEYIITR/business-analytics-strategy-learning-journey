#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

/*
 * Regression Basics: Industry-Style Property Price Prediction
 *
 * C++17 case study.
 *
 * The system models a simplified property valuation service.
 *
 * It demonstrates:
 *   - observations and features
 *   - data validation
 *   - ordinary least squares
 *   - matrix operations
 *   - train/test evaluation
 *   - prediction
 *   - residual analysis
 *   - MAE, MSE, RMSE and R²
 *   - feature scaling
 *   - polynomial features
 *   - ridge regularization
 *   - batch processing
 *   - edge cases
 *   - computational complexity
 *
 * The implementation deliberately uses the standard library so that
 * the mathematical mechanism remains visible.
 */

using Vector = std::vector<double>;
using Matrix = std::vector<Vector>;


// ============================================================
// BASIC STATISTICS
// ============================================================

double mean(const Vector& values) {
    if (values.empty()) {
        throw std::invalid_argument(
            "Cannot calculate mean of an empty vector."
        );
    }

    return std::accumulate(
        values.begin(),
        values.end(),
        0.0
    ) / static_cast<double>(values.size());
}

double meanSquaredError(
    const Vector& actual,
    const Vector& predicted
) {
    if (actual.size() != predicted.size() || actual.empty()) {
        throw std::invalid_argument(
            "MSE requires equal non-empty vectors."
        );
    }

    double total = 0.0;

    for (std::size_t i = 0; i < actual.size(); ++i) {
        const double error =
            actual[i] - predicted[i];

        total += error * error;
    }

    return total /
        static_cast<double>(actual.size());
}

double meanAbsoluteError(
    const Vector& actual,
    const Vector& predicted
) {
    if (actual.size() != predicted.size() || actual.empty()) {
        throw std::invalid_argument(
            "MAE requires equal non-empty vectors."
        );
    }

    double total = 0.0;

    for (std::size_t i = 0; i < actual.size(); ++i) {
        total += std::abs(
            actual[i] - predicted[i]
        );
    }

    return total /
        static_cast<double>(actual.size());
}

double rootMeanSquaredError(
    const Vector& actual,
    const Vector& predicted
) {
    return std::sqrt(
        meanSquaredError(actual, predicted)
    );
}

double rSquared(
    const Vector& actual,
    const Vector& predicted
) {
    if (actual.size() != predicted.size() ||
        actual.empty()) {
        throw std::invalid_argument(
            "R² requires equal non-empty vectors."
        );
    }

    const double targetMean = mean(actual);

    double totalSumOfSquares = 0.0;
    double residualSumOfSquares = 0.0;

    for (std::size_t i = 0; i < actual.size(); ++i) {
        const double totalDifference =
            actual[i] - targetMean;

        const double residual =
            actual[i] - predicted[i];

        totalSumOfSquares +=
            totalDifference * totalDifference;

        residualSumOfSquares +=
            residual * residual;
    }

    if (totalSumOfSquares == 0.0) {
        throw std::invalid_argument(
            "R² is undefined for a constant target."
        );
    }

    return 1.0 -
        residualSumOfSquares /
        totalSumOfSquares;
}


// ============================================================
// MATRIX OPERATIONS
// ============================================================

void validateMatrix(const Matrix& matrix) {
    if (matrix.empty()) {
        throw std::invalid_argument(
            "Matrix cannot be empty."
        );
    }

    const std::size_t columns =
        matrix.front().size();

    if (columns == 0) {
        throw std::invalid_argument(
            "Matrix cannot have zero columns."
        );
    }

    for (const auto& row : matrix) {
        if (row.size() != columns) {
            throw std::invalid_argument(
                "Matrix rows have inconsistent sizes."
            );
        }
    }
}

Matrix transpose(const Matrix& matrix) {
    validateMatrix(matrix);

    Matrix result(
        matrix.front().size(),
        Vector(matrix.size(), 0.0)
    );

    for (std::size_t row = 0;
         row < matrix.size();
         ++row) {
        for (std::size_t column = 0;
             column < matrix[row].size();
             ++column) {
            result[column][row] =
                matrix[row][column];
        }
    }

    return result;
}

Matrix multiply(
    const Matrix& a,
    const Matrix& b
) {
    validateMatrix(a);
    validateMatrix(b);

    if (a.front().size() != b.size()) {
        throw std::invalid_argument(
            "Incompatible matrix dimensions."
        );
    }

    Matrix result(
        a.size(),
        Vector(b.front().size(), 0.0)
    );

    for (std::size_t i = 0;
         i < a.size();
         ++i) {
        for (std::size_t k = 0;
             k < b.size();
             ++k) {
            for (std::size_t j = 0;
                 j < b.front().size();
                 ++j) {
                result[i][j] +=
                    a[i][k] * b[k][j];
            }
        }
    }

    return result;
}

Matrix identityMatrix(std::size_t size) {
    Matrix result(
        size,
        Vector(size, 0.0)
    );

    for (std::size_t i = 0; i < size; ++i) {
        result[i][i] = 1.0;
    }

    return result;
}


// ============================================================
// GAUSS-JORDAN INVERSION
// ============================================================

Matrix inverse(Matrix matrix) {
    validateMatrix(matrix);

    const std::size_t n = matrix.size();

    if (matrix.front().size() != n) {
        throw std::invalid_argument(
            "Only square matrices can be inverted."
        );
    }

    Matrix identity =
        identityMatrix(n);

    Matrix augmented(n);

    for (std::size_t row = 0;
         row < n;
         ++row) {
        augmented[row] = matrix[row];

        augmented[row].insert(
            augmented[row].end(),
            identity[row].begin(),
            identity[row].end()
        );
    }

    for (std::size_t column = 0;
         column < n;
         ++column) {

        // Partial pivoting improves numerical stability.
        std::size_t pivotRow = column;

        for (std::size_t row = column + 1;
             row < n;
             ++row) {
            if (
                std::abs(
                    augmented[row][column]
                ) >
                std::abs(
                    augmented[pivotRow][column]
                )
            ) {
                pivotRow = row;
            }
        }

        if (
            std::abs(
                augmented[pivotRow][column]
            ) < 1e-12
        ) {
            throw std::runtime_error(
                "Matrix is singular or numerically unstable."
            );
        }

        std::swap(
            augmented[column],
            augmented[pivotRow]
        );

        const double pivot =
            augmented[column][column];

        for (double& value : augmented[column]) {
            value /= pivot;
        }

        for (std::size_t row = 0;
             row < n;
             ++row) {
            if (row == column) {
                continue;
            }

            const double factor =
                augmented[row][column];

            for (std::size_t j = 0;
                 j < 2 * n;
                 ++j) {
                augmented[row][j] -=
                    factor * augmented[column][j];
            }
        }
    }

    Matrix result(
        n,
        Vector(n, 0.0)
    );

    for (std::size_t row = 0;
         row < n;
         ++row) {
        for (std::size_t column = 0;
             column < n;
             ++column) {
            result[row][column] =
                augmented[row][column + n];
        }
    }

    return result;
}


// ============================================================
// REGRESSION DATASET
// ============================================================

struct Property {
    double area;
    double bedrooms;
    double age;
    double distanceToCenter;
    double price;
};

void validateProperty(const Property& property) {
    const double values[] = {
        property.area,
        property.bedrooms,
        property.age,
        property.distanceToCenter,
        property.price
    };

    for (double value : values) {
        if (!std::isfinite(value)) {
            throw std::invalid_argument(
                "Property contains a non-finite value."
            );
        }
    }

    if (property.area <= 0.0) {
        throw std::invalid_argument(
            "Property area must be positive."
        );
    }

    if (property.bedrooms <= 0.0) {
        throw std::invalid_argument(
            "Bedroom count must be positive."
        );
    }

    if (property.age < 0.0) {
        throw std::invalid_argument(
            "Property age cannot be negative."
        );
    }

    if (property.distanceToCenter < 0.0) {
        throw std::invalid_argument(
            "Distance cannot be negative."
        );
    }

    if (property.price <= 0.0) {
        throw std::invalid_argument(
            "Price must be positive."
        );
    }
}


// ============================================================
// DESIGN MATRIX
// ============================================================

Matrix buildDesignMatrix(
    const std::vector<Property>& properties
) {
    if (properties.empty()) {
        throw std::invalid_argument(
            "Cannot build a design matrix from empty data."
        );
    }

    Matrix design;

    for (const auto& property : properties) {
        validateProperty(property);

        /*
         * The first column is the intercept.
         *
         * Features:
         *   x1 = area
         *   x2 = bedrooms
         *   x3 = age
         *   x4 = distance to city center
         */
        design.push_back({
            1.0,
            property.area,
            property.bedrooms,
            property.age,
            property.distanceToCenter
        });
    }

    return design;
}

Vector extractTarget(
    const std::vector<Property>& properties
) {
    Vector target;

    for (const auto& property : properties) {
        validateProperty(property);
        target.push_back(property.price);
    }

    return target;
}


// ============================================================
// REGRESSION MODEL
// ============================================================

class LinearRegressionModel {
private:
    Vector coefficients_;

public:
    explicit LinearRegressionModel(
        Vector coefficients
    )
        : coefficients_(std::move(coefficients)) {

        if (coefficients_.empty()) {
            throw std::invalid_argument(
                "Model must have at least one coefficient."
            );
        }
    }

    double predict(
        const Property& property
    ) const {
        validateProperty(property);

        if (coefficients_.size() != 5) {
            throw std::runtime_error(
                "This model expects four property features."
            );
        }

        return
            coefficients_[0] +
            coefficients_[1] * property.area +
            coefficients_[2] * property.bedrooms +
            coefficients_[3] * property.age +
            coefficients_[4] * property.distanceToCenter;
    }

    Vector predict(
        const std::vector<Property>& properties
    ) const {
        Vector predictions;

        predictions.reserve(properties.size());

        for (const auto& property : properties) {
            predictions.push_back(
                predict(property)
            );
        }

        return predictions;
    }

    const Vector& coefficients() const {
        return coefficients_;
    }

    void printEquation() const {
        std::cout
            << "price_hat = "
            << coefficients_[0]
            << " + "
            << coefficients_[1]
            << "*area + "
            << coefficients_[2]
            << "*bedrooms + "
            << coefficients_[3]
            << "*age + "
            << coefficients_[4]
            << "*distance\n";
    }
};


// ============================================================
// ORDINARY LEAST SQUARES
// ============================================================

LinearRegressionModel fitOLS(
    const std::vector<Property>& properties
) {
    Matrix x =
        buildDesignMatrix(properties);

    Vector y =
        extractTarget(properties);

    Matrix xt =
        transpose(x);

    Matrix xtx =
        multiply(xt, x);

    Matrix xty =
        multiply(
            xt,
            Matrix{
                y
            }
        );

    /*
     * Matrix{y} above creates one row containing y, while the
     * normal equation needs a column vector.
     *
     * Convert it explicitly.
     */
    Matrix yColumn(
        y.size(),
        Vector(1)
    );

    for (std::size_t i = 0;
         i < y.size();
         ++i) {
        yColumn[i][0] = y[i];
    }

    xty = multiply(
        xt,
        yColumn
    );

    /*
     * Educational normal equation:
     *
     * beta = (X'X)^(-1) X'y
     *
     * Production numerical systems generally prefer QR or SVD
     * decomposition rather than explicitly computing an inverse.
     */
    Matrix xtxInverse =
        inverse(xtx);

    Matrix beta =
        multiply(
            xtxInverse,
            xty
        );

    Vector coefficients;

    for (const auto& row : beta) {
        coefficients.push_back(row[0]);
    }

    return LinearRegressionModel(
        std::move(coefficients)
    );
}


// ============================================================
// RIDGE REGRESSION
// ============================================================

LinearRegressionModel fitRidge(
    const std::vector<Property>& properties,
    double lambda
) {
    if (lambda < 0.0) {
        throw std::invalid_argument(
            "Ridge lambda cannot be negative."
        );
    }

    Matrix x =
        buildDesignMatrix(properties);

    Vector y =
        extractTarget(properties);

    Matrix xt =
        transpose(x);

    Matrix xtx =
        multiply(xt, x);

    Matrix penalty =
        identityMatrix(xtx.size());

    // The intercept is not penalized.
    penalty[0][0] = 0.0;

    for (std::size_t i = 0;
         i < xtx.size();
         ++i) {
        for (std::size_t j = 0;
             j < xtx.size();
             ++j) {
            xtx[i][j] +=
                lambda * penalty[i][j];
        }
    }

    Matrix yColumn(
        y.size(),
        Vector(1)
    );

    for (std::size_t i = 0;
         i < y.size();
         ++i) {
        yColumn[i][0] = y[i];
    }

    Matrix xty =
        multiply(
            xt,
            yColumn
        );

    Matrix beta =
        multiply(
            inverse(xtx),
            xty
        );

    Vector coefficients;

    for (const auto& row : beta) {
        coefficients.push_back(row[0]);
    }

    return LinearRegressionModel(
        std::move(coefficients)
    );
}


// ============================================================
// DATASET SPLITTING
// ============================================================

struct DatasetSplit {
    std::vector<Property> training;
    std::vector<Property> testing;
};

DatasetSplit splitDataset(
    const std::vector<Property>& data,
    double testRatio,
    unsigned int seed
) {
    if (data.size() < 2) {
        throw std::invalid_argument(
            "At least two observations are required."
        );
    }

    if (!(testRatio > 0.0 &&
          testRatio < 1.0)) {
        throw std::invalid_argument(
            "testRatio must be between 0 and 1."
        );
    }

    std::vector<Property> shuffled =
        data;

    std::mt19937 generator(seed);

    std::shuffle(
        shuffled.begin(),
        shuffled.end(),
        generator
    );

    const std::size_t testSize =
        std::max<std::size_t>(
            1,
            static_cast<std::size_t>(
                std::round(
                    shuffled.size() * testRatio
                )
            )
        );

    DatasetSplit split;

    split.testing.assign(
        shuffled.begin(),
        shuffled.begin() + testSize
    );

    split.training.assign(
        shuffled.begin() + testSize,
        shuffled.end()
    );

    return split;
}


// ============================================================
// MODEL EVALUATION
// ============================================================

struct Metrics {
    double mae;
    double mse;
    double rmse;
    double r2;
};

Metrics evaluate(
    const LinearRegressionModel& model,
    const std::vector<Property>& data
) {
    const Vector actual =
        extractTarget(data);

    const Vector predicted =
        model.predict(data);

    return {
        meanAbsoluteError(
            actual,
            predicted
        ),
        meanSquaredError(
            actual,
            predicted
        ),
        rootMeanSquaredError(
            actual,
            predicted
        ),
        rSquared(
            actual,
            predicted
        )
    };
}

void printMetrics(
    const std::string& label,
    const Metrics& metrics
) {
    std::cout
        << "\n"
        << label
        << "\n"
        << "MAE  : "
        << metrics.mae
        << "\n"
        << "MSE  : "
        << metrics.mse
        << "\n"
        << "RMSE : "
        << metrics.rmse
        << "\n"
        << "R2   : "
        << metrics.r2
        << "\n";
}


// ============================================================
// RESIDUAL REPORT
// ============================================================

void printResidualReport(
    const LinearRegressionModel& model,
    const std::vector<Property>& properties
) {
    const Vector actual =
        extractTarget(properties);

    const Vector predicted =
        model.predict(properties);

    std::cout
        << "\nResidual analysis\n";

    std::cout
        << std::left
        << std::setw(10)
        << "Actual"
        << std::setw(14)
        << "Predicted"
        << std::setw(14)
        << "Residual"
        << "\n";

    for (std::size_t i = 0;
         i < actual.size();
         ++i) {

        const double residual =
            actual[i] - predicted[i];

        std::cout
            << std::left
            << std::setw(10)
            << actual[i]
            << std::setw(14)
            << predicted[i]
            << std::setw(14)
            << residual
            << "\n";
    }
}


// ============================================================
// POLYNOMIAL FEATURE CASE
// ============================================================

Matrix createPolynomialAreaFeatures(
    const std::vector<Property>& properties
) {
    /*
     * Polynomial regression can represent curvature.
     *
     * Here we augment the feature space with area².
     *
     * The model is still linear in its coefficients:
     *
     * y = b0 + b1*area + b2*area² + ...
     */
    Matrix features;

    for (const auto& property : properties) {
        validateProperty(property);

        features.push_back({
            1.0,
            property.area,
            property.area * property.area,
            property.bedrooms,
            property.age,
            property.distanceToCenter
        });
    }

    return features;
}

Vector fitPolynomialAreaModel(
    const std::vector<Property>& properties
) {
    Matrix x =
        createPolynomialAreaFeatures(
            properties
        );

    Vector y =
        extractTarget(properties);

    Matrix xt =
        transpose(x);

    Matrix xtx =
        multiply(xt, x);

    Matrix yColumn(
        y.size(),
        Vector(1)
    );

    for (std::size_t i = 0;
         i < y.size();
         ++i) {
        yColumn[i][0] = y[i];
    }

    Matrix xty =
        multiply(
            xt,
            yColumn
        );

    Matrix beta =
        multiply(
            inverse(xtx),
            xty
        );

    Vector coefficients;

    for (const auto& row : beta) {
        coefficients.push_back(row[0]);
    }

    return coefficients;
}


// ============================================================
// SYNTHETIC INDUSTRY-LIKE DATA
// ============================================================

std::vector<Property> createDataset() {
    /*
     * This is synthetic educational data.
     *
     * In a real valuation system, records would come from validated
     * historical transactions and would require careful attention to
     * geography, time, property type, data provenance and leakage.
     */
    return {
        {800, 2, 25, 12, 180000},
        {900, 2, 20, 10, 205000},
        {1000, 2, 18, 9, 220000},
        {1100, 3, 15, 8, 250000},
        {1200, 3, 12, 7, 275000},
        {1300, 3, 10, 6, 300000},
        {1400, 3, 9, 5, 330000},
        {1500, 4, 8, 6, 350000},
        {1600, 4, 7, 5, 375000},
        {1700, 4, 6, 4, 400000},
        {1800, 4, 5, 4, 425000},
        {1900, 4, 5, 3, 450000},
        {2000, 5, 4, 4, 475000},
        {2100, 5, 3, 3, 500000},
        {2200, 5, 3, 3, 530000},
        {2300, 5, 4, 2, 545000},
        {2400, 5, 2, 2, 575000},
        {2500, 6, 2, 3, 600000},
        {2600, 6, 1, 2, 630000},
        {2800, 6, 1, 2, 680000}
    };
}


// ============================================================
// MAIN CASE STUDY
// ============================================================

int main() {
    try {
        std::cout
            << std::fixed
            << std::setprecision(2);

        std::cout
            << "REGRESSION CASE STUDY\n"
            << "Property Price Prediction\n"
            << "==============================\n";

        const std::vector<Property> dataset =
            createDataset();

        // Validate every record before model fitting.
        for (const auto& property : dataset) {
            validateProperty(property);
        }

        std::cout
            << "\nValidated observations: "
            << dataset.size()
            << "\n";

        // --------------------------------------------------------
        // TRAIN/TEST SPLIT
        // --------------------------------------------------------

        DatasetSplit split =
            splitDataset(
                dataset,
                0.25,
                42
            );

        std::cout
            << "Training observations: "
            << split.training.size()
            << "\n";

        std::cout
            << "Testing observations: "
            << split.testing.size()
            << "\n";

        // --------------------------------------------------------
        // ORDINARY LEAST SQUARES
        // --------------------------------------------------------

        LinearRegressionModel ols =
            fitOLS(
                split.training
            );

        std::cout
            << "\nOrdinary least squares model\n";

        ols.printEquation();

        printMetrics(
            "Training metrics",
            evaluate(
                ols,
                split.training
            )
        );

        printMetrics(
            "Test metrics",
            evaluate(
                ols,
                split.testing
            )
        );

        printResidualReport(
            ols,
            split.testing
        );

        // --------------------------------------------------------
        // PREDICTION SERVICE
        // --------------------------------------------------------

        Property newProperty{
            1850,
            4,
            5,
            4,
            1
        };

        /*
         * The target field is not used by predict().
         * It is set to a positive placeholder only because the
         * validation structure requires a valid price.
         */
        const double predictedPrice =
            ols.predict(
                newProperty
            );

        std::cout
            << "\nNew property prediction\n"
            << "Area: "
            << newProperty.area
            << "\nBedrooms: "
            << newProperty.bedrooms
            << "\nAge: "
            << newProperty.age
            << "\nDistance: "
            << newProperty.distanceToCenter
            << "\nPredicted price: "
            << predictedPrice
            << "\n";

        // --------------------------------------------------------
        // RIDGE REGRESSION
        // --------------------------------------------------------

        LinearRegressionModel ridge =
            fitRidge(
                split.training,
                100.0
            );

        std::cout
            << "\nRidge regression model\n";

        ridge.printEquation();

        printMetrics(
            "Ridge test metrics",
            evaluate(
                ridge,
                split.testing
            )
        );

        // --------------------------------------------------------
        // POLYNOMIAL MODEL
        // --------------------------------------------------------

        const Vector polynomialCoefficients =
            fitPolynomialAreaModel(
                split.training
            );

        std::cout
            << "\nPolynomial feature model coefficients\n";

        for (std::size_t i = 0;
             i < polynomialCoefficients.size();
             ++i) {
            std::cout
                << "b"
                << i
                << " = "
                << polynomialCoefficients[i]
                << "\n";
        }

        // --------------------------------------------------------
        // MODEL COMPARISON WITHOUT RANKING
        // --------------------------------------------------------

        std::cout
            << "\nModel diagnostics\n"
            << "The OLS and ridge models are evaluated on the same "
               "held-out test set.\n"
            << "Metrics should be interpreted in relation to the "
               "business cost of prediction errors and the data "
               "generating process.\n";

        // --------------------------------------------------------
        // EDGE-CASE DEMONSTRATIONS
        // --------------------------------------------------------

        std::cout
            << "\nEdge-case checks\n";

        try {
            std::vector<Property> emptyDataset;

            fitOLS(emptyDataset);
        }
        catch (const std::exception& error) {
            std::cout
                << "Empty dataset: "
                << error.what()
                << "\n";
        }

        try {
            std::vector<Property> invalidData = {
                {-500, 2, 10, 5, 200000},
                {1000, 3, 8, 4, 250000}
            };

            fitOLS(invalidData);
        }
        catch (const std::exception& error) {
            std::cout
                << "Invalid feature: "
                << error.what()
                << "\n";
        }

        try {
            Matrix singular = {
                {1, 2},
                {2, 4}
            };

            inverse(singular);
        }
        catch (const std::exception& error) {
            std::cout
                << "Singular matrix: "
                << error.what()
                << "\n";
        }

        // --------------------------------------------------------
        // COMPLEXITY NOTES
        // --------------------------------------------------------

        std::cout
            << "\nComputational considerations\n"
            << "For n observations and p predictors, constructing "
               "X'X is approximately O(n*p^2).\n"
            << "A naive matrix inversion is approximately O(p^3).\n"
            << "Prediction for one observation is approximately O(p).\n"
            << "For large systems, specialized numerical linear "
               "algebra and decomposition methods are preferable.\n";

        // --------------------------------------------------------
        // PRODUCTION CONSIDERATIONS
        // --------------------------------------------------------

        std::cout
            << "\nProduction considerations\n"
            << "1. Validate feature schemas at ingestion.\n"
            << "2. Preserve training-time preprocessing parameters.\n"
            << "3. Prevent future information from entering historical "
               "training features.\n"
            << "4. Monitor prediction error and data drift.\n"
            << "5. Version model parameters and training data.\n"
            << "6. Log model inputs and outputs subject to privacy rules.\n"
            << "7. Avoid treating statistical association as causal evidence.\n"
            << "8. Use numerically stable solvers for large systems.\n";

        std::cout
            << "\nCase study completed successfully.\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
