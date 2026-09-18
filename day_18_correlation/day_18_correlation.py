"""
Correlation: Measuring Relationships Between Variables
=======================================================

A comprehensive, self-contained study program covering correlation from
absolute beginner concepts through advanced statistical implementation.

The examples use only Python's standard library so the file can be executed
without installing external packages.

Run:
    python correlation.py
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass
from itertools import combinations
from typing import Callable, Iterable, Optional, Sequence


# ============================================================================
# 1. FUNDAMENTAL IDEAS
# ============================================================================

def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def subsection(title: str) -> None:
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


def mean(values: Sequence[float]) -> float:
    """Arithmetic mean."""
    if not values:
        raise ValueError("Mean requires at least one observation.")
    return sum(values) / len(values)


def validate_pairs(x: Sequence[float], y: Sequence[float]) -> None:
    """Validate paired observations used by correlation measures."""
    if len(x) != len(y):
        raise ValueError("Both variables must contain the same number of observations.")
    if len(x) < 2:
        raise ValueError("At least two paired observations are required.")
    if any(not math.isfinite(float(value)) for value in x + y):
        raise ValueError("Correlation requires finite numeric observations.")


def describe_relationship(r: float) -> str:
    """Give a descriptive interpretation without treating correlation as causation."""
    magnitude = abs(r)

    if magnitude < 0.10:
        strength = "negligible"
    elif magnitude < 0.30:
        strength = "weak"
    elif magnitude < 0.50:
        strength = "moderate"
    elif magnitude < 0.70:
        strength = "substantial"
    elif magnitude < 0.90:
        strength = "strong"
    else:
        strength = "very strong"

    direction = "positive" if r > 0 else "negative" if r < 0 else "no"
    return f"{strength} {direction} linear association"


# ============================================================================
# 2. COVARIANCE
# ============================================================================

def covariance_population(x: Sequence[float], y: Sequence[float]) -> float:
    """
    Population covariance.

    Cov(X,Y) = sum((xi - mean_x)(yi - mean_y)) / n
    """
    validate_pairs(x, y)
    x_mean = mean(x)
    y_mean = mean(y)

    return sum(
        (xi - x_mean) * (yi - y_mean)
        for xi, yi in zip(x, y)
    ) / len(x)


def covariance_sample(x: Sequence[float], y: Sequence[float]) -> float:
    """
    Sample covariance.

    The denominator is n - 1 because the observations are treated as a sample
    from a larger population.
    """
    validate_pairs(x, y)
    x_mean = mean(x)
    y_mean = mean(y)

    return sum(
        (xi - x_mean) * (yi - y_mean)
        for xi, yi in zip(x, y)
    ) / (len(x) - 1)


# ============================================================================
# 3. PEARSON CORRELATION
# ============================================================================

def pearson_correlation(x: Sequence[float], y: Sequence[float]) -> float:
    """
    Calculate Pearson's product-moment correlation coefficient.

    r = sum((xi-xbar)(yi-ybar)) /
        sqrt(sum((xi-xbar)^2) * sum((yi-ybar)^2))

    Pearson correlation measures the strength and direction of a linear
    relationship. It is bounded between -1 and +1.
    """
    validate_pairs(x, y)

    x_mean = mean(x)
    y_mean = mean(y)

    centered_x = [value - x_mean for value in x]
    centered_y = [value - y_mean for value in y]

    numerator = sum(a * b for a, b in zip(centered_x, centered_y))
    denominator_x = math.sqrt(sum(a * a for a in centered_x))
    denominator_y = math.sqrt(sum(b * b for b in centered_y))

    if denominator_x == 0 or denominator_y == 0:
        raise ValueError(
            "Pearson correlation is undefined when either variable has zero variance."
        )

    return numerator / (denominator_x * denominator_y)


# ============================================================================
# 4. NUMERIC STABILITY
# ============================================================================

def pearson_correlation_stable(
    x: Sequence[float],
    y: Sequence[float],
) -> float:
    """
    A numerically careful Pearson calculation.

    The formula is algebraically equivalent to the standard implementation,
    but centering before multiplication reduces avoidable floating-point
    cancellation.
    """
    validate_pairs(x, y)

    x_mean = math.fsum(x) / len(x)
    y_mean = math.fsum(y) / len(y)

    centered_x = [value - x_mean for value in x]
    centered_y = [value - y_mean for value in y]

    numerator = math.fsum(
        a * b for a, b in zip(centered_x, centered_y)
    )
    x_sum_squares = math.fsum(a * a for a in centered_x)
    y_sum_squares = math.fsum(b * b for b in centered_y)

    denominator = math.sqrt(x_sum_squares * y_sum_squares)

    if denominator == 0:
        raise ValueError("Correlation is undefined for a constant variable.")

    return numerator / denominator


# ============================================================================
# 5. RANKING
# ============================================================================

def rank_with_ties(values: Sequence[float]) -> list[float]:
    """
    Convert observations to ranks using average ranks for ties.

    Example:
        [30, 10, 20, 20]
        -> [4, 1, 2.5, 2.5]

    Average ranks are important for Spearman correlation when duplicate
    observations occur.
    """
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)

    position = 0
    while position < len(indexed):
        end = position + 1
        current_value = indexed[position][1]

        while end < len(indexed) and indexed[end][1] == current_value:
            end += 1

        # Ranks are one-based. If positions are 0,1,2, the corresponding
        # statistical ranks are 1,2,3.
        average_rank = ((position + 1) + end) / 2.0

        for index in range(position, end):
            original_index = indexed[index][0]
            ranks[original_index] = average_rank

        position = end

    return ranks


def spearman_correlation(
    x: Sequence[float],
    y: Sequence[float],
) -> float:
    """
    Spearman's rank correlation coefficient.

    Spearman correlation is Pearson correlation applied to ranks. It is useful
    when the relationship is monotonic but not necessarily linear and is less
    dependent on the original measurement scale.
    """
    validate_pairs(x, y)

    x_ranks = rank_with_ties(x)
    y_ranks = rank_with_ties(y)

    return pearson_correlation(x_ranks, y_ranks)


# ============================================================================
# 6. KENDALL'S TAU
# ============================================================================

def kendall_tau(
    x: Sequence[float],
    y: Sequence[float],
) -> float:
    """
    Calculate Kendall's tau-a.

    For every pair of observations:
      concordant  -> both variables move in the same direction
      discordant  -> variables move in opposite directions
      tied        -> at least one variable has equal values

    Tau-a ignores tied pairs in the numerator and uses all pairs in the
    denominator. Tau-b uses a tie-adjusted denominator and is usually more
    appropriate when ties are common.
    """
    validate_pairs(x, y)

    concordant = 0
    discordant = 0

    for i, j in combinations(range(len(x)), 2):
        dx = x[j] - x[i]
        dy = y[j] - y[i]

        if dx == 0 or dy == 0:
            continue

        if dx * dy > 0:
            concordant += 1
        else:
            discordant += 1

    total_pairs = len(x) * (len(x) - 1) / 2

    if total_pairs == 0:
        raise ValueError("Kendall's tau requires at least two observations.")

    return (concordant - discordant) / total_pairs


def kendall_tau_b(
    x: Sequence[float],
    y: Sequence[float],
) -> float:
    """
    Calculate Kendall's tau-b with tie correction.

    tau-b =
      (C-D) / sqrt((C+D+Tx)(C+D+Ty))

    Tx counts pairs tied only on X.
    Ty counts pairs tied only on Y.
    """
    validate_pairs(x, y)

    concordant = 0
    discordant = 0
    ties_x_only = 0
    ties_y_only = 0

    for i, j in combinations(range(len(x)), 2):
        dx = x[j] - x[i]
        dy = y[j] - y[i]

        if dx == 0 and dy == 0:
            continue

        if dx == 0:
            ties_x_only += 1
        elif dy == 0:
            ties_y_only += 1
        elif dx * dy > 0:
            concordant += 1
        else:
            discordant += 1

    denominator = math.sqrt(
        (concordant + discordant + ties_x_only)
        * (concordant + discordant + ties_y_only)
    )

    if denominator == 0:
        raise ValueError("Kendall's tau-b is undefined for this data.")

    return (concordant - discordant) / denominator


# ============================================================================
# 7. POINT-BISERIAL CORRELATION
# ============================================================================

def point_biserial_correlation(
    binary: Sequence[int],
    continuous: Sequence[float],
) -> float:
    """
    Calculate point-biserial correlation.

    The binary variable must contain exactly two groups, represented by 0 and 1.

    r_pb = (M1 - M0) / sy * sqrt(n1*n0/n^2)

    This is mathematically related to Pearson correlation between a binary
    0/1 variable and a continuous variable.
    """
    validate_pairs(binary, continuous)

    if any(value not in (0, 1) for value in binary):
        raise ValueError("The binary variable must contain only 0 and 1.")

    group_zero = [
        value for group, value in zip(binary, continuous)
        if group == 0
    ]
    group_one = [
        value for group, value in zip(binary, continuous)
        if group == 1
    ]

    if not group_zero or not group_one:
        raise ValueError("Both binary groups must contain observations.")

    continuous_mean = mean(continuous)
    variance = sum(
        (value - continuous_mean) ** 2
        for value in continuous
    ) / (len(continuous) - 1)

    standard_deviation = math.sqrt(variance)

    if standard_deviation == 0:
        raise ValueError("The continuous variable has zero variance.")

    n0 = len(group_zero)
    n1 = len(group_one)
    n = n0 + n1

    return (
        (mean(group_one) - mean(group_zero))
        / standard_deviation
        * math.sqrt((n1 * n0) / (n * n))
    )


# ============================================================================
# 8. PARTIAL CORRELATION
# ============================================================================

def linear_regression_coefficients(
    x: Sequence[float],
    y: Sequence[float],
) -> tuple[float, float]:
    """
    Fit y = intercept + slope*x using ordinary least squares.

    This small implementation is used to calculate residuals for partial
    correlation.
    """
    validate_pairs(x, y)

    x_mean = mean(x)
    y_mean = mean(y)

    denominator = sum((value - x_mean) ** 2 for value in x)

    if denominator == 0:
        raise ValueError("Regression predictor has zero variance.")

    slope = sum(
        (xi - x_mean) * (yi - y_mean)
        for xi, yi in zip(x, y)
    ) / denominator

    intercept = y_mean - slope * x_mean

    return intercept, slope


def residuals_after_regression(
    target: Sequence[float],
    control: Sequence[float],
) -> list[float]:
    """Remove the linear effect of control from target."""
    intercept, slope = linear_regression_coefficients(control, target)

    return [
        actual - (intercept + slope * predictor)
        for actual, predictor in zip(target, control)
    ]


def partial_correlation(
    x: Sequence[float],
    y: Sequence[float],
    control: Sequence[float],
) -> float:
    """
    Calculate first-order partial Pearson correlation.

    Concept:
      1. Regress X on the control variable.
      2. Regress Y on the control variable.
      3. Correlate the two sets of residuals.

    This measures the linear association between X and Y after removing the
    linear contribution of the control variable.
    """
    validate_pairs(x, y)
    validate_pairs(x, control)

    x_residuals = residuals_after_regression(x, control)
    y_residuals = residuals_after_regression(y, control)

    return pearson_correlation(x_residuals, y_residuals)


# ============================================================================
# 9. CORRELATION MATRIX
# ============================================================================

def correlation_matrix(
    dataset: dict[str, Sequence[float]],
) -> dict[str, dict[str, float]]:
    """
    Build a Pearson correlation matrix represented as nested dictionaries.
    """
    names = list(dataset)
    matrix: dict[str, dict[str, float]] = {}

    for first_name in names:
        matrix[first_name] = {}

        for second_name in names:
            if first_name == second_name:
                matrix[first_name][second_name] = 1.0
            else:
                matrix[first_name][second_name] = pearson_correlation(
                    dataset[first_name],
                    dataset[second_name],
                )

    return matrix


def print_correlation_matrix(
    matrix: dict[str, dict[str, float]],
) -> None:
    names = list(matrix)

    print("".ljust(15) + "".join(name.rjust(15) for name in names))

    for row_name in names:
        values = "".join(
            f"{matrix[row_name][column_name]:15.3f}"
            for column_name in names
        )
        print(f"{row_name:<15}{values}")


# ============================================================================
# 10. SIMPLE LINEAR REGRESSION CONNECTION
# ============================================================================

@dataclass
class RegressionResult:
    intercept: float
    slope: float
    r: float
    r_squared: float

    def predict(self, x_value: float) -> float:
        return self.intercept + self.slope * x_value


def simple_linear_regression(
    x: Sequence[float],
    y: Sequence[float],
) -> RegressionResult:
    """
    Fit a simple least-squares regression.

    In simple linear regression with an intercept:
        R^2 = r^2

    This relationship does not mean correlation and regression are identical.
    Regression additionally defines a response/predictor structure and gives
    a fitted equation.
    """
    r = pearson_correlation(x, y)
    intercept, slope = linear_regression_coefficients(x, y)

    return RegressionResult(
        intercept=intercept,
        slope=slope,
        r=r,
        r_squared=r * r,
    )


# ============================================================================
# 11. OUTLIER SENSITIVITY
# ============================================================================

def demonstrate_outlier_effect() -> None:
    subsection("Outlier sensitivity")

    x = [1, 2, 3, 4, 5, 6, 7]
    y_without_outlier = [2, 4, 6, 8, 10, 12, 14]
    y_with_outlier = [2, 4, 6, 8, 10, 12, 100]

    r_without = pearson_correlation(x, y_without_outlier)
    r_with = pearson_correlation(x, y_with_outlier)

    print(f"Without outlier: r = {r_without:.4f}")
    print(f"With outlier:    r = {r_with:.4f}")

    print(
        "Pearson correlation can change substantially because an extreme "
        "observation affects both centering and cross-products."
    )


# ============================================================================
# 12. NONLINEAR RELATIONSHIPS
# ============================================================================

def demonstrate_nonlinear_relationship() -> None:
    subsection("Nonlinear relationship and correlation")

    x = list(range(-10, 11))
    y = [value * value for value in x]

    pearson = pearson_correlation(x, y)
    spearman = spearman_correlation(x, y)

    print(f"Pearson correlation for y = x^2:  {pearson:.4f}")
    print(f"Spearman correlation for y = x^2: {spearman:.4f}")

    print(
        "The U-shaped relationship is deterministic but is not globally "
        "linear or monotonic. A correlation near zero must not be interpreted "
        "as proof that no relationship exists."
    )


# ============================================================================
# 13. PERFECT POSITIVE AND NEGATIVE RELATIONSHIPS
# ============================================================================

def demonstrate_perfect_relationships() -> None:
    subsection("Perfect relationships")

    x = [1, 2, 3, 4, 5]
    positive = [10, 20, 30, 40, 50]
    negative = [50, 40, 30, 20, 10]

    print(f"Perfect positive: {pearson_correlation(x, positive):.1f}")
    print(f"Perfect negative: {pearson_correlation(x, negative):.1f}")

    print(
        "A value of +1 or -1 indicates perfect linear association in the "
        "observed data. It does not establish causation."
    )


# ============================================================================
# 14. ZERO VARIANCE EDGE CASE
# ============================================================================

def demonstrate_zero_variance() -> None:
    subsection("Zero-variance edge case")

    x = [1, 1, 1, 1]
    y = [2, 3, 4, 5]

    try:
        pearson_correlation(x, y)
    except ValueError as error:
        print(f"Expected error: {error}")


# ============================================================================
# 15. MISSING DATA STRATEGIES
# ============================================================================

def pairwise_complete_cases(
    x: Sequence[Optional[float]],
    y: Sequence[Optional[float]],
) -> tuple[list[float], list[float]]:
    """
    Remove a pair only when at least one corresponding observation is missing.

    This is pairwise complete-case handling for a single pair of variables.
    It does not impute missing values.
    """
    if len(x) != len(y):
        raise ValueError("Variables must have equal lengths.")

    clean_x: list[float] = []
    clean_y: list[float] = []

    for xi, yi in zip(x, y):
        if xi is None or yi is None:
            continue

        clean_x.append(float(xi))
        clean_y.append(float(yi))

    return clean_x, clean_y


# ============================================================================
# 16. BOOTSTRAP CONFIDENCE INTERVAL
# ============================================================================

def bootstrap_correlation_interval(
    x: Sequence[float],
    y: Sequence[float],
    repetitions: int = 5000,
    confidence: float = 0.95,
    seed: int = 42,
) -> tuple[float, float]:
    """
    Estimate a percentile bootstrap confidence interval for Pearson r.

    Bootstrap procedure:
      1. Resample paired observations with replacement.
      2. Calculate r for each bootstrap sample.
      3. Use empirical quantiles.

    This is an estimation technique, not a guarantee that the interval has
    exact finite-sample coverage.
    """
    validate_pairs(x, y)

    if repetitions < 100:
        raise ValueError("Use at least 100 bootstrap repetitions.")
    if not 0 < confidence < 1:
        raise ValueError("Confidence must be between 0 and 1.")

    rng = random.Random(seed)
    pairs = list(zip(x, y))
    estimates: list[float] = []

    for _ in range(repetitions):
        sample = [rng.choice(pairs) for _ in pairs]
        sample_x = [pair[0] for pair in sample]
        sample_y = [pair[1] for pair in sample]

        # Constant bootstrap samples can occasionally occur with small data.
        try:
            estimates.append(pearson_correlation(sample_x, sample_y))
        except ValueError:
            continue

    if not estimates:
        raise ValueError("No valid bootstrap correlation estimates were produced.")

    estimates.sort()

    alpha = 1.0 - confidence
    lower_index = int((alpha / 2) * (len(estimates) - 1))
    upper_index = int((1 - alpha / 2) * (len(estimates) - 1))

    return estimates[lower_index], estimates[upper_index]


# ============================================================================
# 17. PERMUTATION TEST
# ============================================================================

def permutation_correlation_test(
    x: Sequence[float],
    y: Sequence[float],
    repetitions: int = 5000,
    seed: int = 42,
) -> tuple[float, float]:
    """
    Two-sided permutation test for Pearson correlation.

    Null idea:
        If X and Y are unrelated under the chosen exchangeability assumption,
        the pairing between X and Y can be randomly permuted.

    p-value is estimated as:
        (# |permuted r| >= |observed r| + 1) / (repetitions + 1)

    The test depends on the validity of the permutation assumption.
    """
    validate_pairs(x, y)

    if repetitions < 100:
        raise ValueError("Use at least 100 permutations.")

    observed = pearson_correlation(x, y)
    rng = random.Random(seed)
    shuffled_y = list(y)
    extreme = 0

    for _ in range(repetitions):
        rng.shuffle(shuffled_y)
        permuted_r = pearson_correlation(x, shuffled_y)

        if abs(permuted_r) >= abs(observed):
            extreme += 1

    p_value = (extreme + 1) / (repetitions + 1)

    return observed, p_value


# ============================================================================
# 18. FISHER Z TRANSFORMATION
# ============================================================================

def fisher_z_transform(r: float) -> float:
    """
    Fisher's transformation:
        z = 0.5 * ln((1+r)/(1-r))

    It is defined only for -1 < r < 1.
    """
    if not -1 < r < 1:
        raise ValueError("Fisher transformation requires -1 < r < 1.")

    return 0.5 * math.log((1 + r) / (1 - r))


def fisher_z_inverse(z: float) -> float:
    """Inverse Fisher transformation."""
    return math.tanh(z)


def fisher_correlation_confidence_interval(
    r: float,
    sample_size: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """
    Approximate Pearson correlation confidence interval using Fisher z.

    Standard error in z-space:
        SE = 1 / sqrt(n - 3)

    The normal approximation is mainly useful when the sample is sufficiently
    large and the usual assumptions are reasonable.
    """
    if not -1 < r < 1:
        raise ValueError("The correlation must be strictly between -1 and 1.")
    if sample_size <= 3:
        raise ValueError("Sample size must exceed 3.")
    if not 0 < confidence < 1:
        raise ValueError("Confidence must be between 0 and 1.")

    z = fisher_z_transform(r)
    standard_error = 1 / math.sqrt(sample_size - 3)

    # Common normal critical values are approximated for 90%, 95%, and 99%.
    critical_values = {
        0.90: 1.6448536269514722,
        0.95: 1.959963984540054,
        0.99: 2.5758293035489004,
    }

    if confidence not in critical_values:
        raise ValueError("This demonstration supports 0.90, 0.95, and 0.99 confidence.")

    critical = critical_values[confidence]

    lower_z = z - critical * standard_error
    upper_z = z + critical * standard_error

    return fisher_z_inverse(lower_z), fisher_z_inverse(upper_z)


# ============================================================================
# 19. CORRELATION AND SCALE TRANSFORMATIONS
# ============================================================================

def demonstrate_scale_invariance() -> None:
    subsection("Scale transformations")

    x = [1, 2, 3, 4, 5]
    y = [3, 6, 9, 12, 15]

    original = pearson_correlation(x, y)

    transformed_x = [value * 100 + 5000 for value in x]
    transformed_y = [value * -7 + 900 for value in y]

    transformed = pearson_correlation(transformed_x, transformed_y)

    print(f"Original r:   {original:.4f}")
    print(f"Transformed r:{transformed:.4f}")

    print(
        "Positive rescaling and shifting do not change Pearson r. Multiplying "
        "one variable by a negative constant reverses its direction."
    )


# ============================================================================
# 20. CORRELATION IS NOT CAUSATION
# ============================================================================

def demonstrate_spurious_correlation() -> None:
    subsection("Correlation does not establish causation")

    # Both variables increase with a common time-like index. This creates a
    # strong association even though the example contains no causal mechanism
    # from one variable to the other.
    time = list(range(1, 11))
    variable_a = [10 + 2 * t for t in time]
    variable_b = [100 + 5 * t for t in time]

    r = pearson_correlation(variable_a, variable_b)

    print(f"Correlation between two common-trend variables: r = {r:.4f}")
    print(
        "The association can arise because both variables depend on a third "
        "factor or common trend. Correlation alone cannot identify the causal "
        "direction."
    )


# ============================================================================
# 21. SIMPSON'S PARADOX
# ============================================================================

def demonstrate_grouped_correlations() -> None:
    subsection("Grouped data and Simpson's-paradox-style behavior")

    # Two groups can each have one pattern while the combined data exhibit a
    # different pattern because group membership changes the distribution.
    group_a_x = [1, 2, 3, 4, 5]
    group_a_y = [2, 3, 4, 5, 6]

    group_b_x = [10, 11, 12, 13, 14]
    group_b_y = [1, 2, 3, 4, 5]

    combined_x = group_a_x + group_b_x
    combined_y = group_a_y + group_b_y

    print(
        f"Group A correlation: {pearson_correlation(group_a_x, group_a_y):.4f}"
    )
    print(
        f"Group B correlation: {pearson_correlation(group_b_x, group_b_y):.4f}"
    )
    print(
        f"Combined correlation: {pearson_correlation(combined_x, combined_y):.4f}"
    )

    print(
        "Aggregating heterogeneous groups can change the apparent association. "
        "Correlation should be examined alongside relevant subgroup structure."
    )


# ============================================================================
# 22. SYNTHETIC BUSINESS DATA
# ============================================================================

def business_case_study() -> None:
    subsection("Business analytics case study")

    advertising = [12, 15, 17, 20, 22, 25, 27, 30, 34, 36]
    website_visits = [180, 210, 240, 260, 300, 340, 360, 410, 450, 470]
    sales = [25, 30, 32, 39, 43, 49, 52, 60, 67, 70]

    dataset = {
        "Advertising": advertising,
        "WebsiteVisits": website_visits,
        "Sales": sales,
    }

    matrix = correlation_matrix(dataset)
    print_correlation_matrix(matrix)

    regression = simple_linear_regression(advertising, sales)

    print(f"\nSales from advertising:")
    print(f"  slope      = {regression.slope:.4f}")
    print(f"  intercept  = {regression.intercept:.4f}")
    print(f"  r          = {regression.r:.4f}")
    print(f"  R-squared  = {regression.r_squared:.4f}")
    print(f"  predicted sales at advertising=40: {regression.predict(40):.2f}")

    print(
        "\nInterpretation: the observed variables are strongly positively "
        "associated in this synthetic dataset. This alone does not prove that "
        "increasing advertising causes the measured sales increase."
    )


# ============================================================================
# 23. FINANCIAL RETURN CORRELATION
# ============================================================================

def financial_case_study() -> None:
    subsection("Portfolio diversification example")

    asset_a = [0.012, -0.004, 0.008, 0.015, -0.010, 0.006, 0.009, -0.002]
    asset_b = [0.004, 0.003, 0.002, -0.001, 0.005, 0.001, 0.004, 0.002]
    asset_c = [-0.015, 0.009, -0.006, 0.012, 0.011, -0.004, 0.008, -0.010]

    assets = {
        "AssetA": asset_a,
        "AssetB": asset_b,
        "AssetC": asset_c,
    }

    matrix = correlation_matrix(assets)
    print_correlation_matrix(matrix)

    print(
        "\nPortfolio interpretation: lower correlation between asset returns "
        "can provide diversification benefits, but correlation is historical "
        "and can change across market regimes."
    )


# ============================================================================
# 24. TESTING
# ============================================================================

def assert_close(actual: float, expected: float, tolerance: float = 1e-10) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(
            f"Expected {expected}, received {actual}"
        )


def run_tests() -> None:
    subsection("Automated correctness tests")

    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]

    assert_close(pearson_correlation(x, y), 1.0)
    assert_close(pearson_correlation(x, [-2, -4, -6, -8, -10]), -1.0)

    assert_close(
        pearson_correlation_stable(x, y),
        pearson_correlation(x, y),
    )

    ranks = rank_with_ties([30, 10, 20, 20])
    expected_ranks = [4.0, 1.0, 2.5, 2.5]

    for actual, expected in zip(ranks, expected_ranks):
        assert_close(actual, expected)

    assert_close(
        spearman_correlation([1, 2, 3, 4], [10, 20, 30, 40]),
        1.0,
    )

    assert_close(
        kendall_tau([1, 2, 3], [10, 20, 30]),
        1.0,
    )

    clean_x, clean_y = pairwise_complete_cases(
        [1, None, 3, 4],
        [2, 5, None, 8],
    )

    assert clean_x == [1.0, 4.0]
    assert clean_y == [2.0, 8.0]

    regression = simple_linear_regression(x, y)
    assert_close(regression.slope, 2.0)
    assert_close(regression.intercept, 0.0)
    assert_close(regression.r_squared, 1.0)

    print("All tests passed.")


# ============================================================================
# 25. COMMON MISTAKES
# ============================================================================

def common_mistakes_demo() -> None:
    subsection("Common mistakes")

    print("1. Confusing association with causation.")
    print("2. Assuming r near zero means no relationship of any kind.")
    print("3. Ignoring outliers.")
    print("4. Ignoring nonlinear structure.")
    print("5. Reporting a correlation without its sample size and context.")
    print("6. Correlating observations that are not meaningfully paired.")
    print("7. Treating ordinal categories as interval measurements without justification.")
    print("8. Repeatedly testing many correlations without considering multiplicity.")
    print("9. Assuming historical financial correlations remain constant.")
    print("10. Interpreting statistical significance as practical importance.")


# ============================================================================
# 26. MAIN PROGRAM
# ============================================================================

def main() -> None:
    section("Correlation: Measuring Relationships Between Variables")

    subsection("What is correlation?")

    print(
        "Correlation quantifies how variables vary together. A correlation "
        "coefficient is commonly bounded between -1 and +1."
    )
    print(
        "+1 indicates perfect positive linear association, -1 indicates "
        "perfect negative linear association, and 0 indicates no linear "
        "association for Pearson correlation."
    )
    print(
        "Correlation is descriptive. It does not by itself establish a "
        "causal relationship."
    )

    subsection("Basic numerical example")

    study_hours = [1, 2, 3, 4, 5, 6]
    exam_scores = [55, 60, 66, 72, 78, 85]

    covariance = covariance_sample(study_hours, exam_scores)
    correlation = pearson_correlation(study_hours, exam_scores)

    print(f"Study hours: {study_hours}")
    print(f"Exam scores: {exam_scores}")
    print(f"Sample covariance: {covariance:.4f}")
    print(f"Pearson correlation: {correlation:.4f}")
    print(f"Description: {describe_relationship(correlation)}")

    subsection("Pearson, Spearman, and Kendall")

    x = [1, 2, 3, 4, 5, 6]
    y = [2, 3, 5, 7, 11, 13]

    print(f"Pearson r:    {pearson_correlation(x, y):.4f}")
    print(f"Spearman rho: {spearman_correlation(x, y):.4f}")
    print(f"Kendall tau:  {kendall_tau(x, y):.4f}")
    print(f"Kendall tau-b:{kendall_tau_b(x, y):.4f}")

    subsection("Point-biserial correlation")

    completed_training = [0, 0, 1, 1, 1, 0, 1, 0]
    productivity = [62, 65, 70, 75, 80, 64, 83, 61]

    point_biserial = point_biserial_correlation(
        completed_training,
        productivity,
    )

    print(f"Point-biserial correlation: {point_biserial:.4f}")

    subsection("Partial correlation")

    experience = [1, 2, 3, 4, 5, 6, 7, 8]
    training = [2, 3, 4, 4, 6, 7, 8, 9]
    productivity = [50, 54, 60, 61, 69, 73, 77, 82]

    raw_r = pearson_correlation(training, productivity)
    partial_r = partial_correlation(
        training,
        productivity,
        experience,
    )

    print(f"Raw training-productivity r:     {raw_r:.4f}")
    print(f"Partial correlation controlling experience: {partial_r:.4f}")

    demonstrate_perfect_relationships()
    demonstrate_zero_variance()
    demonstrate_outlier_effect()
    demonstrate_nonlinear_relationship()
    demonstrate_scale_invariance()
    demonstrate_spurious_correlation()
    demonstrate_grouped_correlations()

    business_case_study()
    financial_case_study()

    subsection("Bootstrap confidence interval")

    lower, upper = bootstrap_correlation_interval(
        study_hours,
        exam_scores,
        repetitions=3000,
        confidence=0.95,
    )

    print(f"95% bootstrap interval: [{lower:.4f}, {upper:.4f}]")

    subsection("Permutation test")

    observed_r, p_value = permutation_correlation_test(
        study_hours,
        exam_scores,
        repetitions=3000,
    )

    print(f"Observed r: {observed_r:.4f}")
    print(f"Estimated two-sided permutation p-value: {p_value:.4f}")

    subsection("Fisher z transformation")

    r = pearson_correlation(study_hours, exam_scores)
    z = fisher_z_transform(r)
    recovered_r = fisher_z_inverse(z)

    print(f"r:                  {r:.4f}")
    print(f"Fisher z:            {z:.4f}")
    print(f"Inverse transformation: {recovered_r:.4f}")

    if abs(r) < 1:
        lower, upper = fisher_correlation_confidence_interval(
            r,
            sample_size=len(study_hours),
            confidence=0.95,
        )
        print(f"Approximate 95% Fisher-z interval: [{lower:.4f}, {upper:.4f}]")

    common_mistakes_demo()
    run_tests()

    section("End of correlation study")
    print(
        "The central principle is to interpret a correlation coefficient "
        "together with the data structure, measurement scale, sample size, "
        "visual pattern, outliers, uncertainty, and substantive context."
    )


if __name__ == "__main__":
    main()
