"""
Percentiles & Quartiles: Distribution Analysis and Business Interpretation

A self-contained educational script covering:
- Descriptive statistics foundations
- Percentiles and quartiles
- Multiple percentile calculation conventions
- Interpolation
- Five-number summary
- IQR and outlier detection
- Distribution shape and skewness
- Business interpretation
- Group comparisons
- Weighted percentiles
- Empirical CDF
- Robust statistics
- Sensitivity analysis
- Performance considerations
- Validation and testing
- Practical business case studies

The script uses only Python's standard library.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean, median
from typing import Iterable, Sequence


# ============================================================
# 1. FOUNDATIONS
# ============================================================

def validate_numeric_data(data: Iterable[float]) -> list[float]:
    """
    Convert an iterable into a sorted list of finite numeric values.

    Percentiles require an ordered numerical variable. Missing values,
    infinities, and non-numeric observations are rejected explicitly
    rather than silently producing misleading results.
    """
    values = list(data)

    if not values:
        raise ValueError("The dataset must contain at least one observation.")

    cleaned: list[float] = []

    for value in values:
        if isinstance(value, bool):
            raise TypeError("Boolean values are not valid numerical observations.")

        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"Non-numeric value encountered: {value!r}") from exc

        if numeric_value != numeric_value:
            raise ValueError("NaN values are not supported.")

        if numeric_value in (float("inf"), float("-inf")):
            raise ValueError("Infinite values are not supported.")

        cleaned.append(numeric_value)

    return sorted(cleaned)


def population_variance(data: Sequence[float]) -> float:
    """Calculate population variance."""
    values = validate_numeric_data(data)
    center = mean(values)
    return sum((x - center) ** 2 for x in values) / len(values)


def population_std(data: Sequence[float]) -> float:
    """Calculate population standard deviation."""
    return sqrt(population_variance(data))


def describe_basic(data: Sequence[float]) -> dict[str, float]:
    """Return basic descriptive statistics."""
    values = validate_numeric_data(data)

    return {
        "count": len(values),
        "minimum": values[0],
        "maximum": values[-1],
        "mean": mean(values),
        "median": median(values),
        "standard_deviation": population_std(values),
    }


# ============================================================
# 2. PERCENTILE CONCEPT
# ============================================================

def percentile_nearest_rank(data: Sequence[float], percentile: float) -> float:
    """
    Calculate a percentile using the nearest-rank method.

    For p in [0, 100]:
        rank = ceil(p / 100 * n)

    The rank is bounded to [1, n].

    This method is easy to explain but differs from interpolated
    percentile definitions commonly used by statistical software.
    """
    values = validate_numeric_data(data)

    if not 0 <= percentile <= 100:
        raise ValueError("Percentile must be between 0 and 100.")

    if percentile == 0:
        return values[0]

    from math import ceil

    rank = ceil(percentile / 100 * len(values))
    return values[rank - 1]


def percentile_linear(data: Sequence[float], percentile: float) -> float:
    """
    Calculate an interpolated percentile using the common
    (n - 1) * p positional convention.

    Position:
        h = (n - 1) * p

    where p is percentile / 100.

    If h lies between two observations, linear interpolation is used.
    """
    values = validate_numeric_data(data)

    if not 0 <= percentile <= 100:
        raise ValueError("Percentile must be between 0 and 100.")

    if len(values) == 1:
        return values[0]

    p = percentile / 100
    position = (len(values) - 1) * p

    lower_index = int(position)
    upper_index = min(lower_index + 1, len(values) - 1)
    fraction = position - lower_index

    lower_value = values[lower_index]
    upper_value = values[upper_index]

    return lower_value + fraction * (upper_value - lower_value)


def percentile_hazen(data: Sequence[float], percentile: float) -> float:
    """
    Calculate a percentile using the Hazen plotting-position convention.

    Position:
        h = (n + 1) * p

    Boundary behavior is clipped to the minimum and maximum.
    """
    values = validate_numeric_data(data)

    if not 0 <= percentile <= 100:
        raise ValueError("Percentile must be between 0 and 100.")

    if len(values) == 1:
        return values[0]

    p = percentile / 100
    position = (len(values) + 1) * p

    if position <= 1:
        return values[0]

    if position >= len(values):
        return values[-1]

    lower_index = int(position) - 1
    upper_index = lower_index + 1
    fraction = position - int(position)

    return (
        values[lower_index]
        + fraction * (values[upper_index] - values[lower_index])
    )


def percentile(data: Sequence[float], percentile_value: float) -> float:
    """
    Public default percentile implementation.

    The linear interpolation convention is used because it gives
    useful continuous estimates for distribution analysis.
    """
    return percentile_linear(data, percentile_value)


# ============================================================
# 3. QUARTILES
# ============================================================

def quartiles(data: Sequence[float]) -> dict[str, float]:
    """
    Calculate Q1, Q2, and Q3.

    Q1 = 25th percentile
    Q2 = 50th percentile, the median
    Q3 = 75th percentile
    """
    return {
        "Q1": percentile(data, 25),
        "Q2": percentile(data, 50),
        "Q3": percentile(data, 75),
    }


def five_number_summary(data: Sequence[float]) -> dict[str, float]:
    """
    Return the five-number summary:
    minimum, Q1, median, Q3, maximum.
    """
    values = validate_numeric_data(data)
    qs = quartiles(values)

    return {
        "minimum": values[0],
        "Q1": qs["Q1"],
        "median": qs["Q2"],
        "Q3": qs["Q3"],
        "maximum": values[-1],
    }


# ============================================================
# 4. INTERQUARTILE RANGE AND OUTLIERS
# ============================================================

def interquartile_range(data: Sequence[float]) -> float:
    """Calculate IQR = Q3 - Q1."""
    qs = quartiles(data)
    return qs["Q3"] - qs["Q1"]


def iqr_outlier_fences(
    data: Sequence[float],
    multiplier: float = 1.5,
) -> tuple[float, float]:
    """
    Calculate Tukey-style lower and upper fences.

    Lower fence = Q1 - multiplier * IQR
    Upper fence = Q3 + multiplier * IQR

    The common multiplier is 1.5. A value outside the fences is
    conventionally classified as a potential outlier.
    """
    if multiplier < 0:
        raise ValueError("The multiplier cannot be negative.")

    qs = quartiles(data)
    iqr = qs["Q3"] - qs["Q1"]

    return (
        qs["Q1"] - multiplier * iqr,
        qs["Q3"] + multiplier * iqr,
    )


def detect_iqr_outliers(data: Sequence[float]) -> dict[str, object]:
    """Return potential outliers and the associated IQR fences."""
    values = validate_numeric_data(data)
    lower, upper = iqr_outlier_fences(values)

    outliers = [x for x in values if x < lower or x > upper]

    return {
        "lower_fence": lower,
        "upper_fence": upper,
        "outliers": outliers,
        "outlier_count": len(outliers),
    }


# ============================================================
# 5. DISTRIBUTION SEGMENTS
# ============================================================

def percentile_rank(data: Sequence[float], value: float) -> float:
    """
    Estimate the percentage of observations less than or equal to value.

    This is an empirical percentile rank, not an assumption of
    normality or any theoretical probability distribution.
    """
    values = validate_numeric_data(data)
    count = sum(x <= value for x in values)
    return 100 * count / len(values)


def observations_between_percentiles(
    data: Sequence[float],
    lower_percentile: float,
    upper_percentile: float,
) -> dict[str, float]:
    """
    Calculate the value interval and approximate share represented
    by a percentile range.
    """
    if lower_percentile > upper_percentile:
        raise ValueError("Lower percentile cannot exceed upper percentile.")

    lower_value = percentile(data, lower_percentile)
    upper_value = percentile(data, upper_percentile)

    return {
        "lower_percentile": lower_percentile,
        "upper_percentile": upper_percentile,
        "lower_value": lower_value,
        "upper_value": upper_value,
        "percentile_width": upper_percentile - lower_percentile,
    }


def quartile_distribution(data: Sequence[float]) -> dict[str, tuple[float, float]]:
    """
    Return the value ranges corresponding to the four quartile regions.
    """
    values = validate_numeric_data(data)

    q = quartiles(values)

    return {
        "Q1_region": (values[0], q["Q1"]),
        "Q2_region": (q["Q1"], q["Q2"]),
        "Q3_region": (q["Q2"], q["Q3"]),
        "Q4_region": (q["Q3"], values[-1]),
    }


# ============================================================
# 6. DISTRIBUTION SPREAD AND SKEWNESS
# ============================================================

def pearson_second_skewness(data: Sequence[float]) -> float:
    """
    Calculate Pearson's second coefficient of skewness:

        3 * (mean - median) / standard deviation

    This is a descriptive measure. It should not be treated as
    proof of a particular underlying probability distribution.
    """
    values = validate_numeric_data(data)
    std = population_std(values)

    if std == 0:
        return 0.0

    return 3 * (mean(values) - median(values)) / std


def bowley_skewness(data: Sequence[float]) -> float:
    """
    Calculate Bowley's quartile skewness:

        (Q3 + Q1 - 2Q2) / (Q3 - Q1)

    It is based on quartiles and therefore less sensitive to extreme
    observations than many moment-based measures.
    """
    q = quartiles(data)
    denominator = q["Q3"] - q["Q1"]

    if denominator == 0:
        return 0.0

    return (q["Q3"] + q["Q1"] - 2 * q["Q2"]) / denominator


def classify_skewness(value: float, threshold: float = 0.1) -> str:
    """Provide a simple descriptive interpretation of skewness."""
    if value > threshold:
        return "positively skewed (longer right tail)"
    if value < -threshold:
        return "negatively skewed (longer left tail)"
    return "approximately symmetric by this threshold"


# ============================================================
# 7. PERCENTILE TABLE
# ============================================================

def percentile_table(
    data: Sequence[float],
    percentiles: Sequence[float],
) -> list[tuple[float, float]]:
    """Create a percentile-to-value table."""
    return [
        (p, percentile(data, p))
        for p in percentiles
    ]


def print_percentile_table(
    data: Sequence[float],
    percentiles: Sequence[float],
) -> None:
    """Print a readable percentile table."""
    print("\nPercentile table")
    print("-" * 32)
    print(f"{'Percentile':>12} | {'Value':>12}")
    print("-" * 32)

    for p, value in percentile_table(data, percentiles):
        print(f"{p:>11.1f}% | {value:>12.2f}")


# ============================================================
# 8. BUSINESS INTERPRETATION
# ============================================================

def business_interpretation(
    data: Sequence[float],
    metric_name: str,
    higher_is_better: bool = True,
) -> list[str]:
    """
    Produce practical business interpretations from percentiles.

    The interpretation depends on the meaning of the metric.
    For costs or response times, lower values may be better.
    For revenue or customer lifetime value, higher values may be better.
    """
    values = validate_numeric_data(data)
    q = quartiles(values)
    p90 = percentile(values, 90)
    p95 = percentile(values, 95)
    p99 = percentile(values, 99)

    iqr = q["Q3"] - q["Q1"]

    if higher_is_better:
        performance_direction = "higher"
    else:
        performance_direction = "lower"

    return [
        f"{metric_name}: the median is {q['Q2']:.2f}, so half of observations "
        f"are at or below this value.",
        f"The middle 50% lies between {q['Q1']:.2f} and {q['Q3']:.2f}.",
        f"The interquartile range is {iqr:.2f}, describing the spread of the "
        f"central half of observations.",
        f"The 90th percentile is {p90:.2f}, useful for understanding "
        f"high-end performance or exposure.",
        f"The 95th percentile is {p95:.2f}, often useful for service-level "
        f"and risk-oriented analysis.",
        f"The 99th percentile is {p99:.2f}, highlighting extreme but "
        f"still observed performance levels.",
        f"For this metric, {performance_direction} values represent the "
        f"preferred direction under the supplied business assumption.",
    ]


# ============================================================
# 9. GROUP COMPARISON
# ============================================================

@dataclass
class DistributionProfile:
    """Structured description of a business metric distribution."""

    name: str
    count: int
    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float
    iqr: float
    p90: float
    p95: float
    p99: float

    @classmethod
    def from_data(cls, name: str, data: Sequence[float]) -> "DistributionProfile":
        values = validate_numeric_data(data)
        summary = five_number_summary(values)

        return cls(
            name=name,
            count=len(values),
            minimum=summary["minimum"],
            q1=summary["Q1"],
            median=summary["median"],
            q3=summary["Q3"],
            maximum=summary["maximum"],
            iqr=interquartile_range(values),
            p90=percentile(values, 90),
            p95=percentile(values, 95),
            p99=percentile(values, 99),
        )

    def as_dict(self) -> dict[str, float | int | str]:
        """Convert the profile to a dictionary."""
        return {
            "name": self.name,
            "count": self.count,
            "minimum": self.minimum,
            "Q1": self.q1,
            "median": self.median,
            "Q3": self.q3,
            "maximum": self.maximum,
            "IQR": self.iqr,
            "P90": self.p90,
            "P95": self.p95,
            "P99": self.p99,
        }


def compare_groups(
    groups: dict[str, Sequence[float]],
) -> list[DistributionProfile]:
    """Build comparable distribution profiles for multiple groups."""
    return [
        DistributionProfile.from_data(name, data)
        for name, data in groups.items()
    ]


def print_group_comparison(
    groups: dict[str, Sequence[float]],
) -> None:
    """Print key distribution statistics for several groups."""
    profiles = compare_groups(groups)

    print("\nGroup comparison")
    print("-" * 90)
    print(
        f"{'Group':<18}"
        f"{'Median':>12}"
        f"{'Q1':>12}"
        f"{'Q3':>12}"
        f"{'IQR':>12}"
        f"{'P95':>12}"
    )
    print("-" * 90)

    for profile in profiles:
        print(
            f"{profile.name:<18}"
            f"{profile.median:>12.2f}"
            f"{profile.q1:>12.2f}"
            f"{profile.q3:>12.2f}"
            f"{profile.iqr:>12.2f}"
            f"{profile.p95:>12.2f}"
        )


# ============================================================
# 10. WEIGHTED PERCENTILES
# ============================================================

def weighted_percentile(
    data: Sequence[float],
    weights: Sequence[float],
    percentile_value: float,
) -> float:
    """
    Calculate a weighted percentile using cumulative weights.

    Each observation contributes according to its non-negative weight.
    This is useful when observations represent different population sizes,
    exposures, transaction volumes, or sampling weights.
    """
    if len(data) != len(weights):
        raise ValueError("Data and weights must have the same length.")

    if not data:
        raise ValueError("The dataset cannot be empty.")

    if not 0 <= percentile_value <= 100:
        raise ValueError("Percentile must be between 0 and 100.")

    pairs = []

    for value, weight in zip(data, weights):
        numeric_value = float(value)
        numeric_weight = float(weight)

        if numeric_weight < 0:
            raise ValueError("Weights cannot be negative.")

        pairs.append((numeric_value, numeric_weight))

    pairs.sort(key=lambda pair: pair[0])

    total_weight = sum(weight for _, weight in pairs)

    if total_weight <= 0:
        raise ValueError("At least one weight must be positive.")

    target = percentile_value / 100 * total_weight
    cumulative = 0.0

    for value, weight in pairs:
        cumulative += weight
        if cumulative >= target:
            return value

    return pairs[-1][0]


# ============================================================
# 11. EMPIRICAL CUMULATIVE DISTRIBUTION
# ============================================================

def empirical_cdf(data: Sequence[float], value: float) -> float:
    """
    Calculate the empirical CDF at a given value.

    F(x) = P(X <= x) estimated as:
        number of observations <= x / total observations
    """
    values = validate_numeric_data(data)
    return sum(x <= value for x in values) / len(values)


def empirical_cdf_table(
    data: Sequence[float],
) -> list[tuple[float, float]]:
    """Return each distinct observed value with its empirical CDF."""
    values = validate_numeric_data(data)

    result = []

    for value in sorted(set(values)):
        result.append((value, empirical_cdf(values, value)))

    return result


# ============================================================
# 12. ROBUST STATISTICS
# ============================================================

def trimmed_mean(data: Sequence[float], trim_fraction: float = 0.1) -> float:
    """
    Calculate a symmetric trimmed mean.

    A 0.1 trim fraction removes approximately 10% from each tail.
    Trimming can reduce the influence of extreme observations.
    """
    values = validate_numeric_data(data)

    if not 0 <= trim_fraction < 0.5:
        raise ValueError("Trim fraction must be in [0, 0.5).")

    trim_count = int(len(values) * trim_fraction)

    if 2 * trim_count >= len(values):
        raise ValueError("Trimming would remove all observations.")

    remaining = values[trim_count:len(values) - trim_count]

    return mean(remaining)


def winsorized_data(
    data: Sequence[float],
    lower_percentile: float = 5,
    upper_percentile: float = 95,
) -> list[float]:
    """
    Winsorize observations by replacing extreme values with
    percentile boundary values.

    Unlike trimming, observations remain in the dataset.
    """
    if lower_percentile > upper_percentile:
        raise ValueError("Lower percentile cannot exceed upper percentile.")

    values = validate_numeric_data(data)
    lower = percentile(values, lower_percentile)
    upper = percentile(values, upper_percentile)

    return [
        min(max(value, lower), upper)
        for value in values
    ]


# ============================================================
# 13. SENSITIVITY TO EXTREME VALUES
# ============================================================

def compare_before_after_extreme_value(
    data: Sequence[float],
    extreme_value: float,
) -> dict[str, dict[str, float]]:
    """
    Compare mean, median, Q1, Q3, and P95 before and after
    adding an extreme observation.

    This demonstrates why business analysts should not automatically
    use the mean as the only description of a skewed distribution.
    """
    original = validate_numeric_data(data)
    modified = original + [float(extreme_value)]

    return {
        "original": {
            "mean": mean(original),
            "median": median(original),
            "Q1": percentile(original, 25),
            "Q3": percentile(original, 75),
            "P95": percentile(original, 95),
        },
        "with_extreme_value": {
            "mean": mean(modified),
            "median": median(modified),
            "Q1": percentile(modified, 25),
            "Q3": percentile(modified, 75),
            "P95": percentile(modified, 95),
        },
    }


# ============================================================
# 14. BUSINESS CASE STUDY: DELIVERY TIMES
# ============================================================

def delivery_time_case_study() -> None:
    """
    Analyze delivery times.

    Lower delivery time is better, but high percentiles are important
    because a small group of customers may experience severe delays.
    """
    delivery_times = [
        18, 20, 21, 22, 22, 23, 24, 24, 25, 26,
        27, 27, 28, 29, 30, 31, 31, 32, 33, 34,
        35, 36, 38, 40, 42, 45, 48, 52, 60, 90,
    ]

    print("\n" + "=" * 70)
    print("BUSINESS CASE: DELIVERY TIMES")
    print("=" * 70)

    summary = five_number_summary(delivery_times)

    for key, value in summary.items():
        print(f"{key:>10}: {value:.2f} minutes")

    for p in (50, 75, 90, 95, 99):
        print(
            f"P{p}: {percentile(delivery_times, p):.2f} minutes"
        )

    print("\nInterpretation:")
    for statement in business_interpretation(
        delivery_times,
        "Delivery time",
        higher_is_better=False,
    ):
        print("-", statement)

    outliers = detect_iqr_outliers(delivery_times)

    print("\nPotential IQR outliers:")
    print(outliers["outliers"])

    print(
        "\nBusiness implication: reporting only the average delivery time "
        "can hide poor experiences in the upper tail. P90, P95, and P99 "
        "show the customer experience among slower deliveries."
    )


# ============================================================
# 15. BUSINESS CASE STUDY: CUSTOMER SPEND
# ============================================================

def customer_spend_case_study() -> None:
    """
    Analyze customer annual spending.

    Customer spending often has a right-skewed distribution because
    a relatively small group of customers can spend substantially more.
    """
    spending = [
        120, 140, 155, 180, 190, 210, 220, 240, 250, 275,
        290, 310, 325, 350, 375, 400, 430, 460, 500, 550,
        600, 700, 850, 1000, 1300, 1800, 2500, 4200, 8000, 15000,
    ]

    print("\n" + "=" * 70)
    print("BUSINESS CASE: CUSTOMER ANNUAL SPEND")
    print("=" * 70)

    print(f"Mean:   {mean(spending):.2f}")
    print(f"Median: {median(spending):.2f}")

    q = quartiles(spending)

    print(f"Q1:     {q['Q1']:.2f}")
    print(f"Q3:     {q['Q3']:.2f}")
    print(f"IQR:    {interquartile_range(spending):.2f}")

    skew = bowley_skewness(spending)

    print(f"Bowley skewness: {skew:.3f}")
    print(f"Distribution: {classify_skewness(skew)}")

    print(
        "\nBusiness interpretation: the median is usually a better "
        "description of the typical customer than the mean when a small "
        "number of high-spending customers strongly influence the average."
    )


# ============================================================
# 16. BUSINESS CASE STUDY: EMPLOYEE COMPENSATION
# ============================================================

def salary_case_study() -> None:
    """
    Analyze salaries across a workforce.

    Percentiles can support compensation benchmarking and help identify
    where employees fall within an internal salary distribution.
    """
    salaries = [
        28000, 30000, 32000, 34000, 35000,
        36000, 38000, 40000, 42000, 45000,
        47000, 49000, 52000, 55000, 58000,
        62000, 68000, 72000, 85000, 120000,
    ]

    print("\n" + "=" * 70)
    print("BUSINESS CASE: EMPLOYEE SALARIES")
    print("=" * 70)

    for p in (10, 25, 50, 75, 90):
        value = percentile(salaries, p)
        print(f"P{p:>2}: {value:,.0f}")

    employee_salary = 70000
    rank = percentile_rank(salaries, employee_salary)

    print(
        f"\nA salary of {employee_salary:,.0f} is at or below "
        f"approximately {rank:.1f}% of the observed salaries."
    )

    print(
        "\nImportant distinction: percentile rank describes relative "
        "position within this dataset. It does not prove whether a salary "
        "is fair, competitive, or appropriate without external context."
    )


# ============================================================
# 17. BUSINESS CASE STUDY: WEBSITE RESPONSE TIME
# ============================================================

def response_time_case_study() -> None:
    """
    Analyze application response times.

    Tail percentiles are especially important for system performance.
    """
    response_times = [
        80, 82, 85, 87, 90, 92, 95, 97, 100, 105,
        108, 110, 115, 120, 125, 130, 140, 155, 180, 250,
    ]

    print("\n" + "=" * 70)
    print("BUSINESS CASE: WEBSITE RESPONSE TIME")
    print("=" * 70)

    for p in (50, 90, 95, 99):
        print(
            f"P{p}: {percentile(response_times, p):.2f} ms"
        )

    print(
        "\nOperational interpretation:"
        "\n- P50 describes the typical observed request."
        "\n- P90 describes slower requests experienced by roughly the top 10%."
        "\n- P95 focuses on a more demanding service-performance threshold."
        "\n- P99 exposes the extreme tail and can reveal operational problems "
        "that averages hide."
    )


# ============================================================
# 18. QUARTILE-BASED SEGMENTATION
# ============================================================

def assign_quartile_segment(
    data: Sequence[float],
    value: float,
) -> str:
    """
    Assign an observation to a quartile-based segment.

    Boundary conventions are explicitly defined using <= comparisons.
    """
    q = quartiles(data)

    if value <= q["Q1"]:
        return "Q1: bottom 25% region"
    if value <= q["Q2"]:
        return "Q2: 25%-50% region"
    if value <= q["Q3"]:
        return "Q3: 50%-75% region"
    return "Q4: top 25% region"


# ============================================================
# 19. PERCENTILE-BASED BUSINESS SEGMENTATION
# ============================================================

def percentile_segment(
    data: Sequence[float],
    value: float,
) -> str:
    """
    Assign a value to practical percentile bands.

    This can support customer segmentation, risk tiers, and
    performance classification.
    """
    if value <= percentile(data, 25):
        return "0-25th percentile"
    if value <= percentile(data, 50):
        return "25th-50th percentile"
    if value <= percentile(data, 75):
        return "50th-75th percentile"
    if value <= percentile(data, 90):
        return "75th-90th percentile"
    if value <= percentile(data, 95):
        return "90th-95th percentile"
    return "above the 95th percentile"


# ============================================================
# 20. EDGE CASES
# ============================================================

def demonstrate_edge_cases() -> None:
    """Demonstrate important boundary conditions."""
    print("\n" + "=" * 70)
    print("EDGE CASES")
    print("=" * 70)

    cases = {
        "single observation": [42],
        "two observations": [10, 20],
        "identical values": [5, 5, 5, 5],
        "negative values": [-20, -10, -5, 0, 10, 20],
        "already unsorted": [50, 10, 40, 20, 30],
    }

    for name, data in cases.items():
        print(f"\n{name}: {data}")
        print(f"Q1={percentile(data, 25):.2f}")
        print(f"Median={percentile(data, 50):.2f}")
        print(f"Q3={percentile(data, 75):.2f}")

    print(
        "\nImportant: a percentile is not necessarily one of the original "
        "observed values when interpolation is used."
    )


# ============================================================
# 21. INVALID INPUTS
# ============================================================

def demonstrate_validation() -> None:
    """Show how invalid percentile and dataset inputs are handled."""
    print("\n" + "=" * 70)
    print("VALIDATION AND ERROR HANDLING")
    print("=" * 70)

    invalid_examples = [
        ("empty dataset", lambda: percentile([], 50)),
        ("invalid percentile", lambda: percentile([1, 2, 3], 110)),
        ("NaN", lambda: percentile([1, float("nan"), 3], 50)),
        ("infinity", lambda: percentile([1, float("inf"), 3], 50)),
        ("text", lambda: percentile([1, "abc", 3], 50)),
    ]

    for name, operation in invalid_examples:
        try:
            operation()
        except (ValueError, TypeError) as error:
            print(f"{name}: correctly rejected -> {error}")


# ============================================================
# 22. METHOD COMPARISON
# ============================================================

def compare_percentile_methods(data: Sequence[float]) -> None:
    """
    Compare different percentile definitions.

    Different statistical software and standards may use different
    quantile conventions. Analysts must document their method when
    reproducibility matters.
    """
    print("\n" + "=" * 70)
    print("PERCENTILE METHOD COMPARISON")
    print("=" * 70)

    print(f"{'Percentile':>12} | {'Nearest Rank':>15} | {'Linear':>15} | {'Hazen':>15}")
    print("-" * 65)

    for p in (10, 25, 50, 75, 90):
        nearest = percentile_nearest_rank(data, p)
        linear = percentile_linear(data, p)
        hazen = percentile_hazen(data, p)

        print(
            f"{p:>11}% | "
            f"{nearest:>15.2f} | "
            f"{linear:>15.2f} | "
            f"{hazen:>15.2f}"
        )


# ============================================================
# 23. BUSINESS METRIC DIAGNOSTICS
# ============================================================

def distribution_diagnostics(data: Sequence[float]) -> dict[str, object]:
    """
    Produce a compact distribution diagnostic report.

    This combines central tendency, spread, tail percentiles,
    outlier detection, and skewness.
    """
    values = validate_numeric_data(data)
    q = quartiles(values)
    iqr = interquartile_range(values)
    outliers = detect_iqr_outliers(values)
    bowley = bowley_skewness(values)

    return {
        "count": len(values),
        "minimum": values[0],
        "Q1": q["Q1"],
        "median": q["Q2"],
        "Q3": q["Q3"],
        "maximum": values[-1],
        "IQR": iqr,
        "P90": percentile(values, 90),
        "P95": percentile(values, 95),
        "P99": percentile(values, 99),
        "mean": mean(values),
        "standard_deviation": population_std(values),
        "Bowley_skewness": bowley,
        "skewness_interpretation": classify_skewness(bowley),
        "potential_outliers": outliers["outliers"],
    }


def print_diagnostics(data: Sequence[float]) -> None:
    """Print distribution diagnostics."""
    report = distribution_diagnostics(data)

    print("\nDistribution diagnostics")
    print("-" * 45)

    for key, value in report.items():
        print(f"{key:<25}: {value}")


# ============================================================
# 24. UNIT TESTS
# ============================================================

def run_tests() -> None:
    """
    Basic tests for the core percentile implementation.

    These tests are deliberately small and readable so learners can
    inspect the expected mathematical behavior.
    """
    data = [10, 20, 30, 40, 50]

    assert percentile(data, 0) == 10
    assert percentile(data, 50) == 30
    assert percentile(data, 100) == 50

    assert percentile(data, 25) == 20
    assert percentile(data, 75) == 40

    assert interquartile_range(data) == 20

    assert percentile([5], 10) == 5
    assert percentile([5], 90) == 5

    assert percentile([10, 20], 25) == 12.5
    assert percentile([10, 20], 75) == 17.5

    try:
        percentile([], 50)
        raise AssertionError("Empty data should fail.")
    except ValueError:
        pass

    try:
        percentile(data, -1)
        raise AssertionError("Negative percentile should fail.")
    except ValueError:
        pass

    print("\nAll core tests passed.")


# ============================================================
# 25. PERFORMANCE CONSIDERATIONS
# ============================================================

def performance_note() -> None:
    """
    Explain computational considerations.

    Sorting is the dominant operation in the simple implementation.
    For n observations:
        sorting: O(n log n)
        percentile lookup after sorting: O(1)

    This is appropriate for educational and moderate-sized datasets.
    Production systems handling very large or streaming datasets may
    require specialized approximate quantile algorithms.
    """
    print("\n" + "=" * 70)
    print("PERFORMANCE CONSIDERATIONS")
    print("=" * 70)

    print("The implementation sorts the data before calculating percentiles.")
    print("Typical sorting complexity: O(n log n).")
    print("A percentile lookup after sorting is approximately O(1).")
    print(
        "Repeated percentile calls currently re-sort the dataset because "
        "the public functions validate and sort their input."
    )
    print(
        "For production workloads, sort once and reuse the ordered data, "
        "or use a quantile implementation optimized for the workload."
    )
    print(
        "For massive streaming datasets, approximate quantile algorithms "
        "can trade a small amount of accuracy for substantially lower "
        "memory requirements."
    )


# ============================================================
# 26. SECURITY AND DATA QUALITY
# ============================================================

def data_quality_note() -> None:
    """
    Explain security and data-quality considerations.

    Percentiles are analytical outputs, so the major risks are usually
    data integrity, manipulation, privacy, and incorrect interpretation.
    """
    print("\n" + "=" * 70)
    print("DATA QUALITY AND SECURITY CONSIDERATIONS")
    print("=" * 70)

    print(
        "1. Validate numeric inputs rather than silently coercing bad data."
    )
    print(
        "2. Define how missing observations are handled before analysis."
    )
    print(
        "3. Protect sensitive customer, employee, financial, or operational "
        "data according to applicable access controls."
    )
    print(
        "4. Monitor unusual changes in percentile values because sudden "
        "distribution shifts can indicate real business changes or data "
        "pipeline problems."
    )
    print(
        "5. Preserve the percentile method and data-filtering rules so that "
        "reports can be reproduced."
    )


# ============================================================
# 27. MAIN EDUCATIONAL PROGRAM
# ============================================================

def main() -> None:
    print("=" * 70)
    print("PERCENTILES & QUARTILES")
    print("Distribution Analysis and Business Interpretation")
    print("=" * 70)

    basic_data = [
        12, 15, 18, 20, 22,
        24, 25, 27, 30, 32,
        35, 38, 40, 45, 50,
    ]

    print("\nBasic dataset:")
    print(basic_data)

    print("\nBasic descriptive statistics:")
    for key, value in describe_basic(basic_data).items():
        print(f"{key:<22}: {value:.2f}")

    print_percentile_table(
        basic_data,
        [0, 10, 25, 50, 75, 90, 95, 100],
    )

    print("\nQuartiles:")
    for key, value in quartiles(basic_data).items():
        print(f"{key}: {value:.2f}")

    print("\nFive-number summary:")
    for key, value in five_number_summary(basic_data).items():
        print(f"{key:<10}: {value:.2f}")

    print(f"\nIQR: {interquartile_range(basic_data):.2f}")

    lower, upper = iqr_outlier_fences(basic_data)
    print(f"IQR lower fence: {lower:.2f}")
    print(f"IQR upper fence: {upper:.2f}")

    print("\nPercentile rank examples:")
    for value in (18, 30, 40, 50):
        print(
            f"{value:>5} is at or below approximately "
            f"{percentile_rank(basic_data, value):.1f}% of observations."
        )

    print("\nQuartile segmentation:")
    for value in (15, 22, 30, 45):
        print(
            f"{value:>5}: {assign_quartile_segment(basic_data, value)}"
        )

    print("\nPercentile segmentation:")
    for value in (15, 22, 30, 45):
        print(
            f"{value:>5}: {percentile_segment(basic_data, value)}"
        )

    print("\nEmpirical CDF:")
    for value, probability in empirical_cdf_table(basic_data):
        print(f"F({value:.0f}) = {probability:.3f}")

    print("\nSkewness:")
    pearson = pearson_second_skewness(basic_data)
    bowley = bowley_skewness(basic_data)
    print(f"Pearson second skewness: {pearson:.3f}")
    print(f"Bowley skewness: {bowley:.3f}")
    print(f"Interpretation: {classify_skewness(bowley)}")

    print("\nRobust statistics:")
    print(f"Mean: {mean(basic_data):.2f}")
    print(f"Median: {median(basic_data):.2f}")
    print(f"10% trimmed mean: {trimmed_mean(basic_data):.2f}")

    print("\nWeighted percentile example:")
    sales_values = [100, 200, 300, 500, 1000]
    customer_weights = [50, 30, 15, 4, 1]

    for p in (50, 75, 90):
        result = weighted_percentile(
            sales_values,
            customer_weights,
            p,
        )
        print(f"Weighted P{p}: {result:.2f}")

    compare_percentile_methods(basic_data)

    groups = {
        "Region A": [10, 12, 14, 16, 18, 20, 25, 30],
        "Region B": [8, 10, 15, 20, 25, 30, 40, 55],
        "Region C": [14, 15, 16, 17, 18, 19, 20, 21],
    }

    print_group_comparison(groups)

    print("\nExtreme-value sensitivity:")
    sensitivity = compare_before_after_extreme_value(
        basic_data,
        extreme_value=1000,
    )

    for scenario, statistics in sensitivity.items():
        print(f"\n{scenario}:")
        for key, value in statistics.items():
            print(f"{key:<10}: {value:.2f}")

    delivery_time_case_study()
    customer_spend_case_study()
    salary_case_study()
    response_time_case_study()

    demonstrate_edge_cases()
    demonstrate_validation()

    print_diagnostics(
        [
            20, 21, 22, 22, 23, 24, 25, 25, 26, 27,
            28, 30, 31, 35, 40, 50, 70, 100,
        ]
    )

    performance_note()
    data_quality_note()
    run_tests()

    print("\n" + "=" * 70)
    print("END OF PERCENTILES AND QUARTILES TUTORIAL")
    print("=" * 70)


if __name__ == "__main__":
    main()
