"""
Regression Basics: Understanding Relationships and Prediction

A self-contained study program covering regression from absolute beginner
concepts through practical and advanced ideas.

The examples use only Python's standard library.
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


# ============================================================
# 1. FUNDAMENTAL IDEAS
# ============================================================

def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def subsection(title: str) -> None:
    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)


section("REGRESSION BASICS")

print(
    """
Regression is a statistical and machine-learning technique for studying
relationships between variables and for predicting a target variable.

A simple regression problem can be written as:

    y = f(x) + error

where:
    x     = predictor or independent variable
    y     = response, target, or dependent variable
    f(x)  = systematic relationship
    error = unexplained variation

In linear regression, the model assumes:

    y_hat = b0 + b1*x

where:
    b0 = intercept
    b1 = slope
    y_hat = predicted value

Regression is different from correlation:
correlation describes the strength and direction of linear association,
while regression explicitly defines a predictive relationship.
"""
)


# ============================================================
# 2. A SMALL DATASET
# ============================================================

section("A SMALL REGRESSION DATASET")

hours_studied = [1, 2, 3, 4, 5, 6, 7, 8]
exam_scores = [52, 55, 61, 66, 70, 74, 79, 85]

print("Hours studied:", hours_studied)
print("Exam scores :", exam_scores)


# ============================================================
# 3. MEAN, VARIANCE, COVARIANCE AND CORRELATION
# ============================================================

section("STATISTICAL FOUNDATIONS")


def mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("Cannot calculate the mean of an empty sequence.")
    return sum(values) / len(values)


def sample_variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        raise ValueError("At least two observations are required.")
    average = mean(values)
    return sum((value - average) ** 2 for value in values) / (len(values) - 1)


def covariance(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y):
        raise ValueError("x and y must have equal lengths.")
    if len(x) < 2:
        raise ValueError("At least two observations are required.")

    x_mean = mean(x)
    y_mean = mean(y)

    return sum(
        (xi - x_mean) * (yi - y_mean)
        for xi, yi in zip(x, y)
    ) / (len(x) - 1)


def correlation(x: Sequence[float], y: Sequence[float]) -> float:
    denominator = math.sqrt(
        sample_variance(x) * sample_variance(y)
    )

    if denominator == 0:
        raise ValueError(
            "Correlation is undefined when one variable has zero variance."
        )

    return covariance(x, y) / denominator


print("Mean study hours:", mean(hours_studied))
print("Mean score:", mean(exam_scores))
print("Sample variance of hours:", sample_variance(hours_studied))
print("Sample variance of scores:", sample_variance(exam_scores))
print("Covariance:", covariance(hours_studied, exam_scores))
print("Correlation:", round(correlation(hours_studied, exam_scores), 4))


# ============================================================
# 4. SIMPLE LINEAR REGRESSION FROM FIRST PRINCIPLES
# ============================================================

section("SIMPLE LINEAR REGRESSION")


@dataclass
class SimpleLinearRegression:
    slope: float
    intercept: float

    def predict_one(self, x: float) -> float:
        return self.intercept + self.slope * x

    def predict(self, values: Iterable[float]) -> list[float]:
        return [self.predict_one(value) for value in values]


def fit_simple_linear_regression(
    x: Sequence[float],
    y: Sequence[float],
) -> SimpleLinearRegression:
    if len(x) != len(y):
        raise ValueError("x and y must contain the same number of observations.")

    if len(x) < 2:
        raise ValueError("At least two observations are required.")

    x_mean = mean(x)
    y_mean = mean(y)

    denominator = sum((xi - x_mean) ** 2 for xi in x)

    if denominator == 0:
        raise ValueError(
            "The predictor has zero variance, so a slope cannot be estimated."
        )

    slope = sum(
        (xi - x_mean) * (yi - y_mean)
        for xi, yi in zip(x, y)
    ) / denominator

    intercept = y_mean - slope * x_mean

    return SimpleLinearRegression(slope, intercept)


model = fit_simple_linear_regression(hours_studied, exam_scores)

print("Slope:", round(model.slope, 4))
print("Intercept:", round(model.intercept, 4))
print("Equation:")
print(f"score_hat = {model.intercept:.3f} + {model.slope:.3f} * hours")


# Prediction
new_hours = [2.5, 5.5, 9]
predictions = model.predict(new_hours)

for hours, prediction in zip(new_hours, predictions):
    print(f"{hours} study hours -> predicted score {prediction:.2f}")


# ============================================================
# 5. RESIDUALS
# ============================================================

section("RESIDUALS")

predicted_scores = model.predict(hours_studied)
residuals = [
    actual - predicted
    for actual, predicted in zip(exam_scores, predicted_scores)
]

for x_value, actual, predicted, residual in zip(
    hours_studied,
    exam_scores,
    predicted_scores,
    residuals,
):
    print(
        f"x={x_value:2d}, actual={actual:6.2f}, "
        f"predicted={predicted:6.2f}, residual={residual:7.3f}"
    )

print(
    """
A residual is:

    residual = actual value - predicted value

Positive residual:
    the observation is above the regression line.

Negative residual:
    the observation is below the regression line.

A useful regression model should generally leave residuals that do not show
strong systematic patterns.
"""
)


# ============================================================
# 6. MODEL EVALUATION
# ============================================================

section("REGRESSION METRICS")


def mse(actual: Sequence[float], predicted: Sequence[float]) -> float:
    if len(actual) != len(predicted):
        raise ValueError("Input lengths must match.")
    return mean([
        (a - p) ** 2
        for a, p in zip(actual, predicted)
    ])


def rmse(actual: Sequence[float], predicted: Sequence[float]) -> float:
    return math.sqrt(mse(actual, predicted))


def mae(actual: Sequence[float], predicted: Sequence[float]) -> float:
    if len(actual) != len(predicted):
        raise ValueError("Input lengths must match.")
    return mean([
        abs(a - p)
        for a, p in zip(actual, predicted)
    ])


def r_squared(
    actual: Sequence[float],
    predicted: Sequence[float],
) -> float:
    if len(actual) != len(predicted):
        raise ValueError("Input lengths must match.")

    actual_mean = mean(actual)

    total_sum_of_squares = sum(
        (value - actual_mean) ** 2
        for value in actual
    )

    residual_sum_of_squares = sum(
        (actual_value - predicted_value) ** 2
        for actual_value, predicted_value
        in zip(actual, predicted)
    )

    if total_sum_of_squares == 0:
        raise ValueError(
            "R-squared is undefined when the target has zero variance."
        )

    return 1 - residual_sum_of_squares / total_sum_of_squares


print("MAE :", round(mae(exam_scores, predicted_scores), 4))
print("MSE :", round(mse(exam_scores, predicted_scores), 4))
print("RMSE:", round(rmse(exam_scores, predicted_scores), 4))
print("R²  :", round(r_squared(exam_scores, predicted_scores), 4))


# ============================================================
# 7. WHY R-SQUARED IS NOT ENOUGH
# ============================================================

section("INTERPRETING R-SQUARED")

print(
    """
R² measures the proportion of target variance explained by the model
relative to a baseline that predicts the mean target.

Important cautions:

1. A high R² does not prove causation.
2. A high R² does not guarantee good predictions outside the observed range.
3. A low R² can still be useful in noisy scientific or economic systems.
4. Adding predictors to ordinary linear regression cannot decrease training R².
5. Training performance is not the same as generalization performance.
"""
)


# ============================================================
# 8. MULTIPLE LINEAR REGRESSION
# ============================================================

section("MULTIPLE LINEAR REGRESSION")

print(
    """
Multiple linear regression extends the equation to:

    y_hat = b0 + b1*x1 + b2*x2 + ... + bk*xk

Example:

    house_price =
        b0
        + b1 * area
        + b2 * bedrooms
        + b3 * age
"""
)


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    if not matrix:
        return []
    return [list(column) for column in zip(*matrix)]


def matrix_multiply(
    a: list[list[float]],
    b: list[list[float]],
) -> list[list[float]]:
    if not a or not b:
        raise ValueError("Matrices cannot be empty.")

    if len(a[0]) != len(b):
        raise ValueError("Matrix dimensions are incompatible.")

    result = [
        [0.0 for _ in range(len(b[0]))]
        for _ in range(len(a))
    ]

    for i in range(len(a)):
        for j in range(len(b[0])):
            result[i][j] = sum(
                a[i][k] * b[k][j]
                for k in range(len(b))
            )

    return result


def identity_matrix(size: int) -> list[list[float]]:
    return [
        [
            1.0 if row == column else 0.0
            for column in range(size)
        ]
        for row in range(size)
    ]


def inverse_matrix(matrix: list[list[float]]) -> list[list[float]]:
    """
    Gauss-Jordan matrix inversion with partial pivoting.

    This implementation is educational. Production numerical software
    should normally use stable linear algebra routines rather than explicitly
    forming a matrix inverse.
    """
    n = len(matrix)

    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("Matrix must be non-empty and square.")

    augmented = [
        row[:] + identity_matrix(n)[i]
        for i, row in enumerate(matrix)
    ]

    for column in range(n):
        pivot_row = max(
            range(column, n),
            key=lambda row: abs(augmented[row][column]),
        )

        pivot_value = augmented[pivot_row][column]

        if abs(pivot_value) < 1e-12:
            raise ValueError(
                "Matrix is singular or numerically close to singular."
            )

        if pivot_row != column:
            augmented[column], augmented[pivot_row] = (
                augmented[pivot_row],
                augmented[column],
            )

        pivot = augmented[column][column]

        augmented[column] = [
            value / pivot
            for value in augmented[column]
        ]

        for row in range(n):
            if row == column:
                continue

            factor = augmented[row][column]

            augmented[row] = [
                current - factor * pivot_value
                for current, pivot_value
                in zip(augmented[row], augmented[column])
            ]

    return [
        row[n:]
        for row in augmented
    ]


def fit_multiple_linear_regression(
    x: list[list[float]],
    y: Sequence[float],
) -> list[float]:
    """
    Educational ordinary least squares estimator.

    X includes only predictor columns here.
    The intercept is added automatically.

    Normal equation:

        beta = (X'X)^(-1) X'y

    The normal equation is useful for learning the mathematics, although
    QR or SVD based methods are usually preferred for numerical stability.
    """
    if not x or not y:
        raise ValueError("Training data cannot be empty.")

    if len(x) != len(y):
        raise ValueError("X and y must contain the same number of rows.")

    feature_count = len(x[0])

    if feature_count == 0:
        raise ValueError("At least one feature is required.")

    if any(len(row) != feature_count for row in x):
        raise ValueError("All rows must contain the same number of features.")

    design_matrix = [
        [1.0] + [float(value) for value in row]
        for row in x
    ]

    x_transpose = transpose(design_matrix)
    xtx = matrix_multiply(x_transpose, design_matrix)
    xty = matrix_multiply(
        x_transpose,
        [[float(value)] for value in y],
    )

    xtx_inverse = inverse_matrix(xtx)
    coefficients = matrix_multiply(xtx_inverse, xty)

    return [row[0] for row in coefficients]


def predict_multiple(
    x: list[list[float]],
    coefficients: Sequence[float],
) -> list[float]:
    if not coefficients:
        raise ValueError("Coefficients cannot be empty.")

    expected_features = len(coefficients) - 1

    if any(len(row) != expected_features for row in x):
        raise ValueError("Feature dimensions do not match coefficients.")

    return [
        coefficients[0] + sum(
            coefficient * feature
            for coefficient, feature
            in zip(coefficients[1:], row)
        )
        for row in x
    ]


house_features = [
    [1200, 2, 20],
    [1400, 3, 15],
    [1600, 3, 10],
    [1800, 4, 8],
    [2000, 4, 5],
    [2200, 5, 3],
]

house_prices = [
    210000,
    250000,
    290000,
    330000,
    370000,
    410000,
]

house_coefficients = fit_multiple_linear_regression(
    house_features,
    house_prices,
)

print("Coefficients:", [round(value, 4) for value in house_coefficients])

house_predictions = predict_multiple(
    house_features,
    house_coefficients,
)

print("Training RMSE:", round(
    rmse(house_prices, house_predictions),
    4,
))


# ============================================================
# 9. TRAINING AND TESTING
# ============================================================

section("TRAINING AND TEST DATA")

print(
    """
A model should normally be evaluated on observations that were not used
to estimate its parameters.

Training set:
    used to fit model parameters.

Validation set:
    often used to select models or tune hyperparameters.

Test set:
    reserved for final unbiased performance assessment.

Using the test set repeatedly during model development can turn it into
an unofficial validation set and lead to optimistic estimates.
"""
)


def train_test_split(
    x: Sequence,
    y: Sequence,
    test_ratio: float = 0.25,
    seed: int = 42,
) -> tuple[list, list, list, list]:
    if len(x) != len(y):
        raise ValueError("x and y lengths must match.")

    if not 0 < test_ratio < 1:
        raise ValueError("test_ratio must be between 0 and 1.")

    indices = list(range(len(x)))
    generator = random.Random(seed)
    generator.shuffle(indices)

    test_size = max(1, int(round(len(x) * test_ratio)))

    test_indices = indices[:test_size]
    train_indices = indices[test_size:]

    x_train = [x[index] for index in train_indices]
    x_test = [x[index] for index in test_indices]
    y_train = [y[index] for index in train_indices]
    y_test = [y[index] for index in test_indices]

    return x_train, x_test, y_train, y_test


x_train, x_test, y_train, y_test = train_test_split(
    hours_studied,
    exam_scores,
)

split_model = fit_simple_linear_regression(x_train, y_train)
train_predictions = split_model.predict(x_train)
test_predictions = split_model.predict(x_test)

print("Training examples:", list(zip(x_train, y_train)))
print("Test examples    :", list(zip(x_test, y_test)))
print("Training RMSE:", round(rmse(y_train, train_predictions), 4))
print("Test RMSE    :", round(rmse(y_test, test_predictions), 4))


# ============================================================
# 10. GRADIENT DESCENT
# ============================================================

section("LINEAR REGRESSION WITH GRADIENT DESCENT")

print(
    """
Gradient descent provides an optimization-based way to estimate parameters.

For a model:

    y_hat = w*x + b

the mean squared error is:

    MSE = (1/n) * sum((y - y_hat)^2)

The parameters are repeatedly updated in the direction that decreases
the loss.

Standardization is important for many optimization problems because
features with very different scales can produce poorly conditioned
optimization paths.
"""
)


def standardize(
    values: Sequence[float],
) -> tuple[list[float], float, float]:
    average = mean(values)
    standard_deviation = statistics.stdev(values)

    if standard_deviation == 0:
        raise ValueError("Cannot standardize a constant feature.")

    return (
        [
            (value - average) / standard_deviation
            for value in values
        ],
        average,
        standard_deviation,
    )


def gradient_descent_linear_regression(
    x: Sequence[float],
    y: Sequence[float],
    learning_rate: float = 0.05,
    epochs: int = 5000,
) -> tuple[float, float, list[float]]:
    if len(x) != len(y) or not x:
        raise ValueError("x and y must have equal non-zero lengths.")

    if learning_rate <= 0:
        raise ValueError("Learning rate must be positive.")

    if epochs <= 0:
        raise ValueError("Epochs must be positive.")

    x_scaled, x_mean, x_std = standardize(x)

    weight = 0.0
    bias = mean(y)
    losses = []

    n = len(x_scaled)

    for _ in range(epochs):
        predictions = [
            weight * feature + bias
            for feature in x_scaled
        ]

        errors = [
            prediction - target
            for prediction, target
            in zip(predictions, y)
        ]

        loss = sum(error ** 2 for error in errors) / n
        losses.append(loss)

        gradient_weight = (
            2 / n
        ) * sum(
            error * feature
            for error, feature
            in zip(errors, x_scaled)
        )

        gradient_bias = (
            2 / n
        ) * sum(errors)

        weight -= learning_rate * gradient_weight
        bias -= learning_rate * gradient_bias

    # Convert coefficients from standardized-x space back to original x.
    original_slope = weight / x_std
    original_intercept = bias - original_slope * x_mean

    return original_slope, original_intercept, losses


gd_slope, gd_intercept, losses = gradient_descent_linear_regression(
    hours_studied,
    exam_scores,
)

gd_predictions = [
    gd_intercept + gd_slope * value
    for value in hours_studied
]

print("Gradient descent slope:", round(gd_slope, 4))
print("Gradient descent intercept:", round(gd_intercept, 4))
print("Final loss:", round(losses[-1], 6))


# ============================================================
# 11. POLYNOMIAL REGRESSION
# ============================================================

section("POLYNOMIAL REGRESSION")

print(
    """
Polynomial regression models nonlinear relationships by expanding the
feature space:

    y_hat = b0 + b1*x + b2*x² + ... + bk*x^k

The model is nonlinear in x but remains linear in its coefficients.

A polynomial that is too simple may underfit.
A polynomial that is too flexible may overfit.
"""
)


def polynomial_features(
    values: Sequence[float],
    degree: int,
) -> list[list[float]]:
    if degree < 1:
        raise ValueError("Degree must be at least 1.")

    return [
        [value ** power for power in range(1, degree + 1)]
        for value in values
    ]


curved_x = [0, 1, 2, 3, 4, 5]
curved_y = [1.1, 2.8, 6.9, 13.2, 21.1, 31.3]

curved_features = polynomial_features(curved_x, degree=2)
curved_coefficients = fit_multiple_linear_regression(
    curved_features,
    curved_y,
)

curved_predictions = predict_multiple(
    curved_features,
    curved_coefficients,
)

print(
    "Polynomial coefficients:",
    [round(value, 4) for value in curved_coefficients],
)
print("Polynomial RMSE:", round(
    rmse(curved_y, curved_predictions),
    4,
))


# ============================================================
# 12. REGULARIZATION
# ============================================================

section("REGULARIZATION")

print(
    """
Regularization discourages unnecessarily large coefficients.

Ridge regression adds an L2 penalty:

    loss = SSE + lambda * sum(beta_j²)

Lasso regression adds an L1 penalty:

    loss = SSE + lambda * sum(|beta_j|)

Ridge generally shrinks coefficients toward zero.
Lasso can shrink some coefficients exactly to zero, which can produce
sparse models.

The intercept is normally excluded from the regularization penalty.
"""
)


def ridge_regression(
    x: list[list[float]],
    y: Sequence[float],
    alpha: float = 1.0,
) -> list[float]:
    if alpha < 0:
        raise ValueError("alpha must be non-negative.")

    if not x or len(x) != len(y):
        raise ValueError("Invalid training data.")

    design = [
        [1.0] + [float(value) for value in row]
        for row in x
    ]

    xt = transpose(design)
    xtx = matrix_multiply(xt, design)
    xty = matrix_multiply(
        xt,
        [[float(value)] for value in y],
    )

    # Do not penalize the intercept.
    for index in range(1, len(xtx)):
        xtx[index][index] += alpha

    coefficients = matrix_multiply(
        inverse_matrix(xtx),
        xty,
    )

    return [row[0] for row in coefficients]


ridge_coefficients = ridge_regression(
    house_features,
    house_prices,
    alpha=10.0,
)

print(
    "Ridge coefficients:",
    [round(value, 4) for value in ridge_coefficients],
)


# ============================================================
# 13. CATEGORICAL VARIABLES
# ============================================================

section("CATEGORICAL VARIABLES")

print(
    """
Regression models operate on numerical representations.

For a categorical feature such as:

    city = {Delhi, Mumbai, Lucknow}

one common encoding is one-hot encoding:

    Delhi  -> [1, 0, 0]
    Mumbai -> [0, 1, 0]
    Lucknow -> [0, 0, 1]

With an intercept, using all category indicators simultaneously can create
perfect multicollinearity. A reference category can be omitted.
"""
)


def one_hot_encode(
    values: Sequence[str],
    categories: Sequence[str] | None = None,
) -> tuple[list[list[int]], list[str]]:
    if categories is None:
        categories = sorted(set(values))

    categories = list(categories)

    unknown = set(values) - set(categories)
    if unknown:
        raise ValueError(
            f"Unknown categories encountered: {sorted(unknown)}"
        )

    encoded = [
        [
            1 if value == category else 0
            for category in categories
        ]
        for value in values
    ]

    return encoded, categories


cities = ["Delhi", "Mumbai", "Lucknow", "Delhi"]
encoded_cities, city_categories = one_hot_encode(cities)

print("Categories:", city_categories)
print("Encoded values:", encoded_cities)


# ============================================================
# 14. LOG TRANSFORMATION
# ============================================================

section("TRANSFORMATIONS")

print(
    """
Transformations can make a relationship easier to model.

A logarithmic relationship can be represented as:

    y = b0 + b1*log(x)

A log transformation requires x > 0.

Transformations may help with:
    - skewed predictors
    - multiplicative relationships
    - changing variance
    - nonlinear patterns

Transformations should be justified by the data-generating context rather
than applied mechanically.
"""
)


def safe_log_transform(values: Sequence[float]) -> list[float]:
    if any(value <= 0 for value in values):
        raise ValueError("Log transformation requires strictly positive values.")
    return [math.log(value) for value in values]


positive_values = [1, 2, 4, 8, 16]
print("Original:", positive_values)
print("Natural logarithm:", [
    round(value, 4)
    for value in safe_log_transform(positive_values)
])


# ============================================================
# 15. OUTLIERS AND LEVERAGE
# ============================================================

section("OUTLIERS, LEVERAGE AND INFLUENCE")

print(
    """
An outlier is an observation unusual relative to the rest of the data.

A high-leverage point has an unusual predictor value.

An influential observation can substantially change the fitted model.

These concepts are related but not identical.

Important diagnostic questions include:

    Is the observation a data-entry error?
    Is it a valid rare event?
    Does the model adequately describe the population?
    Does the observation belong to the target population?

Removing observations solely because they make the model look better
can introduce bias.
"""
)


# ============================================================
# 16. HETEROSCEDASTICITY
# ============================================================

section("HETEROSCEDASTICITY")

print(
    """
Homoscedasticity means the error variance is approximately constant.

Heteroscedasticity means error variance changes across predictor values.

For example, large businesses may have much greater variation in annual
revenue than small businesses.

Ordinary least squares coefficient estimates can still be useful under
some forms of heteroscedasticity, but conventional standard errors may
be unreliable. Robust standard errors or alternative modeling strategies
may be appropriate.
"""
)


# ============================================================
# 17. MULTICOLLINEARITY
# ============================================================

section("MULTICOLLINEARITY")

print(
    """
Multicollinearity occurs when predictors contain substantial redundant
information.

Example:

    annual_income
    monthly_income

are almost deterministic transformations of each other.

Consequences can include:
    - unstable coefficient estimates
    - large standard errors
    - coefficients changing considerably across samples
    - difficulty interpreting individual effects

Prediction can remain reasonable even when individual coefficient
interpretation is problematic.
"""
)


# ============================================================
# 18. UNDERFITTING AND OVERFITTING
# ============================================================

section("UNDERFITTING AND OVERFITTING")

print(
    """
Underfitting:
    the model is too simple to capture important structure.

Overfitting:
    the model learns noise or accidental patterns in the training data.

Typical progression:

    too simple -> useful structure -> excessive complexity

Generalization error is the central concern when selecting model
complexity.
"""
)


# ============================================================
# 19. CROSS-VALIDATION
# ============================================================

section("K-FOLD CROSS-VALIDATION")


def k_fold_indices(
    sample_count: int,
    k: int = 5,
    seed: int = 42,
) -> list[tuple[list[int], list[int]]]:
    if sample_count < 2:
        raise ValueError("At least two samples are required.")

    if not 2 <= k <= sample_count:
        raise ValueError("k must be between 2 and the sample count.")

    indices = list(range(sample_count))
    random.Random(seed).shuffle(indices)

    folds = [
        indices[i::k]
        for i in range(k)
    ]

    splits = []

    for fold_index in range(k):
        validation = folds[fold_index]
        training = [
            index
            for other_fold, fold in enumerate(folds)
            if other_fold != fold_index
            for index in fold
        ]
        splits.append((training, validation))

    return splits


splits = k_fold_indices(len(hours_studied), k=4)

for fold_number, (training_indices, validation_indices) in enumerate(
    splits,
    start=1,
):
    print(
        f"Fold {fold_number}: "
        f"train={training_indices}, "
        f"validation={validation_indices}"
    )


# ============================================================
# 20. CONFIDENCE INTERVAL VS PREDICTION INTERVAL
# ============================================================

section("CONFIDENCE INTERVALS AND PREDICTION INTERVALS")

print(
    """
A confidence interval for a regression mean concerns uncertainty about
the expected response at a predictor value.

A prediction interval concerns uncertainty for a future individual
observation.

Prediction intervals are generally wider because they include both:
    - uncertainty in estimating the mean relationship
    - individual outcome variability

These concepts should not be confused.
"""
)


# ============================================================
# 21. CAUSATION
# ============================================================

section("ASSOCIATION IS NOT CAUSATION")

print(
    """
Regression can quantify associations and make predictions.

A regression coefficient by itself does not establish that changing
a predictor will cause the target to change.

Causal interpretation requires assumptions or designs such as:
    - randomized experiments
    - credible natural experiments
    - causal identification strategies
    - appropriate controls for confounding

A statistically significant coefficient is not automatically a causal
effect.
"""
)


# ============================================================
# 22. BINARY TARGETS AND LOGISTIC REGRESSION
# ============================================================

section("LOGISTIC REGRESSION")

print(
    """
When the target is binary, ordinary linear regression can produce
predictions below 0 or above 1.

Logistic regression models probability using the sigmoid function:

    p = 1 / (1 + exp(-z))

where:

    z = b0 + b1*x1 + ... + bk*xk

The coefficients are often interpreted through odds ratios:

    odds ratio = exp(beta)

This is a classification model despite its name.
"""
)


def sigmoid(value: float) -> float:
    # Stable enough for ordinary educational values.
    if value >= 0:
        exponent = math.exp(-value)
        return 1 / (1 + exponent)

    exponent = math.exp(value)
    return exponent / (1 + exponent)


for value in [-5, -1, 0, 1, 5]:
    print(f"sigmoid({value}) = {sigmoid(value):.6f}")


# ============================================================
# 23. POISSON REGRESSION
# ============================================================

section("COUNT DATA")

print(
    """
When the target is a count, such as:
    - number of support tickets
    - number of incidents
    - number of purchases

a generalized linear model such as Poisson regression may be more
appropriate than ordinary linear regression.

A log link commonly represents:

    log(E[Y | X]) = beta0 + beta1*x1 + ...

The correct regression family depends on the target's distribution and
the assumptions of the modeling problem.
"""
)


# ============================================================
# 24. ROBUST LOSS FUNCTIONS
# ============================================================

section("ROBUST REGRESSION IDEAS")

print(
    """
Ordinary least squares uses squared residuals.

Because large residuals are squared, extreme observations can have
substantial influence.

Alternative losses include:

Absolute error:
    |error|

Huber loss:
    quadratic near zero
    approximately linear for large errors

Robust approaches can reduce sensitivity to extreme residuals, but
they do not automatically solve data-quality problems or every form
of model misspecification.
"""
)


# ============================================================
# 25. FEATURE ENGINEERING
# ============================================================

section("FEATURE ENGINEERING")

print(
    """
Regression quality often depends on how the available information is
represented.

Examples:

Raw:
    transaction_date

Engineered:
    day_of_week
    month
    holiday_indicator
    days_since_customer_signup

Raw:
    area

Engineered:
    area_per_bedroom

Feature engineering should respect temporal ordering and avoid leakage.
"""
)


# ============================================================
# 26. DATA LEAKAGE
# ============================================================

section("DATA LEAKAGE")

print(
    """
Data leakage occurs when information unavailable at prediction time
enters model training.

Example:

Predicting whether a loan will default using a field that is only
recorded after the default occurs.

Leakage can create excellent-looking validation results that fail in
production.

Every feature should be evaluated using the question:

    "Would this information genuinely be available at prediction time?"
"""
)


# ============================================================
# 27. EXTRAPOLATION
# ============================================================

section("EXTRAPOLATION")

print(
    """
Interpolation predicts within the range represented by training data.

Extrapolation predicts outside that range.

Example:
    Training data: 10 to 100 years of age
    Prediction: age 200

A regression equation can mathematically produce such a value, but
the statistical relationship may not remain valid outside the observed
domain.

Extrapolation should therefore be treated cautiously.
"""
)


# ============================================================
# 28. MODEL ASSUMPTIONS
# ============================================================

section("ORDINARY LEAST SQUARES ASSUMPTIONS")

print(
    """
Important assumptions depend on the purpose of the analysis.

Common considerations include:

1. Linearity in parameters.
2. Appropriate specification of the conditional mean.
3. Independent observations where independence is required.
4. Reasonable treatment of influential observations.
5. Error variance assumptions when making standard-error-based inference.
6. Absence of perfect multicollinearity.
7. Appropriate measurement and sampling process.

Normality of errors is not required simply to calculate ordinary least
squares coefficients. It can matter for certain small-sample inferential
procedures.
"""
)


# ============================================================
# 29. EDGE CASES
# ============================================================

section("EDGE CASES")

edge_cases = {
    "empty data": "Cannot estimate a model.",
    "one observation": "Insufficient information for ordinary slope estimation.",
    "constant predictor": "Slope denominator becomes zero.",
    "constant target": "R² is undefined under the standard formula.",
    "missing values": "Must be handled deliberately rather than silently ignored.",
    "extreme outlier": "Can strongly affect least-squares estimates.",
    "perfect collinearity": "Coefficient system becomes non-identifiable.",
    "prediction outside training range": "Potential extrapolation risk.",
}

for name, behavior in edge_cases.items():
    print(f"{name:28s}: {behavior}")


# ============================================================
# 30. VALIDATION HELPER
# ============================================================

section("DATA VALIDATION")


def validate_regression_data(
    x: Sequence[float],
    y: Sequence[float],
) -> None:
    if not x or not y:
        raise ValueError("Regression data cannot be empty.")

    if len(x) != len(y):
        raise ValueError("Predictor and target lengths must match.")

    if any(
        not isinstance(value, (int, float)) or not math.isfinite(value)
        for value in x
    ):
        raise ValueError("All predictor values must be finite numbers.")

    if any(
        not isinstance(value, (int, float)) or not math.isfinite(value)
        for value in y
    ):
        raise ValueError("All target values must be finite numbers.")


validate_regression_data(hours_studied, exam_scores)
print("Validation successful.")


# ============================================================
# 31. REPRODUCIBLE SYNTHETIC DATA
# ============================================================

section("SYNTHETIC DATA AND NOISE")

generator = random.Random(7)

synthetic_x = list(range(1, 21))
synthetic_y = [
    20 + 4 * x + generator.gauss(0, 3)
    for x in synthetic_x
]

synthetic_model = fit_simple_linear_regression(
    synthetic_x,
    synthetic_y,
)

synthetic_predictions = synthetic_model.predict(synthetic_x)

print("Estimated slope:", round(synthetic_model.slope, 3))
print("Estimated intercept:", round(synthetic_model.intercept, 3))
print("R²:", round(
    r_squared(synthetic_y, synthetic_predictions),
    4,
))


# ============================================================
# 32. A COMPLETE MINI REGRESSION WORKFLOW
# ============================================================

section("COMPLETE MINI WORKFLOW")

workflow_x = [
    10, 12, 15, 17, 20,
    23, 25, 27, 30, 32,
]

workflow_y = [
    31, 35, 39, 43, 48,
    54, 57, 61, 67, 71,
]

validate_regression_data(workflow_x, workflow_y)

workflow_train_x, workflow_test_x, workflow_train_y, workflow_test_y = (
    train_test_split(
        workflow_x,
        workflow_y,
        test_ratio=0.2,
        seed=10,
    )
)

workflow_model = fit_simple_linear_regression(
    workflow_train_x,
    workflow_train_y,
)

workflow_train_prediction = workflow_model.predict(workflow_train_x)
workflow_test_prediction = workflow_model.predict(workflow_test_x)

print("Model:")
print(
    f"y_hat = {workflow_model.intercept:.4f} "
    f"+ {workflow_model.slope:.4f}x"
)

print("\nTraining metrics:")
print("MAE :", round(
    mae(workflow_train_y, workflow_train_prediction),
    4,
))
print("RMSE:", round(
    rmse(workflow_train_y, workflow_train_prediction),
    4,
))
print("R²  :", round(
    r_squared(workflow_train_y, workflow_train_prediction),
    4,
))

print("\nTest metrics:")
print("MAE :", round(
    mae(workflow_test_y, workflow_test_prediction),
    4,
))
print("RMSE:", round(
    rmse(workflow_test_y, workflow_test_prediction),
    4,
))

print("\nPredictions:")
for actual_x, actual_y, predicted_y in zip(
    workflow_test_x,
    workflow_test_y,
    workflow_test_prediction,
):
    print(
        f"x={actual_x:2d}, actual={actual_y:6.2f}, "
        f"predicted={predicted_y:6.2f}, "
        f"residual={actual_y - predicted_y:7.2f}"
    )


# ============================================================
# 33. DEBUGGING EXAMPLE
# ============================================================

section("DEBUGGING A REGRESSION MODEL")

def debug_regression(
    x: Sequence[float],
    y: Sequence[float],
) -> SimpleLinearRegression:
    validate_regression_data(x, y)

    if len(x) < 2:
        raise ValueError("At least two observations are required.")

    if len(set(x)) == 1:
        raise ValueError(
            "All predictor values are identical; slope cannot be estimated."
        )

    fitted_model = fit_simple_linear_regression(x, y)

    if not math.isfinite(fitted_model.slope):
        raise ValueError("Estimated slope is not finite.")

    if not math.isfinite(fitted_model.intercept):
        raise ValueError("Estimated intercept is not finite.")

    return fitted_model


debugged_model = debug_regression(
    [1, 2, 3, 4],
    [2, 4, 5, 8],
)

print("Debugged model slope:", round(debugged_model.slope, 4))
print("Debugged model intercept:", round(
    debugged_model.intercept,
    4,
))


# ============================================================
# 34. FINAL CONCEPT CHECK
# ============================================================

section("CONCEPT CHECK")

questions = [
    (
        "What does a regression model estimate?",
        "A relationship between predictors and a target, often for explanation or prediction.",
    ),
    (
        "What is a residual?",
        "Observed target minus predicted target.",
    ),
    (
        "What does RMSE measure?",
        "The square root of average squared prediction error.",
    ),
    (
        "What is overfitting?",
        "Learning training-specific noise or accidental structure that does not generalize.",
    ),
    (
        "Does correlation prove causation?",
        "No.",
    ),
    (
        "Why use a test set?",
        "To obtain an evaluation that was not directly used for model development.",
    ),
    (
        "Why regularize?",
        "To control coefficient complexity and potentially improve generalization.",
    ),
    (
        "What is extrapolation?",
        "Prediction outside the predictor range represented by the training data.",
    ),
]

for question, answer in questions:
    print(f"\nQ: {question}\nA: {answer}")


section("END OF REGRESSION STUDY SCRIPT")

print(
    """
The program has demonstrated the progression from descriptive statistics
to simple linear regression, multiple regression, optimization,
transformations, categorical variables, regularization, validation,
diagnostics, and practical modeling considerations.
"""
)
