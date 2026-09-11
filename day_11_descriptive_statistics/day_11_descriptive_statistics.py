"""
Descriptive Statistics: Mean, Median, Mode, Variance and Standard Deviation

A self-contained study script covering descriptive statistics from absolute
beginner concepts through advanced implementation details.

Topics covered:
    1. Population vs sample
    2. Numerical and categorical data
    3. Mean
    4. Weighted mean
    5. Median
    6. Mode
    7. Range
    8. Quartiles and interquartile range
    9. Variance
    10. Standard deviation
    11. Population vs sample variance and standard deviation
    12. Manual implementations
    13. Python implementations
    14. Comparison of measures
    15. Outliers and skewed data
    16. Grouped and frequency data
    17. Weighted observations
    18. Numerical precision
    19. Online/streaming variance
    20. Welford's algorithm
    21. Robust statistics
    22. Data validation
    23. Performance considerations
    24. Statistical interpretation
    25. Real-world examples
    26. Testing and verification

Only Python's standard library is used.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, getcontext
from math import fsum, isfinite, sqrt
from statistics import (
    mean as statistics_mean,
    median as statistics_median,
    multimode,
    pvariance,
    pstdev,
    variance,
    stdev,
)
from typing import Iterable, Sequence


# ---------------------------------------------------------------------------
# 1. FOUNDATIONS
# ---------------------------------------------------------------------------

def print_section(title: str) -> None:
    """Print a consistent section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_subsection(title: str) -> None:
    """Print a subsection heading."""
    print(f"\n--- {title} ---")


def explain_foundations() -> None:
    """
    Demonstrate the basic terminology used in descriptive statistics.

    Descriptive statistics summarizes observed data. It does not, by itself,
    make claims about an entire population beyond the observations being
    summarized.
    """
    print_section("1. Foundations of descriptive statistics")

    data = [10, 12, 12, 15, 18]

    print("Dataset:", data)
    print("Number of observations:", len(data))
    print("Minimum:", min(data))
    print("Maximum:", max(data))

    print("\nPopulation:")
    print("A population is the complete set of observations of interest.")

    print("\nSample:")
    print("A sample is a subset used to learn about a larger population.")

    print("\nExample:")
    population = [10, 12, 12, 15, 18]
    sample = [10, 12, 18]

    print("Population:", population)
    print("Sample:", sample)

    print("\nImportant distinction:")
    print("Population variance divides by N.")
    print("Sample variance divides by n - 1.")

    print("\nData types:")
    categorical = ["red", "blue", "blue", "green"]
    numerical = [10, 20, 20, 30]

    print("Categorical data:", categorical)
    print("Numerical data:", numerical)

    print(
        "\nMean, median, variance and standard deviation are primarily "
        "descriptive measures for numerical data."
    )
    print(
        "Mode can be useful for both categorical and numerical data."
    )


# ---------------------------------------------------------------------------
# 2. DATA VALIDATION
# ---------------------------------------------------------------------------

def validate_numeric_data(
    data: Iterable[float],
    *,
    allow_empty: bool = False,
    require_finite: bool = True,
) -> list[float]:
    """
    Convert an iterable to a list of floats and validate the observations.

    Empty data is rejected by default because most descriptive measures
    require at least one observation.
    """
    values = list(data)

    if not values and not allow_empty:
        raise ValueError("The dataset must contain at least one observation.")

    result: list[float] = []

    for index, value in enumerate(values):
        if isinstance(value, bool):
            raise TypeError(
                f"Observation {index} is boolean. "
                "Boolean values should not be treated as measurements."
            )

        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                f"Observation {index} is not numeric: {value!r}"
            ) from exc

        if require_finite and not isfinite(numeric_value):
            raise ValueError(
                f"Observation {index} is not finite: {value!r}"
            )

        result.append(numeric_value)

    return result


# ---------------------------------------------------------------------------
# 3. MEAN
# ---------------------------------------------------------------------------

def arithmetic_mean(data: Iterable[float]) -> float:
    """
    Calculate the arithmetic mean.

    Formula:

        mean = (x1 + x2 + ... + xn) / n

    The implementation uses math.fsum rather than ordinary sum to reduce
    floating-point accumulation error for many floating-point observations.
    """
    values = validate_numeric_data(data)

    return fsum(values) / len(values)


def arithmetic_mean_simple(data: Iterable[float]) -> float:
    """
    Simple educational implementation of the arithmetic mean.

    This version intentionally uses sum() because the formula is easier
    to see directly.
    """
    values = validate_numeric_data(data)
    return sum(values) / len(values)


def weighted_mean(
    values: Iterable[float],
    weights: Iterable[float],
) -> float:
    """
    Calculate a weighted arithmetic mean.

    Formula:

        weighted mean = sum(w_i * x_i) / sum(w_i)

    Weights normally represent importance, frequency, probability mass,
    credit, or contribution.

    Negative weights are rejected because they do not represent ordinary
    weighting in this implementation.
    """
    x = validate_numeric_data(values)
    w = validate_numeric_data(weights)

    if len(x) != len(w):
        raise ValueError("Values and weights must have the same length.")

    if any(weight < 0 for weight in w):
        raise ValueError("Weights must be non-negative.")

    total_weight = fsum(w)

    if total_weight == 0:
        raise ValueError("The total weight must be greater than zero.")

    numerator = fsum(
        value * weight
        for value, weight in zip(x, w)
    )

    return numerator / total_weight


def demonstrate_mean() -> None:
    print_section("2. Mean")

    data = [10, 20, 30, 40, 50]

    print("Dataset:", data)
    print("Arithmetic mean:", arithmetic_mean(data))
    print("Simple implementation:", arithmetic_mean_simple(data))

    print("\nManual calculation:")
    total = sum(data)
    count = len(data)

    print("Sum =", total)
    print("Count =", count)
    print("Mean =", total / count)

    print("\nWeighted mean example:")
    scores = [80, 90, 70]
    weights = [0.2, 0.5, 0.3]

    print("Scores:", scores)
    print("Weights:", weights)
    print("Weighted mean:", weighted_mean(scores, weights))

    print("\nImportant property:")
    print(
        "The arithmetic mean uses every observation, so extreme values "
        "can substantially influence it."
    )


# ---------------------------------------------------------------------------
# 4. MEDIAN
# ---------------------------------------------------------------------------

def median_manual(data: Iterable[float]) -> float:
    """
    Calculate the median manually.

    For odd n:
        median = middle sorted observation

    For even n:
        median = average of the two middle observations.
    """
    values = sorted(validate_numeric_data(data))
    n = len(values)

    middle = n // 2

    if n % 2 == 1:
        return values[middle]

    return (values[middle - 1] + values[middle]) / 2


def demonstrate_median() -> None:
    print_section("3. Median")

    odd_data = [7, 2, 9, 4, 5]
    even_data = [7, 2, 9, 4, 5, 10]

    print("Odd-sized dataset:", odd_data)
    print("Sorted:", sorted(odd_data))
    print("Median:", median_manual(odd_data))

    print("\nEven-sized dataset:", even_data)
    print("Sorted:", sorted(even_data))
    print("Median:", median_manual(even_data))

    print(
        "\nThe median is resistant to extreme observations because "
        "it depends on position after sorting rather than the magnitude "
        "of every observation."
    )


# ---------------------------------------------------------------------------
# 5. MODE
# ---------------------------------------------------------------------------

def modes_manual(data: Iterable[float]) -> list[float]:
    """
    Return all modes.

    A mode is an observation occurring with the highest frequency.

    A dataset can have:
        - one mode
        - multiple modes
        - every value tied
    """
    values = validate_numeric_data(data)

    counts = Counter(values)
    highest_frequency = max(counts.values())

    return sorted(
        value
        for value, frequency in counts.items()
        if frequency == highest_frequency
    )


def demonstrate_mode() -> None:
    print_section("4. Mode")

    examples = {
        "Unimodal": [1, 2, 2, 3, 4],
        "Bimodal": [1, 1, 2, 2, 3],
        "All tied": [1, 2, 3, 4],
        "Categorical": ["red", "blue", "blue", "green"],
    }

    for name, data in examples.items():
        if isinstance(data[0], str):
            counts = Counter(data)
            highest = max(counts.values())
            result = [
                value
                for value, frequency in counts.items()
                if frequency == highest
            ]
        else:
            result = modes_manual(data)

        print(f"{name}: {data}")
        print("Modes:", result)

    print(
        "\nA dataset with multiple equally frequent values is multimodal."
    )


# ---------------------------------------------------------------------------
# 6. RANGE
# ---------------------------------------------------------------------------

def data_range(data: Iterable[float]) -> float:
    """Calculate maximum minus minimum."""
    values = validate_numeric_data(data)
    return max(values) - min(values)


def demonstrate_range() -> None:
    print_section("5. Range")

    data = [4, 8, 15, 16, 23, 42]

    print("Dataset:", data)
    print("Minimum:", min(data))
    print("Maximum:", max(data))
    print("Range:", data_range(data))

    print(
        "\nRange is simple but depends only on two observations. "
        "One extreme value can change it dramatically."
    )


# ---------------------------------------------------------------------------
# 7. QUARTILES AND INTERQUARTILE RANGE
# ---------------------------------------------------------------------------

def percentile_linear(data: Iterable[float], percentile: float) -> float:
    """
    Calculate a percentile using linear interpolation.

    This implementation uses the common position:

        position = (n - 1) * p

    where p is between 0 and 1.

    Different statistical software can use different percentile definitions.
    Therefore percentile results should be interpreted together with the
    chosen method.
    """
    values = sorted(validate_numeric_data(data))

    if not 0 <= percentile <= 1:
        raise ValueError("Percentile must be between 0 and 1.")

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)

    fraction = position - lower

    return values[lower] + fraction * (values[upper] - values[lower])


def quartiles_and_iqr(
    data: Iterable[float],
) -> tuple[float, float, float]:
    """Return Q1, Q3 and the interquartile range."""
    q1 = percentile_linear(data, 0.25)
    q3 = percentile_linear(data, 0.75)
    return q1, q3, q3 - q1


def demonstrate_quartiles() -> None:
    print_section("6. Quartiles and interquartile range")

    data = [4, 7, 8, 12, 15, 18, 21, 24, 30]

    q1, q3, iqr = quartiles_and_iqr(data)

    print("Dataset:", data)
    print("Q1:", q1)
    print("Q3:", q3)
    print("IQR:", iqr)

    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    print("Lower outlier fence:", lower_fence)
    print("Upper outlier fence:", upper_fence)

    print(
        "\nThe IQR measures the spread of the middle 50% of observations."
    )


# ---------------------------------------------------------------------------
# 8. VARIANCE
# ---------------------------------------------------------------------------

def population_variance_manual(data: Iterable[float]) -> float:
    """
    Calculate population variance.

    Formula:

        σ² = Σ(x_i - μ)² / N

    Every observation in the population is included.
    """
    values = validate_numeric_data(data)
    population_mean = arithmetic_mean(values)

    squared_deviations = [
        (value - population_mean) ** 2
        for value in values
    ]

    return fsum(squared_deviations) / len(values)


def sample_variance_manual(data: Iterable[float]) -> float:
    """
    Calculate sample variance.

    Formula:

        s² = Σ(x_i - x̄)² / (n - 1)

    The n - 1 denominator is Bessel's correction. Under the usual
    independent random-sample assumptions, it makes the sample variance
    an unbiased estimator of population variance.
    """
    values = validate_numeric_data(data)

    if len(values) < 2:
        raise ValueError(
            "At least two observations are required for sample variance."
        )

    sample_mean = arithmetic_mean(values)

    squared_deviations = [
        (value - sample_mean) ** 2
        for value in values
    ]

    return fsum(squared_deviations) / (len(values) - 1)


def demonstrate_variance() -> None:
    print_section("7. Variance")

    population = [2, 4, 4, 4, 5, 5, 7, 9]

    pop_variance = population_variance_manual(population)
    sample_variance = sample_variance_manual(population)

    print("Data:", population)
    print("Mean:", arithmetic_mean(population))
    print("Population variance:", pop_variance)
    print("Sample variance:", sample_variance)

    print("\nStep-by-step population variance:")

    mean_value = arithmetic_mean(population)

    for value in population:
        deviation = value - mean_value
        squared_deviation = deviation ** 2

        print(
            f"x={value:>4}, "
            f"x-mean={deviation:>7.3f}, "
            f"(x-mean)^2={squared_deviation:>9.3f}"
        )

    print(
        "\nVariance is measured in squared units. "
        "For example, if data is measured in rupees, variance is measured "
        "in rupees squared."
    )


# ---------------------------------------------------------------------------
# 9. STANDARD DEVIATION
# ---------------------------------------------------------------------------

def population_standard_deviation_manual(
    data: Iterable[float],
) -> float:
    """Calculate population standard deviation."""
    return sqrt(population_variance_manual(data))


def sample_standard_deviation_manual(
    data: Iterable[float],
) -> float:
    """Calculate sample standard deviation."""
    return sqrt(sample_variance_manual(data))


def demonstrate_standard_deviation() -> None:
    print_section("8. Standard deviation")

    data = [2, 4, 4, 4, 5, 5, 7, 9]

    population_sd = population_standard_deviation_manual(data)
    sample_sd = sample_standard_deviation_manual(data)

    print("Data:", data)
    print("Population standard deviation:", population_sd)
    print("Sample standard deviation:", sample_sd)

    print(
        "\nStandard deviation is the square root of variance. "
        "It returns the spread measure to the original units of the data."
    )

    print(
        "\nInterpretation must consider the distribution. "
        "A standard deviation is not automatically the distance from the "
        "mean that every observation must fall within."
    )


# ---------------------------------------------------------------------------
# 10. POPULATION VS SAMPLE
# ---------------------------------------------------------------------------

def compare_population_and_sample() -> None:
    print_section("9. Population versus sample")

    data = [10, 12, 15, 18, 20]

    print("Dataset:", data)
    print()
    print("Population variance:", population_variance_manual(data))
    print("Sample variance:", sample_variance_manual(data))
    print(
        "Population standard deviation:",
        population_standard_deviation_manual(data),
    )
    print(
        "Sample standard deviation:",
        sample_standard_deviation_manual(data),
    )

    print("\nPython statistics module:")
    print("pvariance:", pvariance(data))
    print("variance:", variance(data))
    print("pstdev:", pstdev(data))
    print("stdev:", stdev(data))

    print(
        "\nUse population measures when the dataset itself is the complete "
        "population of interest."
    )

    print(
        "Use sample measures when the observations represent a sample and "
        "the goal is to estimate population variability."
    )


# ---------------------------------------------------------------------------
# 11. COMPARING DATASETS
# ---------------------------------------------------------------------------

def compare_datasets() -> None:
    print_section("10. Comparing datasets")

    dataset_a = [50, 50, 50, 50, 50]
    dataset_b = [30, 40, 50, 60, 70]
    dataset_c = [10, 45, 50, 55, 90]

    datasets = {
        "A": dataset_a,
        "B": dataset_b,
        "C": dataset_c,
    }

    for name, data in datasets.items():
        print(f"\nDataset {name}: {data}")
        print("Mean:", arithmetic_mean(data))
        print("Median:", median_manual(data))
        print("Population variance:", population_variance_manual(data))
        print(
            "Population standard deviation:",
            population_standard_deviation_manual(data),
        )

    print(
        "\nDatasets can have the same mean while having very different "
        "amounts of variation."
    )


# ---------------------------------------------------------------------------
# 12. EFFECT OF OUTLIERS
# ---------------------------------------------------------------------------

def demonstrate_outliers() -> None:
    print_section("11. Outliers and their effect")

    normal_data = [20, 21, 22, 23, 24, 25, 26]
    outlier_data = normal_data + [200]

    print("Original:", normal_data)
    print("With outlier:", outlier_data)

    print("\nOriginal mean:", arithmetic_mean(normal_data))
    print("With outlier:", arithmetic_mean(outlier_data))

    print("\nOriginal median:", median_manual(normal_data))
    print("With outlier:", median_manual(outlier_data))

    print(
        "\nMean changed substantially because it incorporates the magnitude "
        "of every observation."
    )

    print(
        "Median changed much less because it is based on ordered position."
    )

    print("\nSpread comparison:")
    print(
        "Original population SD:",
        population_standard_deviation_manual(normal_data),
    )
    print(
        "With outlier population SD:",
        population_standard_deviation_manual(outlier_data),
    )


# ---------------------------------------------------------------------------
# 13. SKEWNESS AND INTERPRETATION
# ---------------------------------------------------------------------------

def pearson_median_skewness(data: Iterable[float]) -> float:
    """
    Calculate Pearson's second coefficient of skewness.

        Skewness approximation = 3(mean - median) / standard deviation

    This is a descriptive index, not the only definition of skewness.
    """
    values = validate_numeric_data(data)

    sd = population_standard_deviation_manual(values)

    if sd == 0:
        return 0.0

    return 3 * (
        arithmetic_mean(values) - median_manual(values)
    ) / sd


def demonstrate_skewness() -> None:
    print_section("12. Mean, median and skewness")

    distributions = {
        "Approximately symmetric": [2, 3, 4, 5, 6, 7, 8],
        "Right-skewed": [1, 2, 2, 3, 3, 4, 20],
        "Left-skewed": [1, 17, 18, 18, 19, 20, 20],
    }

    for name, data in distributions.items():
        print(f"\n{name}")
        print("Data:", data)
        print("Mean:", arithmetic_mean(data))
        print("Median:", median_manual(data))
        print("Mean - median:", arithmetic_mean(data) - median_manual(data))
        print(
            "Pearson median skewness:",
            pearson_median_skewness(data),
        )

    print(
        "\nMean greater than median often occurs in right-skewed data, "
        "while mean less than median often occurs in left-skewed data. "
        "This is a useful descriptive clue, not a universal rule."
    )


# ---------------------------------------------------------------------------
# 14. FREQUENCY DATA
# ---------------------------------------------------------------------------

def frequency_mean(
    values: Iterable[float],
    frequencies: Iterable[int],
) -> float:
    """
    Calculate a mean from distinct values and their frequencies.

        mean = Σ(x_i f_i) / Σf_i
    """
    x = validate_numeric_data(values)
    f = list(frequencies)

    if len(x) != len(f):
        raise ValueError("Values and frequencies must have equal lengths.")

    if any(isinstance(value, bool) or not isinstance(value, int) for value in f):
        raise TypeError("Frequencies must be integers.")

    if any(value < 0 for value in f):
        raise ValueError("Frequencies cannot be negative.")

    total_frequency = sum(f)

    if total_frequency == 0:
        raise ValueError("Total frequency must be greater than zero.")

    return fsum(
        value * frequency
        for value, frequency in zip(x, f)
    ) / total_frequency


def frequency_variance(
    values: Iterable[float],
    frequencies: Iterable[int],
    *,
    sample: bool = False,
) -> float:
    """
    Calculate variance from frequency data.

    For sample variance, the denominator is total_frequency - 1.
    """
    x = validate_numeric_data(values)
    f = list(frequencies)

    if len(x) != len(f):
        raise ValueError("Values and frequencies must have equal lengths.")

    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in f
    ):
        raise TypeError("Frequencies must be integers.")

    if any(value < 0 for value in f):
        raise ValueError("Frequencies cannot be negative.")

    total_frequency = sum(f)

    denominator = total_frequency - 1 if sample else total_frequency

    if denominator <= 0:
        raise ValueError(
            "Not enough observations for the requested variance."
        )

    mean_value = frequency_mean(x, f)

    squared_sum = fsum(
        frequency * (value - mean_value) ** 2
        for value, frequency in zip(x, f)
    )

    return squared_sum / denominator


def demonstrate_frequency_data() -> None:
    print_section("13. Frequency data")

    values = [10, 20, 30, 40]
    frequencies = [2, 3, 4, 1]

    expanded = [
        value
        for value, frequency in zip(values, frequencies)
        for _ in range(frequency)
    ]

    print("Distinct values:", values)
    print("Frequencies:", frequencies)
    print("Expanded data:", expanded)

    print("\nFrequency mean:", frequency_mean(values, frequencies))
    print("Expanded mean:", arithmetic_mean(expanded))

    print(
        "\nFrequency population variance:",
        frequency_variance(values, frequencies),
    )

    print(
        "Expanded population variance:",
        population_variance_manual(expanded),
    )


# ---------------------------------------------------------------------------
# 15. GROUPED DATA
# ---------------------------------------------------------------------------

def grouped_data_mean(
    class_midpoints: Iterable[float],
    frequencies: Iterable[int],
) -> float:
    """
    Approximate the mean of grouped continuous data.

    Class midpoints are used as representative values, so the result is
    generally an approximation rather than the exact raw-data mean.
    """
    return frequency_mean(class_midpoints, frequencies)


def demonstrate_grouped_data() -> None:
    print_section("14. Grouped data")

    intervals = [
        "0-10",
        "10-20",
        "20-30",
        "30-40",
    ]

    midpoints = [5, 15, 25, 35]
    frequencies = [3, 7, 8, 2]

    print("Intervals:", intervals)
    print("Midpoints:", midpoints)
    print("Frequencies:", frequencies)

    print(
        "Estimated mean:",
        grouped_data_mean(midpoints, frequencies),
    )

    print(
        "\nGrouped-data statistics lose information because individual "
        "observations inside each interval are no longer known."
    )


# ---------------------------------------------------------------------------
# 16. ROBUST STATISTICS
# ---------------------------------------------------------------------------

def median_absolute_deviation(data: Iterable[float]) -> float:
    """
    Calculate the median absolute deviation (MAD).

        MAD = median(|x_i - median(x)|)

    MAD is resistant to outliers and is useful when data is strongly skewed
    or contains extreme observations.
    """
    values = validate_numeric_data(data)
    center = median_manual(values)

    deviations = [
        abs(value - center)
        for value in values
    ]

    return median_manual(deviations)


def demonstrate_robust_statistics() -> None:
    print_section("15. Robust descriptive statistics")

    data = [20, 21, 22, 22, 23, 24, 25, 200]

    print("Data:", data)
    print("Mean:", arithmetic_mean(data))
    print("Median:", median_manual(data))
    print(
        "Population standard deviation:",
        population_standard_deviation_manual(data),
    )
    print("IQR:", quartiles_and_iqr(data)[2])
    print("MAD:", median_absolute_deviation(data))

    print(
        "\nRobust measures such as median, IQR and MAD are often more "
        "informative than mean and standard deviation when extreme values "
        "or heavy tails dominate the dataset."
    )


# ---------------------------------------------------------------------------
# 17. PERCENTILES
# ---------------------------------------------------------------------------

def demonstrate_percentiles() -> None:
    print_section("16. Percentiles")

    data = [5, 10, 15, 20, 25, 30, 35, 40]

    print("Data:", data)

    for percentile in [0, 0.10, 0.25, 0.50, 0.75, 0.90, 1.0]:
        print(
            f"{percentile * 100:>5.1f}th percentile:",
            percentile_linear(data, percentile),
        )

    print(
        "\nThe 50th percentile corresponds to the median under this "
        "percentile definition."
    )


# ---------------------------------------------------------------------------
# 18. COEFFICIENT OF VARIATION
# ---------------------------------------------------------------------------

def coefficient_of_variation(data: Iterable[float]) -> float:
    """
    Calculate the population coefficient of variation.

        CV = standard deviation / mean

    CV is dimensionless, but interpretation becomes problematic when the
    mean is zero or close to zero. For datasets where the mean can be
    negative, domain-specific interpretation is required.
    """
    values = validate_numeric_data(data)
    mean_value = arithmetic_mean(values)

    if mean_value == 0:
        raise ValueError(
            "Coefficient of variation is undefined when the mean is zero."
        )

    return population_standard_deviation_manual(values) / mean_value


def demonstrate_coefficient_of_variation() -> None:
    print_section("17. Coefficient of variation")

    investment_a = [90, 100, 110]
    investment_b = [180, 200, 220]

    for name, data in {
        "A": investment_a,
        "B": investment_b,
    }.items():
        print(f"Investment {name}: {data}")
        print("Mean:", arithmetic_mean(data))
        print(
            "Population SD:",
            population_standard_deviation_manual(data),
        )
        print(
            "CV:",
            coefficient_of_variation(data),
        )

    print(
        "\nCV can compare relative variability when the means are positive "
        "and the ratio is meaningful for the domain."
    )


# ---------------------------------------------------------------------------
# 19. ONLINE / STREAMING STATISTICS
# ---------------------------------------------------------------------------

@dataclass
class RunningStatistics:
    """
    Online calculation of mean and population variance.

    This implementation uses Welford's algorithm.

    It avoids storing the complete dataset and is substantially more stable
    than calculating variance through:

        mean(x^2) - mean(x)^2

    which can suffer from catastrophic cancellation.
    """

    count: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def update(self, value: float) -> None:
        """Add one observation."""
        if isinstance(value, bool):
            raise TypeError("Boolean values are not valid observations.")

        value = float(value)

        if not isfinite(value):
            raise ValueError("Observation must be finite.")

        self.count += 1

        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean

        self.m2 += delta * delta2

    def population_variance(self) -> float:
        """Return population variance of observations seen so far."""
        if self.count == 0:
            raise ValueError("No observations have been added.")

        return self.m2 / self.count

    def sample_variance(self) -> float:
        """Return sample variance of observations seen so far."""
        if self.count < 2:
            raise ValueError(
                "At least two observations are required."
            )

        return self.m2 / (self.count - 1)

    def population_standard_deviation(self) -> float:
        """Return population standard deviation."""
        return sqrt(self.population_variance())

    def sample_standard_deviation(self) -> float:
        """Return sample standard deviation."""
        return sqrt(self.sample_variance())


def demonstrate_welford() -> None:
    print_section("18. Streaming statistics and Welford's algorithm")

    data = [10, 20, 30, 40, 50]

    running = RunningStatistics()

    for value in data:
        running.update(value)

        print(
            f"Added {value:>3}: "
            f"count={running.count}, "
            f"mean={running.mean:.4f}, "
            f"population_variance="
            f"{running.population_variance():.4f}"
        )

    print("\nBatch calculation:")
    print("Mean:", arithmetic_mean(data))
    print(
        "Population variance:",
        population_variance_manual(data),
    )

    print(
        "\nWelford's algorithm is useful for large streams of data where "
        "keeping every observation in memory is undesirable."
    )


# ---------------------------------------------------------------------------
# 20. NUMERICAL STABILITY
# ---------------------------------------------------------------------------

def naive_variance_formula(data: Iterable[float]) -> float:
    """
    Calculate population variance through E[X²] - E[X]².

    This formula is mathematically correct but can be numerically unstable
    when values are very large while their variance is relatively small.
    """
    values = validate_numeric_data(data)

    mean_value = arithmetic_mean(values)
    mean_square = fsum(value * value for value in values) / len(values)

    return mean_square - mean_value * mean_value


def demonstrate_numerical_stability() -> None:
    print_section("19. Numerical precision and variance")

    data = [
        1_000_000_000_000.0 + 1,
        1_000_000_000_000.0 + 2,
        1_000_000_000_000.0 + 3,
        1_000_000_000_000.0 + 4,
    ]

    stable = population_variance_manual(data)
    naive = naive_variance_formula(data)

    print("Data:", data)
    print("Stable deviation-based variance:", stable)
    print("Naive E[X²] - E[X]² variance:", naive)

    print(
        "\nFloating-point arithmetic has finite precision. "
        "Subtracting two very large nearly equal quantities can lose "
        "significant information."
    )

    print(
        "Deviation-based algorithms and Welford's algorithm are preferred "
        "for numerically sensitive calculations."
    )


# ---------------------------------------------------------------------------
# 21. DECIMAL ARITHMETIC
# ---------------------------------------------------------------------------

def demonstrate_decimal_precision() -> None:
    print_section("20. Decimal arithmetic")

    getcontext().prec = 28

    values = [
        Decimal("0.1"),
        Decimal("0.2"),
        Decimal("0.3"),
    ]

    decimal_mean = sum(values) / Decimal(len(values))

    print("Decimal values:", values)
    print("Decimal mean:", decimal_mean)

    binary_float_result = (0.1 + 0.2) == 0.3

    print("\nBinary floating-point comparison:")
    print("0.1 + 0.2 == 0.3:", binary_float_result)

    print(
        "\nDecimal arithmetic can be appropriate when exact decimal "
        "representation matters, especially in financial calculations."
    )


# ---------------------------------------------------------------------------
# 22. COMPLETE DESCRIPTIVE STATISTICS PROFILE
# ---------------------------------------------------------------------------

@dataclass
class DescriptiveStatistics:
    """Container for commonly used descriptive statistics."""

    count: int
    minimum: float
    maximum: float
    range: float
    mean: float
    median: float
    modes: list[float]
    population_variance: float
    population_standard_deviation: float
    sample_variance: float | None
    sample_standard_deviation: float | None
    q1: float
    q3: float
    iqr: float
    mad: float


def describe(data: Iterable[float]) -> DescriptiveStatistics:
    """
    Produce a comprehensive descriptive statistics profile.

    Sample variance and sample standard deviation are omitted for datasets
    containing fewer than two observations.
    """
    values = validate_numeric_data(data)

    q1, q3, iqr = quartiles_and_iqr(values)

    if len(values) >= 2:
        sample_var = sample_variance_manual(values)
        sample_sd = sqrt(sample_var)
    else:
        sample_var = None
        sample_sd = None

    return DescriptiveStatistics(
        count=len(values),
        minimum=min(values),
        maximum=max(values),
        range=max(values) - min(values),
        mean=arithmetic_mean(values),
        median=median_manual(values),
        modes=modes_manual(values),
        population_variance=population_variance_manual(values),
        population_standard_deviation=population_standard_deviation_manual(
            values
        ),
        sample_variance=sample_var,
        sample_standard_deviation=sample_sd,
        q1=q1,
        q3=q3,
        iqr=iqr,
        mad=median_absolute_deviation(values),
    )


def demonstrate_describe() -> None:
    print_section("21. Complete descriptive statistics profile")

    data = [12, 15, 15, 16, 18, 20, 21, 21, 25, 30]

    profile = describe(data)

    print("Data:", data)

    for field_name, value in vars(profile).items():
        print(f"{field_name}: {value}")


# ---------------------------------------------------------------------------
# 23. OUTLIER DETECTION USING IQR
# ---------------------------------------------------------------------------

def iqr_outliers(data: Iterable[float]) -> list[float]:
    """Return observations outside the conventional 1.5 × IQR fences."""
    values = validate_numeric_data(data)

    q1, q3, iqr = quartiles_and_iqr(values)

    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    return [
        value
        for value in values
        if value < lower_fence or value > upper_fence
    ]


def demonstrate_iqr_outliers() -> None:
    print_section("22. IQR-based outlier detection")

    data = [10, 11, 12, 12, 13, 14, 15, 16, 100]

    q1, q3, iqr = quartiles_and_iqr(data)

    print("Data:", data)
    print("Q1:", q1)
    print("Q3:", q3)
    print("IQR:", iqr)
    print("Potential outliers:", iqr_outliers(data))

    print(
        "\nAn IQR rule identifies observations for investigation. "
        "It does not prove that an observation is erroneous."
    )


# ---------------------------------------------------------------------------
# 24. Z-SCORES
# ---------------------------------------------------------------------------

def z_scores(data: Iterable[float]) -> list[float]:
    """
    Standardize observations using the population mean and population SD.

        z = (x - mean) / standard deviation

    A z-score describes an observation relative to the dataset's center
    and spread.
    """
    values = validate_numeric_data(data)
    mean_value = arithmetic_mean(values)
    sd = population_standard_deviation_manual(values)

    if sd == 0:
        return [0.0 for _ in values]

    return [
        (value - mean_value) / sd
        for value in values
    ]


def demonstrate_z_scores() -> None:
    print_section("23. Z-scores")

    data = [40, 45, 50, 55, 60]

    print("Data:", data)

    for value, z in zip(data, z_scores(data)):
        print(f"Value {value}: z-score = {z:.4f}")

    print(
        "\nA z-score of zero means the observation equals the mean. "
        "Positive values are above the mean and negative values are below it."
    )


# ---------------------------------------------------------------------------
# 25. PERCENTAGE CHANGE AND DESCRIPTIVE CONTEXT
# ---------------------------------------------------------------------------

def percentage_difference_from_mean(
    data: Iterable[float],
) -> list[float]:
    """Return percentage difference from the arithmetic mean."""
    values = validate_numeric_data(data)
    mean_value = arithmetic_mean(values)

    if mean_value == 0:
        raise ValueError(
            "Cannot calculate percentage differences from a zero mean."
        )

    return [
        ((value - mean_value) / mean_value) * 100
        for value in values
    ]


def demonstrate_relative_deviation() -> None:
    print_section("24. Relative deviation from the mean")

    sales = [90, 100, 110, 120, 80]

    print("Sales:", sales)
    print("Mean sales:", arithmetic_mean(sales))

    for value, percentage in zip(
        sales,
        percentage_difference_from_mean(sales),
    ):
        print(
            f"{value:>3} is {percentage:>7.2f}% "
            "from the mean."
        )


# ---------------------------------------------------------------------------
# 26. REAL-WORLD APPLICATION: STUDENT SCORES
# ---------------------------------------------------------------------------

def student_score_analysis() -> None:
    print_section("25. Real-world example: student scores")

    scores = [62, 75, 81, 81, 84, 88, 91, 95, 100]

    profile = describe(scores)

    print("Scores:", scores)
    print("Average score:", profile.mean)
    print("Median score:", profile.median)
    print("Mode:", profile.modes)
    print("Score range:", profile.range)
    print(
        "Population standard deviation:",
        profile.population_standard_deviation,
    )
    print("Q1:", profile.q1)
    print("Q3:", profile.q3)
    print("IQR:", profile.iqr)

    print(
        "\nInterpretation:"
        "\n- Mean represents the arithmetic average."
        "\n- Median represents the central ordered position."
        "\n- Mode identifies the most frequent score."
        "\n- Standard deviation describes overall spread around the mean."
        "\n- IQR describes the spread of the middle half."
    )


# ---------------------------------------------------------------------------
# 27. REAL-WORLD APPLICATION: BUSINESS SALES
# ---------------------------------------------------------------------------

def business_sales_analysis() -> None:
    print_section("26. Real-world example: monthly sales")

    monthly_sales = [
        120_000,
        125_000,
        118_000,
        132_000,
        127_000,
        140_000,
        250_000,
    ]

    print("Monthly sales:", monthly_sales)

    mean_sales = arithmetic_mean(monthly_sales)
    median_sales = median_manual(monthly_sales)
    sd_sales = population_standard_deviation_manual(monthly_sales)

    print("Mean sales:", mean_sales)
    print("Median sales:", median_sales)
    print("Population SD:", sd_sales)

    print(
        "\nThe unusually high final month pulls the mean upward. "
        "The median provides a more resistant measure of a typical month."
    )


# ---------------------------------------------------------------------------
# 28. REAL-WORLD APPLICATION: INVESTMENT RETURNS
# ---------------------------------------------------------------------------

def investment_return_analysis() -> None:
    print_section("27. Real-world example: investment returns")

    returns = [0.04, -0.02, 0.06, 0.01, -0.03, 0.08]

    mean_return = arithmetic_mean(returns)
    volatility = population_standard_deviation_manual(returns)

    print("Returns:", returns)
    print("Mean return:", mean_return)
    print("Mean return percentage:", mean_return * 100)
    print("Population standard deviation:", volatility)
    print("Volatility percentage:", volatility * 100)

    print(
        "\nStandard deviation is commonly used as a descriptive measure "
        "of variability in investment returns, although it does not fully "
        "describe downside risk, tail risk or non-normal return behavior."
    )


# ---------------------------------------------------------------------------
# 29. REAL-WORLD APPLICATION: OPERATIONS
# ---------------------------------------------------------------------------

def delivery_time_analysis() -> None:
    print_section("28. Real-world example: delivery times")

    delivery_times = [28, 31, 29, 30, 32, 27, 29, 45, 31, 30]

    print("Delivery times in minutes:", delivery_times)

    print("Mean:", arithmetic_mean(delivery_times))
    print("Median:", median_manual(delivery_times))
    print("Mode:", modes_manual(delivery_times))
    print(
        "Population standard deviation:",
        population_standard_deviation_manual(delivery_times),
    )
    print("IQR:", quartiles_and_iqr(delivery_times)[2])
    print("Potential outliers:", iqr_outliers(delivery_times))

    print(
        "\nFor operational service times, median and percentile measures "
        "can be especially useful because customers experience delays "
        "individually rather than as an average."
    )


# ---------------------------------------------------------------------------
# 30. EDGE CASES
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print_section("29. Edge cases and exceptions")

    cases = {
        "Single observation": [42],
        "Repeated observation": [10, 10, 10, 10],
        "Negative values": [-10, -5, 0, 5, 10],
        "Decimal values": [1.1, 1.2, 1.3],
    }

    for name, data in cases.items():
        print(f"\n{name}: {data}")

        profile = describe(data)

        print("Mean:", profile.mean)
        print("Median:", profile.median)
        print("Mode:", profile.modes)
        print(
            "Population variance:",
            profile.population_variance,
        )
        print(
            "Population SD:",
            profile.population_standard_deviation,
        )
        print("Sample variance:", profile.sample_variance)

    print("\nEmpty dataset:")
    try:
        arithmetic_mean([])
    except ValueError as error:
        print("Handled:", error)

    print("\nSample variance with one observation:")
    try:
        sample_variance_manual([42])
    except ValueError as error:
        print("Handled:", error)

    print("\nZero-mean coefficient of variation:")
    try:
        coefficient_of_variation([-1, 0, 1])
    except ValueError as error:
        print("Handled:", error)

    print("\nNaN:")
    try:
        arithmetic_mean([1, float("nan"), 3])
    except ValueError as error:
        print("Handled:", error)


# ---------------------------------------------------------------------------
# 31. COMMON MISTAKES
# ---------------------------------------------------------------------------

def demonstrate_common_mistakes() -> None:
    print_section("30. Common mistakes")

    data = [10, 20, 30, 40]

    print("Data:", data)

    print(
        "\nMistake 1: confusing variance with standard deviation."
    )
    print("Variance:", population_variance_manual(data))
    print(
        "Standard deviation:",
        population_standard_deviation_manual(data),
    )

    print(
        "\nMistake 2: using sample variance when the complete population "
        "is being described."
    )
    print(
        "Population variance:",
        population_variance_manual(data),
    )
    print(
        "Sample variance:",
        sample_variance_manual(data),
    )

    print(
        "\nMistake 3: assuming the mean is always the best measure of center."
    )
    skewed = [10, 11, 12, 13, 100]

    print("Skewed data:", skewed)
    print("Mean:", arithmetic_mean(skewed))
    print("Median:", median_manual(skewed))

    print(
        "\nMistake 4: treating an outlier as automatically incorrect."
    )
    print(
        "An extreme observation may be a valid and important part of "
        "the underlying process."
    )

    print(
        "\nMistake 5: interpreting standard deviation without considering "
        "the shape and units of the distribution."
    )


# ---------------------------------------------------------------------------
# 32. COMPARISON TABLE THROUGH CODE
# ---------------------------------------------------------------------------

def measure_comparison() -> None:
    print_section("31. Comparing descriptive measures")

    measures = [
        (
            "Mean",
            "Arithmetic center",
            "Sensitive to outliers",
            "Numerical",
        ),
        (
            "Median",
            "Middle ordered value",
            "Robust to outliers",
            "Numerical",
        ),
        (
            "Mode",
            "Most frequent value",
            "Depends on frequency",
            "Categorical/numerical",
        ),
        (
            "Range",
            "Maximum - minimum",
            "Highly sensitive",
            "Numerical",
        ),
        (
            "Variance",
            "Average squared deviation",
            "Sensitive to outliers",
            "Numerical",
        ),
        (
            "Standard deviation",
            "Square root of variance",
            "Sensitive to outliers",
            "Numerical",
        ),
        (
            "IQR",
            "Q3 - Q1",
            "Robust",
            "Numerical",
        ),
        (
            "MAD",
            "Median absolute deviation",
            "Robust",
            "Numerical",
        ),
    ]

    headers = [
        "Measure",
        "Meaning",
        "Outlier behavior",
        "Typical data",
    ]

    widths = [20, 28, 25, 22]

    print(
        "".join(
            header.ljust(width)
            for header, width in zip(headers, widths)
        )
    )

    print("-" * sum(widths))

    for row in measures:
        print(
            "".join(
                str(value).ljust(width)
                for value, width in zip(row, widths)
            )
        )


# ---------------------------------------------------------------------------
# 33. VERIFY AGAINST PYTHON'S STANDARD LIBRARY
# ---------------------------------------------------------------------------

def verify_against_statistics_module() -> None:
    print_section("32. Verification against Python's statistics module")

    data = [4.5, 7.2, 7.2, 8.1, 10.4, 12.8, 15.0]

    custom_mean = arithmetic_mean(data)
    custom_median = median_manual(data)
    custom_population_variance = population_variance_manual(data)
    custom_sample_variance = sample_variance_manual(data)
    custom_population_sd = population_standard_deviation_manual(data)
    custom_sample_sd = sample_standard_deviation_manual(data)

    print("Data:", data)

    print("\nMean:")
    print("Custom:", custom_mean)
    print("statistics.mean:", statistics_mean(data))

    print("\nMedian:")
    print("Custom:", custom_median)
    print("statistics.median:", statistics_median(data))

    print("\nPopulation variance:")
    print("Custom:", custom_population_variance)
    print("statistics.pvariance:", pvariance(data))

    print("\nSample variance:")
    print("Custom:", custom_sample_variance)
    print("statistics.variance:", variance(data))

    print("\nPopulation standard deviation:")
    print("Custom:", custom_population_sd)
    print("statistics.pstdev:", pstdev(data))

    print("\nSample standard deviation:")
    print("Custom:", custom_sample_sd)
    print("statistics.stdev:", stdev(data))

    print("\nModes:")
    print("Custom:", modes_manual(data))
    print("statistics.multimode:", multimode(data))


# ---------------------------------------------------------------------------
# 34. ASSERTION-BASED TESTS
# ---------------------------------------------------------------------------

def run_tests() -> None:
    """Run correctness tests for the core implementations."""
    print_section("33. Tests")

    data = [1, 2, 3, 4, 5]

    assert arithmetic_mean(data) == 3.0
    assert median_manual(data) == 3.0

    assert population_variance_manual(data) == 2.0
    assert sample_variance_manual(data) == 2.5

    assert (
        population_standard_deviation_manual(data)
        == sqrt(2.0)
    )

    assert (
        sample_standard_deviation_manual(data)
        == sqrt(2.5)
    )

    assert modes_manual([1, 1, 2, 3]) == [1.0]

    assert weighted_mean(
        [10, 20],
        [1, 3],
    ) == 17.5

    assert data_range(data) == 4.0

    q1, q3, iqr = quartiles_and_iqr(data)
    assert q1 == 2.0
    assert q3 == 4.0
    assert iqr == 2.0

    running = RunningStatistics()

    for value in data:
        running.update(value)

    assert abs(running.mean - 3.0) < 1e-12
    assert abs(running.population_variance() - 2.0) < 1e-12

    try:
        arithmetic_mean([])
    except ValueError:
        pass
    else:
        raise AssertionError("Empty dataset should raise ValueError.")

    try:
        sample_variance_manual([1])
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Sample variance with one observation should fail."
        )

    try:
        arithmetic_mean([1, float("inf")])
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Non-finite data should raise ValueError."
        )

    print("All tests passed.")


# ---------------------------------------------------------------------------
# 35. PERFORMANCE COMPARISON
# ---------------------------------------------------------------------------

def explain_performance() -> None:
    print_section("34. Performance considerations")

    print(
        "Mean, variance and standard deviation can generally be calculated "
        "in O(n) time."
    )

    print(
        "Median generally requires ordering the observations, giving "
        "O(n log n) time with a full sort."
    )

    print(
        "Mode using a frequency dictionary is typically O(n) expected time "
        "with O(k) additional storage, where k is the number of distinct "
        "values."
    )

    print(
        "Welford's algorithm processes each observation once and requires "
        "O(1) additional state."
    )

    print(
        "A full descriptive profile may require multiple passes or "
        "additional storage depending on which statistics are requested."
    )

    print(
        "\nFor very large datasets, streaming algorithms, database-side "
        "aggregation, approximate quantiles, chunk processing and "
        "distributed aggregation may be appropriate."
    )


# ---------------------------------------------------------------------------
# 36. SECURITY AND DATA QUALITY
# ---------------------------------------------------------------------------

def explain_data_quality_and_security() -> None:
    print_section("35. Data quality and security considerations")

    print(
        "Statistical calculations are only as reliable as the data supplied "
        "to them."
    )

    print(
        "\nImportant validation checks:"
        "\n1. Confirm that observations have the correct type."
        "\n2. Check for missing values."
        "\n3. Check for NaN and infinity."
        "\n4. Verify units."
        "\n5. Detect duplicate records when duplicates are not expected."
        "\n6. Investigate impossible values."
        "\n7. Confirm that frequency and weight definitions are correct."
        "\n8. Check whether the sample is representative for the intended use."
    )

    print(
        "\nSecurity:"
        "\n- Validate externally supplied data before processing."
        "\n- Avoid executing user-provided expressions as Python code."
        "\n- Limit resource consumption when processing untrusted huge datasets."
        "\n- Protect sensitive datasets from unauthorized disclosure."
        "\n- Treat statistical output as potentially sensitive when it can reveal "
        "information about individuals."
    )


# ---------------------------------------------------------------------------
# 37. INTERPRETATION RULES
# ---------------------------------------------------------------------------

def explain_interpretation() -> None:
    print_section("36. Interpretation principles")

    print(
        "Mean:"
        "\nUse when the arithmetic average is meaningful and extreme values "
        "do not dominate the interpretation."
    )

    print(
        "\nMedian:"
        "\nUse when data is skewed, contains outliers, or when the central "
        "ordered position is more representative."
    )

    print(
        "\nMode:"
        "\nUse when frequency is important or when working with categorical "
        "data."
    )

    print(
        "\nVariance:"
        "\nUse when squared deviations are mathematically appropriate. "
        "Remember that its units are squared."
    )

    print(
        "\nStandard deviation:"
        "\nUse when a spread measure in the original units is easier to "
        "interpret."
    )

    print(
        "\nIQR and MAD:"
        "\nUse when robust measures are preferred because extreme observations "
        "may distort mean-based measures."
    )


# ---------------------------------------------------------------------------
# 38. MULTIPLE CALCULATIONS IN ONE EXAMPLE
# ---------------------------------------------------------------------------

def integrated_case_study() -> None:
    print_section("37. Integrated case study")

    response_times = [
        120,
        135,
        128,
        142,
        131,
        127,
        150,
        129,
        133,
        138,
        500,
    ]

    print("System response times in milliseconds:")
    print(response_times)

    profile = describe(response_times)

    print("\nDescriptive profile:")
    print(f"Count: {profile.count}")
    print(f"Minimum: {profile.minimum}")
    print(f"Maximum: {profile.maximum}")
    print(f"Range: {profile.range}")
    print(f"Mean: {profile.mean:.2f}")
    print(f"Median: {profile.median:.2f}")
    print(f"Mode(s): {profile.modes}")
    print(
        "Population variance:",
        f"{profile.population_variance:.2f}",
    )
    print(
        "Population SD:",
        f"{profile.population_standard_deviation:.2f}",
    )
    print(f"Q1: {profile.q1:.2f}")
    print(f"Q3: {profile.q3:.2f}")
    print(f"IQR: {profile.iqr:.2f}")
    print(f"MAD: {profile.mad:.2f}")

    print("\nPotential IQR outliers:", iqr_outliers(response_times))

    print("\nZ-scores:")
    for value, z in zip(response_times, z_scores(response_times)):
        print(f"{value:>4} ms -> z = {z:>7.3f}")

    print(
        "\nInterpretation:"
        "\nThe 500 ms observation strongly increases the mean and standard "
        "deviation. Median, IQR and MAD provide a more robust view of the "
        "typical response-time behavior."
    )


# ---------------------------------------------------------------------------
# 39. MAIN EXECUTION
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the complete descriptive statistics learning program."""

    explain_foundations()
    demonstrate_mean()
    demonstrate_median()
    demonstrate_mode()
    demonstrate_range()
    demonstrate_quartiles()
    demonstrate_variance()
    demonstrate_standard_deviation()
    compare_population_and_sample()
    compare_datasets()
    demonstrate_outliers()
    demonstrate_skewness()
    demonstrate_frequency_data()
    demonstrate_grouped_data()
    demonstrate_robust_statistics()
    demonstrate_percentiles()
    demonstrate_coefficient_of_variation()
    demonstrate_welford()
    demonstrate_numerical_stability()
    demonstrate_decimal_precision()
    demonstrate_describe()
    demonstrate_iqr_outliers()
    demonstrate_z_scores()
    demonstrate_relative_deviation()
    student_score_analysis()
    business_sales_analysis()
    investment_return_analysis()
    delivery_time_analysis()
    demonstrate_edge_cases()
    demonstrate_common_mistakes()
    measure_comparison()
    verify_against_statistics_module()
    run_tests()
    explain_performance()
    explain_data_quality_and_security()
    explain_interpretation()
    integrated_case_study()

    print_section("End of descriptive statistics study script")

    print(
        "The program demonstrated mean, median, mode, variance, standard "
        "deviation and related descriptive measures through executable "
        "implementations and examples."
    )


if __name__ == "__main__":
    main()
