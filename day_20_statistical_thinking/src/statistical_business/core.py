# File: src/statistical_business/core.py

from __future__ import annotations

"""Core statistical calculations used by the business decision toolkit.

The implementations intentionally use the Python standard library so that
the statistical mechanics remain visible to learners.
"""

from dataclasses import dataclass
from math import erf, exp, log, sqrt
from statistics import mean, median, pstdev, stdev
from typing import Iterable, Sequence


NumberList = Sequence[float]


class StatisticalError(ValueError):
    """Raised when a statistical calculation cannot be performed."""


def _validate_numeric(values: Iterable[float], minimum: int = 1) -> list[float]:
    data = [float(value) for value in values]
    if len(data) < minimum:
        raise StatisticalError(
            f"At least {minimum} numeric observations are required."
        )
    return data


def describe(values: Iterable[float]) -> dict[str, float]:
    """Return descriptive statistics useful for an initial business diagnosis.

    Mean answers: what is the arithmetic average?
    Median answers: what is the middle observation?
    Standard deviation answers: how dispersed are observations?
    """
    data = _validate_numeric(values, 2)

    return {
        "count": float(len(data)),
        "mean": mean(data),
        "median": median(data),
        "minimum": min(data),
        "maximum": max(data),
        "population_std_dev": pstdev(data),
        "sample_std_dev": stdev(data),
        "range": max(data) - min(data),
    }


def percentile(values: Iterable[float], p: float) -> float:
    """Calculate a linearly interpolated percentile."""
    data = sorted(_validate_numeric(values))
    if not 0 <= p <= 100:
        raise StatisticalError("Percentile must be between 0 and 100.")

    position = (len(data) - 1) * p / 100
    lower = int(position)
    upper = min(lower + 1, len(data) - 1)
    fraction = position - lower
    return data[lower] + (data[upper] - data[lower]) * fraction


def covariance(x: Iterable[float], y: Iterable[float]) -> float:
    """Calculate sample covariance."""
    first = _validate_numeric(x, 2)
    second = _validate_numeric(y, 2)
    if len(first) != len(second):
        raise StatisticalError("Both series must contain the same number of observations.")

    x_bar = mean(first)
    y_bar = mean(second)
    return sum((a - x_bar) * (b - y_bar) for a, b in zip(first, second)) / (
        len(first) - 1
    )


def correlation(x: Iterable[float], y: Iterable[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    first = _validate_numeric(x, 2)
    second = _validate_numeric(y, 2)

    if len(first) != len(second):
        raise StatisticalError("Both series must contain the same number of observations.")

    x_std = stdev(first)
    y_std = stdev(second)

    if x_std == 0 or y_std == 0:
        raise StatisticalError("Correlation is undefined when a series has zero variance.")

    return covariance(first, second) / (x_std * y_std)


@dataclass(frozen=True)
class LinearRegression:
    """Simple least-squares regression model y = intercept + slope*x."""

    slope: float
    intercept: float
    r_squared: float

    def predict(self, x: float) -> float:
        return self.intercept + self.slope * x


def linear_regression(x: Iterable[float], y: Iterable[float]) -> LinearRegression:
    """Fit a simple linear regression model."""
    first = _validate_numeric(x, 2)
    second = _validate_numeric(y, 2)

    if len(first) != len(second):
        raise StatisticalError("Both series must contain the same number of observations.")

    x_bar = mean(first)
    y_bar = mean(second)
    denominator = sum((value - x_bar) ** 2 for value in first)

    if denominator == 0:
        raise StatisticalError("Regression requires variation in the predictor.")

    slope = sum(
        (a - x_bar) * (b - y_bar) for a, b in zip(first, second)
    ) / denominator
    intercept = y_bar - slope * x_bar

    predictions = [intercept + slope * value for value in first]
    ss_total = sum((value - y_bar) ** 2 for value in second)
    ss_residual = sum(
        (actual - predicted) ** 2
        for actual, predicted in zip(second, predictions)
    )

    r_squared = 1.0 if ss_total == 0 and ss_residual == 0 else (
        1 - ss_residual / ss_total if ss_total else 0.0
    )

    return LinearRegression(slope, intercept, r_squared)


def _normal_cdf(z: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1 + erf(z / sqrt(2)))


def proportion_confidence_interval(
    successes: int,
    sample_size: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Calculate a Wald confidence interval for a population proportion.

    This is useful for teaching uncertainty, but production experimentation
    systems should consider Wilson or exact intervals for small samples.
    """
    if sample_size <= 0:
        raise StatisticalError("Sample size must be positive.")
    if successes < 0 or successes > sample_size:
        raise StatisticalError("Successes must be between zero and sample size.")
    if not 0 < confidence < 1:
        raise StatisticalError("Confidence must be between zero and one.")

    proportion = successes / sample_size
    z = 1.96 if confidence == 0.95 else _normal_quantile((1 + confidence) / 2)
    standard_error = sqrt(proportion * (1 - proportion) / sample_size)

    return (
        max(0.0, proportion - z * standard_error),
        min(1.0, proportion + z * standard_error),
    )


def _normal_quantile(p: float) -> float:
    """Approximate inverse normal CDF using the Acklam rational approximation."""
    if not 0 < p < 1:
        raise StatisticalError("Probability must be between zero and one.")

    a = [
        -39.6968302866538,
        220.946098424521,
        -275.928510446969,
        138.357751867269,
        -30.6647980661472,
        2.50662827745924,
    ]
    b = [
        -54.4760987982241,
        161.585836858041,
        -155.698979859887,
        66.8013118877197,
        -13.2806815528857,
    ]
    c = [
        -0.00778489400243029,
        -0.322396458041136,
        -2.40075827716184,
        -2.54973253934373,
        4.37466414146497,
        2.93816398269878,
    ]
    d = [
        0.00778469570904146,
        0.32246712907004,
        2.445134137143,
        3.75440866190742,
    ]

    if p < 0.02425:
        q = sqrt(-2 * log(p))
        return (
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        )

    if p > 1 - 0.02425:
        q = sqrt(-2 * log(1 - p))
        return -(
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        )

    q = p - 0.5
    r = q * q
    return (
        (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
        / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    )


def two_proportion_z_test(
    successes_a: int,
    size_a: int,
    successes_b: int,
    size_b: int,
) -> dict[str, float]:
    """Compare two independent proportions with a two-sided z test.

    Null hypothesis: the two population conversion proportions are equal.
    """
    if min(size_a, size_b) <= 0:
        raise StatisticalError("Sample sizes must be positive.")
    if not 0 <= successes_a <= size_a or not 0 <= successes_b <= size_b:
        raise StatisticalError("Successes must lie within their sample sizes.")

    p_a = successes_a / size_a
    p_b = successes_b / size_b
    pooled = (successes_a + successes_b) / (size_a + size_b)

    standard_error = sqrt(
        pooled * (1 - pooled) * (1 / size_a + 1 / size_b)
    )

    if standard_error == 0:
        raise StatisticalError("The pooled standard error is zero.")

    z = (p_b - p_a) / standard_error
    p_value = 2 * (1 - _normal_cdf(abs(z)))

    return {
        "proportion_a": p_a,
        "proportion_b": p_b,
        "absolute_difference": p_b - p_a,
        "relative_change": (p_b - p_a) / p_a if p_a else float("inf"),
        "z_statistic": z,
        "p_value": p_value,
    }


def expected_value(outcomes: Iterable[tuple[float, float]]) -> float:
    """Calculate expected monetary value from outcome/probability pairs."""
    pairs = list(outcomes)
    if not pairs:
        raise StatisticalError("At least one outcome is required.")

    probability_total = sum(probability for _, probability in pairs)
    if abs(probability_total - 1) > 1e-9:
        raise StatisticalError("Probabilities must sum to one.")

    if any(probability < 0 for _, probability in pairs):
        raise StatisticalError("Probabilities cannot be negative.")

    return sum(value * probability for value, probability in pairs)


def moving_average(values: Iterable[float], window: int) -> list[float]:
    """Calculate a simple moving average for a time series."""
    data = _validate_numeric(values, window)
    if window <= 0:
        raise StatisticalError("Window must be positive.")
    if window > len(data):
        raise StatisticalError("Window cannot exceed the number of observations.")

    return [
        mean(data[index : index + window])
        for index in range(len(data) - window + 1)
    ]

