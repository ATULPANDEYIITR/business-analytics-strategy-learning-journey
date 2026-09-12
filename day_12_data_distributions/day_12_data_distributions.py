"""
Data Distributions: Normal, Skewed, and Categorical Distributions
===================================================================

A standalone educational script covering data distributions from beginner
through advanced level.

Topics covered
--------------
1. What a data distribution is
2. Population versus sample
3. Variables and measurement scales
4. Frequency distributions
5. Relative frequency and cumulative frequency
6. Histograms and bins
7. Probability mass functions for categorical data
8. Probability density and continuous data
9. Mean, median, mode, variance, standard deviation
10. Quantiles and percentiles
11. Normal distributions
12. Standard normal distributions and z-scores
13. Empirical rules
14. Sampling from a normal distribution
15. Right-skewed and left-skewed distributions
16. Log transformation and skewness reduction
17. Categorical distributions
18. Binary and multinomial categorical data
19. Joint and conditional categorical distributions
20. Distribution shape and outliers
21. Sampling distributions and the Central Limit Theorem
22. Law of Large Numbers
23. Empirical CDF
24. Probability calculations
25. Distribution comparison
26. Simple kernel density estimation
27. Robust statistics
28. Data validation and edge cases
29. Practical interpretation
30. Testing and reproducibility

Only Python's standard library is used.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass
from statistics import mean, median, multimode, variance, stdev
from typing import Any, Iterable, Sequence


# =============================================================================
# SECTION 1: BASIC CONCEPTS
# =============================================================================

def print_title(title: str) -> None:
    """Print a readable section title."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_subtitle(title: str) -> None:
    """Print a smaller subsection title."""
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


def explain_distribution() -> None:
    """
    Demonstrate the basic idea of a distribution.

    A distribution describes how observations are allocated across possible
    values. The values can be numeric or categorical.
    """
    print_title("1. What Is a Data Distribution?")

    data = [2, 3, 3, 4, 4, 4, 5, 5, 6]

    frequencies = Counter(data)

    print("Data:", data)
    print("Frequency table:")

    for value in sorted(frequencies):
        print(f"  Value {value}: {frequencies[value]} observation(s)")

    total = len(data)

    print("\nRelative frequencies:")
    for value in sorted(frequencies):
        relative_frequency = frequencies[value] / total
        print(f"  Value {value}: {relative_frequency:.3f}")

    print(
        "\nA distribution answers questions such as which values are common, "
        "which values are rare, how spread out the observations are, and "
        "whether the data has a particular shape."
    )


# =============================================================================
# SECTION 2: POPULATION, SAMPLE, AND VARIABLE TYPES
# =============================================================================

def explain_population_and_sample() -> None:
    print_title("2. Population, Sample, and Variable Types")

    population = list(range(1, 101))
    sample = [12, 18, 27, 31, 44, 56, 63, 71, 82, 95]

    print("Population example:")
    print(f"  Number of observations: {len(population)}")
    print(f"  Population mean: {mean(population):.2f}")

    print("\nSample example:")
    print(f"  Sample: {sample}")
    print(f"  Sample mean: {mean(sample):.2f}")

    print("\nCommon variable classifications:")
    classifications = {
        "Nominal": "Categories without an intrinsic order",
        "Ordinal": "Categories with an order",
        "Discrete": "Countable numerical values",
        "Continuous": "Numerical measurements that can take values on a continuum",
    }

    for name, definition in classifications.items():
        print(f"  {name}: {definition}")

    print("\nExamples:")
    print("  Nominal: department = Sales, HR, Finance")
    print("  Ordinal: satisfaction = Poor, Fair, Good, Excellent")
    print("  Discrete: number of purchases")
    print("  Continuous: height, weight, temperature")


# =============================================================================
# SECTION 3: DESCRIPTIVE STATISTICS
# =============================================================================

def population_variance(data: Sequence[float]) -> float:
    """Calculate population variance."""
    if not data:
        raise ValueError("Cannot calculate variance of an empty dataset.")

    average = sum(data) / len(data)
    return sum((x - average) ** 2 for x in data) / len(data)


def population_standard_deviation(data: Sequence[float]) -> float:
    """Calculate population standard deviation."""
    return math.sqrt(population_variance(data))


def percentile(data: Sequence[float], p: float) -> float:
    """
    Calculate a percentile using linear interpolation.

    p must be between 0 and 100.
    """
    if not data:
        raise ValueError("Cannot calculate a percentile of an empty dataset.")

    if not 0 <= p <= 100:
        raise ValueError("Percentile must be between 0 and 100.")

    ordered = sorted(data)

    if len(ordered) == 1:
        return float(ordered[0])

    position = (len(ordered) - 1) * p / 100
    lower_index = math.floor(position)
    upper_index = math.ceil(position)

    if lower_index == upper_index:
        return float(ordered[lower_index])

    fraction = position - lower_index

    return (
        ordered[lower_index]
        + fraction * (ordered[upper_index] - ordered[lower_index])
    )


def quartiles(data: Sequence[float]) -> tuple[float, float, float]:
    """Return Q1, median, and Q3."""
    return (
        percentile(data, 25),
        percentile(data, 50),
        percentile(data, 75),
    )


def interquartile_range(data: Sequence[float]) -> float:
    """Return IQR = Q3 - Q1."""
    q1, _, q3 = quartiles(data)
    return q3 - q1


def sample_skewness(data: Sequence[float]) -> float:
    """
    Calculate adjusted Fisher-Pearson sample skewness.

    Positive values generally indicate a longer right tail.
    Negative values generally indicate a longer left tail.
    """
    n = len(data)

    if n < 3:
        raise ValueError("At least three observations are required.")

    average = mean(data)
    sample_sd = stdev(data)

    if sample_sd == 0:
        return 0.0

    numerator = sum((x - average) ** 3 for x in data)

    return (n / ((n - 1) * (n - 2))) * numerator / (sample_sd ** 3)


def sample_kurtosis_excess(data: Sequence[float]) -> float:
    """
    Calculate adjusted excess kurtosis.

    Excess kurtosis is approximately 0 for a normal distribution.
    """
    n = len(data)

    if n < 4:
        raise ValueError("At least four observations are required.")

    average = mean(data)
    sample_sd = stdev(data)

    if sample_sd == 0:
        return 0.0

    m2 = sum((x - average) ** 2 for x in data)
    m4 = sum((x - average) ** 4 for x in data)

    term1 = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3)))
    term2 = m4 / (sample_sd ** 4)

    term3 = 3 * ((n - 1) ** 2) / ((n - 2) * (n - 3))

    return term1 * term2 - term3


def describe_numeric(data: Sequence[float], name: str = "Data") -> None:
    """Print a comprehensive numerical distribution summary."""
    if not data:
        raise ValueError("Dataset cannot be empty.")

    q1, q2, q3 = quartiles(data)

    print_subtitle(f"Descriptive Statistics: {name}")

    print(f"Count:              {len(data)}")
    print(f"Minimum:            {min(data):.4f}")
    print(f"Q1:                 {q1:.4f}")
    print(f"Median:             {q2:.4f}")
    print(f"Q3:                 {q3:.4f}")
    print(f"Maximum:            {max(data):.4f}")
    print(f"Mean:               {mean(data):.4f}")

    if len(data) >= 2:
        print(f"Sample variance:    {variance(data):.4f}")
        print(f"Sample std. dev.:   {stdev(data):.4f}")

    print(f"Population variance:{population_variance(data):.4f}")
    print(f"Population std.:    {population_standard_deviation(data):.4f}")
    print(f"IQR:                {q3 - q1:.4f}")

    if len(data) >= 3:
        print(f"Skewness:            {sample_skewness(data):.4f}")

    if len(data) >= 4:
        print(f"Excess kurtosis:    {sample_kurtosis_excess(data):.4f}")

    print(f"Modes:              {multimode(data)}")


# =============================================================================
# SECTION 4: FREQUENCY DISTRIBUTIONS
# =============================================================================

def frequency_distribution(data: Sequence[Any]) -> list[tuple[Any, int, float]]:
    """Return value, count, and relative frequency."""
    if not data:
        return []

    counts = Counter(data)
    total = len(data)

    return [
        (value, counts[value], counts[value] / total)
        for value in sorted(counts, key=lambda x: str(x))
    ]


def print_frequency_table(data: Sequence[Any]) -> None:
    """Print a frequency table."""
    print_subtitle("Frequency Distribution")

    print(f"{'Value':<20} {'Frequency':>10} {'Relative':>12}")

    for value, count, relative in frequency_distribution(data):
        print(f"{str(value):<20} {count:>10} {relative:>11.2%}")


def make_numeric_bins(
    data: Sequence[float],
    number_of_bins: int = 10,
) -> list[tuple[float, float, int]]:
    """
    Create equal-width histogram bins.

    The final bin includes its upper boundary.
    """
    if not data:
        raise ValueError("Data cannot be empty.")

    if number_of_bins <= 0:
        raise ValueError("Number of bins must be positive.")

    minimum = min(data)
    maximum = max(data)

    if minimum == maximum:
        return [(minimum, maximum, len(data))]

    width = (maximum - minimum) / number_of_bins
    counts = [0] * number_of_bins

    for value in data:
        index = int((value - minimum) / width)

        if index == number_of_bins:
            index -= 1

        counts[index] += 1

    bins = []

    for index, count in enumerate(counts):
        lower = minimum + index * width
        upper = minimum + (index + 1) * width
        bins.append((lower, upper, count))

    return bins


def print_histogram(
    data: Sequence[float],
    number_of_bins: int = 10,
    width: int = 50,
) -> None:
    """
    Print an ASCII histogram.

    This demonstrates the concept without requiring plotting libraries.
    """
    print_subtitle("Histogram")

    bins = make_numeric_bins(data, number_of_bins)
    maximum_count = max(count for _, _, count in bins)

    for lower, upper, count in bins:
        bar_length = 0

        if maximum_count:
            bar_length = round(width * count / maximum_count)

        bar = "#" * bar_length

        print(
            f"{lower:9.2f} to {upper:9.2f} | "
            f"{bar:<{width}} {count}"
        )


# =============================================================================
# SECTION 5: NORMAL DISTRIBUTION
# =============================================================================

def normal_pdf(
    x: float,
    mu: float = 0.0,
    sigma: float = 1.0,
) -> float:
    """
    Probability density function of a normal distribution.

    f(x) = 1/(sigma*sqrt(2*pi)) *
           exp(-0.5*((x-mu)/sigma)^2)
    """
    if sigma <= 0:
        raise ValueError("Standard deviation must be positive.")

    coefficient = 1 / (sigma * math.sqrt(2 * math.pi))
    exponent = -0.5 * ((x - mu) / sigma) ** 2

    return coefficient * math.exp(exponent)


def normal_cdf(
    x: float,
    mu: float = 0.0,
    sigma: float = 1.0,
) -> float:
    """Cumulative distribution function of a normal distribution."""
    if sigma <= 0:
        raise ValueError("Standard deviation must be positive.")

    z = (x - mu) / (sigma * math.sqrt(2))
    return 0.5 * (1 + math.erf(z))


def z_score(
    x: float,
    mu: float,
    sigma: float,
) -> float:
    """Convert an observation to a standard score."""
    if sigma <= 0:
        raise ValueError("Standard deviation must be positive.")

    return (x - mu) / sigma


def normal_distribution_demo() -> None:
    print_title("5. Normal Distribution")

    mu = 100
    sigma = 15

    print(f"Mean (mu): {mu}")
    print(f"Standard deviation (sigma): {sigma}")

    values = [70, 85, 100, 115, 130]

    print("\nPDF values:")
    for x in values:
        print(f"  x={x:3}: density={normal_pdf(x, mu, sigma):.6f}")

    print("\nCDF values:")
    for x in values:
        probability = normal_cdf(x, mu, sigma)
        print(f"  P(X <= {x}) = {probability:.4%}")

    print("\nZ-scores:")
    for x in values:
        print(f"  x={x:3}: z={z_score(x, mu, sigma):.2f}")

    print("\nEmpirical rule for a normal distribution:")
    print("  Approximately 68% of observations lie within ±1 SD.")
    print("  Approximately 95% lie within ±2 SD.")
    print("  Approximately 99.7% lie within ±3 SD.")

    lower_1sd = mu - sigma
    upper_1sd = mu + sigma
    lower_2sd = mu - 2 * sigma
    upper_2sd = mu + 2 * sigma

    probability_1sd = (
        normal_cdf(upper_1sd, mu, sigma)
        - normal_cdf(lower_1sd, mu, sigma)
    )

    probability_2sd = (
        normal_cdf(upper_2sd, mu, sigma)
        - normal_cdf(lower_2sd, mu, sigma)
    )

    print(f"\nExact normal probability within ±1 SD: {probability_1sd:.4%}")
    print(f"Exact normal probability within ±2 SD: {probability_2sd:.4%}")


def normal_probability_examples() -> None:
    print_subtitle("Normal Probability Calculations")

    mu = 50
    sigma = 10

    less_than_60 = normal_cdf(60, mu, sigma)

    greater_than_60 = 1 - normal_cdf(60, mu, sigma)

    between_40_and_60 = (
        normal_cdf(60, mu, sigma)
        - normal_cdf(40, mu, sigma)
    )

    print(f"P(X < 60):       {less_than_60:.4%}")
    print(f"P(X > 60):       {greater_than_60:.4%}")
    print(f"P(40 < X < 60):  {between_40_and_60:.4%}")


# =============================================================================
# SECTION 6: SAMPLING FROM A NORMAL DISTRIBUTION
# =============================================================================

def generate_normal_sample(
    size: int,
    mu: float,
    sigma: float,
    seed: int | None = None,
) -> list[float]:
    """Generate reproducible normal observations."""
    if size <= 0:
        raise ValueError("Sample size must be positive.")

    if sigma <= 0:
        raise ValueError("Standard deviation must be positive.")

    generator = random.Random(seed)

    return [
        generator.gauss(mu, sigma)
        for _ in range(size)
    ]


def normal_sampling_demo() -> None:
    print_title("6. Sampling from a Normal Distribution")

    sample = generate_normal_sample(
        size=1000,
        mu=100,
        sigma=15,
        seed=42,
    )

    describe_numeric(sample, "Simulated Normal Data")
    print_histogram(sample, number_of_bins=12, width=45)


# =============================================================================
# SECTION 7: SKEWED DISTRIBUTIONS
# =============================================================================

def generate_right_skewed_data(
    size: int,
    seed: int = 42,
) -> list[float]:
    """
    Generate right-skewed data using an exponential distribution.

    The exponential distribution has a long right tail.
    """
    if size <= 0:
        raise ValueError("Size must be positive.")

    generator = random.Random(seed)

    return [
        generator.expovariate(1 / 20)
        for _ in range(size)
    ]


def generate_left_skewed_data(
    size: int,
    seed: int = 42,
) -> list[float]:
    """
    Generate left-skewed data by reflecting exponential observations.

    If Y is right-skewed, -Y is left-skewed.
    """
    right_skewed = generate_right_skewed_data(size, seed)
    return [100 - x for x in right_skewed]


def compare_mean_and_median(data: Sequence[float]) -> str:
    """Interpret skewness using the relationship between mean and median."""
    average = mean(data)
    middle = median(data)

    if average > middle:
        return "Mean > median: this is consistent with right skew."

    if average < middle:
        return "Mean < median: this is consistent with left skew."

    return "Mean ≈ median: this relationship alone does not indicate skew."


def skewness_demo() -> None:
    print_title("7. Skewed Distributions")

    right_skewed = generate_right_skewed_data(1000, seed=42)
    left_skewed = generate_left_skewed_data(1000, seed=42)

    describe_numeric(right_skewed, "Right-Skewed Data")

    print("\nInterpretation:")
    print(compare_mean_and_median(right_skewed))

    describe_numeric(left_skewed, "Left-Skewed Data")

    print("\nInterpretation:")
    print(compare_mean_and_median(left_skewed))

    print("\nTypical patterns:")
    print("  Right skew: long tail toward larger values.")
    print("  Left skew:  long tail toward smaller values.")
    print("  Symmetric:  left and right sides have broadly similar shape.")

    print_histogram(right_skewed, number_of_bins=12, width=45)


# =============================================================================
# SECTION 8: TRANSFORMATIONS AND SKEWNESS
# =============================================================================

def safe_log_transform(data: Sequence[float]) -> list[float]:
    """
    Apply log(1+x) so that zero is allowed.

    Negative values below -1 are invalid.
    """
    if any(x < -1 for x in data):
        raise ValueError("log1p transformation requires x >= -1.")

    return [math.log1p(x) for x in data]


def exponential_transform(data: Sequence[float]) -> list[float]:
    """Apply exp(x) to demonstrate how skewness can increase."""
    return [math.exp(x) for x in data]


def transformation_demo() -> None:
    print_title("8. Transformations and Distribution Shape")

    original = generate_right_skewed_data(1000, seed=10)

    transformed = safe_log_transform(original)

    print("Original right-skewed data:")
    print(
        f"  Mean={mean(original):.3f}, "
        f"Median={median(original):.3f}, "
        f"Skewness={sample_skewness(original):.3f}"
    )

    print("\nAfter log(1+x) transformation:")
    print(
        f"  Mean={mean(transformed):.3f}, "
        f"Median={median(transformed):.3f}, "
        f"Skewness={sample_skewness(transformed):.3f}"
    )

    print(
        "\nLog transformations often reduce right skew when a variable "
        "contains multiplicative effects or spans several orders of magnitude."
    )

    print("\nImportant caution:")
    print(
        "A transformation changes the scale and interpretation of the "
        "variable. It should not be applied merely to force data to look normal."
    )


# =============================================================================
# SECTION 9: CATEGORICAL DISTRIBUTIONS
# =============================================================================

def categorical_distribution(
    categories: Sequence[Any],
) -> dict[Any, float]:
    """Calculate empirical category probabilities."""
    if not categories:
        raise ValueError("Categories cannot be empty.")

    counts = Counter(categories)
    total = len(categories)

    return {
        category: count / total
        for category, count in counts.items()
    }


def print_categorical_distribution(
    categories: Sequence[Any],
) -> None:
    """Print category counts and probabilities."""
    print_subtitle("Categorical Distribution")

    counts = Counter(categories)
    total = len(categories)

    print(f"{'Category':<20} {'Count':>10} {'Probability':>14}")

    for category, count in sorted(
        counts.items(),
        key=lambda item: str(item[0]),
    ):
        print(
            f"{str(category):<20} "
            f"{count:>10} "
            f"{count / total:>13.2%}"
        )


def categorical_demo() -> None:
    print_title("9. Categorical Distributions")

    product_choices = [
        "Basic",
        "Premium",
        "Premium",
        "Basic",
        "Enterprise",
        "Premium",
        "Basic",
        "Enterprise",
        "Premium",
        "Basic",
        "Premium",
        "Enterprise",
    ]

    print("Observed categories:")
    print(product_choices)

    print_categorical_distribution(product_choices)

    print("\nInterpretation:")
    print(
        "For categorical data, the empirical distribution is represented "
        "by the proportion of observations belonging to each category."
    )

    print("\nCategorical variables:")
    print("  Nominal: category order has no numerical meaning.")
    print("  Ordinal: category order carries information.")
    print("  Binary: exactly two categories.")
    print("  Multinomial: more than two possible categories.")


# =============================================================================
# SECTION 10: BINARY AND MULTINOMIAL DISTRIBUTIONS
# =============================================================================

def bernoulli_pmf(x: int, p: float) -> float:
    """
    Probability mass function for a Bernoulli random variable.

    X = 1 with probability p
    X = 0 with probability 1-p
    """
    if not 0 <= p <= 1:
        raise ValueError("p must be between 0 and 1.")

    if x == 1:
        return p

    if x == 0:
        return 1 - p

    return 0.0


def binomial_pmf(
    k: int,
    n: int,
    p: float,
) -> float:
    """
    Probability mass function of a Binomial(n, p) distribution.

    P(X=k) = C(n,k) p^k (1-p)^(n-k)
    """
    if n < 0:
        raise ValueError("n must be non-negative.")

    if not 0 <= p <= 1:
        raise ValueError("p must be between 0 and 1.")

    if k < 0 or k > n:
        return 0.0

    combinations = math.comb(n, k)

    return combinations * (p ** k) * ((1 - p) ** (n - k))


def multinomial_probability(
    counts: Sequence[int],
    probabilities: Sequence[float],
) -> float:
    """
    Calculate a multinomial probability.

    counts[i] represents the number of observations in category i.
    probabilities[i] represents the probability of category i.

    P = n! / product(k_i!) * product(p_i ^ k_i)
    """
    if len(counts) != len(probabilities):
        raise ValueError("Counts and probabilities must have equal length.")

    if any(count < 0 for count in counts):
        raise ValueError("Counts cannot be negative.")

    if any(p < 0 for p in probabilities):
        raise ValueError("Probabilities cannot be negative.")

    if not math.isclose(sum(probabilities), 1.0, rel_tol=1e-9):
        raise ValueError("Probabilities must sum to 1.")

    n = sum(counts)

    coefficient = math.factorial(n)

    for count in counts:
        coefficient /= math.factorial(count)

    probability_product = 1.0

    for count, probability in zip(counts, probabilities):
        if probability == 0 and count > 0:
            return 0.0

        probability_product *= probability ** count

    return coefficient * probability_product


def categorical_probability_demo() -> None:
    print_title("10. Bernoulli, Binomial, and Multinomial Distributions")

    p = 0.7

    print("Bernoulli distribution:")
    print(f"  P(X=1) = {bernoulli_pmf(1, p):.3f}")
    print(f"  P(X=0) = {bernoulli_pmf(0, p):.3f}")

    print("\nBinomial distribution:")
    n = 10

    for k in range(n + 1):
        probability = binomial_pmf(k, n, p)
        print(f"  P(X={k:2}) = {probability:.6f}")

    print("\nMultinomial example:")
    counts = [4, 3, 3]
    probabilities = [0.4, 0.3, 0.3]

    probability = multinomial_probability(
        counts,
        probabilities,
    )

    print(f"  Counts: {counts}")
    print(f"  Probabilities: {probabilities}")
    print(f"  Probability: {probability:.6f}")


# =============================================================================
# SECTION 11: JOINT AND CONDITIONAL CATEGORICAL DISTRIBUTIONS
# =============================================================================

def joint_frequency_table(
    pairs: Sequence[tuple[Any, Any]],
) -> Counter:
    """Create a joint frequency table from paired categorical observations."""
    return Counter(pairs)


def conditional_probability(
    pairs: Sequence[tuple[Any, Any]],
    target: Any,
    given: Any,
) -> float:
    """
    Calculate P(target first variable | second variable = given).

    P(A|B) = count(A and B) / count(B)
    """
    denominator = sum(
        1 for first, second in pairs
        if second == given
    )

    if denominator == 0:
        raise ValueError("Conditioning category does not occur.")

    numerator = sum(
        1 for first, second in pairs
        if first == target and second == given
    )

    return numerator / denominator


def categorical_joint_demo() -> None:
    print_title("11. Joint and Conditional Categorical Distributions")

    observations = [
        ("Buy", "Mobile"),
        ("No Buy", "Desktop"),
        ("Buy", "Mobile"),
        ("Buy", "Desktop"),
        ("No Buy", "Mobile"),
        ("Buy", "Tablet"),
        ("No Buy", "Desktop"),
        ("Buy", "Mobile"),
        ("Buy", "Desktop"),
        ("No Buy", "Tablet"),
        ("Buy", "Mobile"),
        ("No Buy", "Mobile"),
    ]

    joint_counts = joint_frequency_table(observations)

    print("Joint frequencies:")
    for pair, count in sorted(
        joint_counts.items(),
        key=lambda item: str(item[0]),
    ):
        print(f"  {pair}: {count}")

    probability = conditional_probability(
        observations,
        target="Buy",
        given="Mobile",
    )

    print(
        f"\nP(Buy | Mobile) = {probability:.2%}"
    )

    print(
        "\nA joint distribution describes combinations of variables. "
        "A conditional distribution describes one variable after fixing "
        "the value of another variable."
    )


# =============================================================================
# SECTION 12: OUTLIERS AND ROBUST DISTRIBUTION DESCRIPTIONS
# =============================================================================

def iqr_outliers(data: Sequence[float]) -> list[float]:
    """Detect observations outside the standard 1.5*IQR fences."""
    if not data:
        return []

    q1, _, q3 = quartiles(data)
    iqr = q3 - q1

    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    return [
        value
        for value in data
        if value < lower_fence or value > upper_fence
    ]


def robust_statistics(data: Sequence[float]) -> dict[str, float]:
    """Return statistics less sensitive to extreme observations."""
    q1, middle, q3 = quartiles(data)

    return {
        "median": middle,
        "IQR": q3 - q1,
        "Q1": q1,
        "Q3": q3,
    }


def outlier_demo() -> None:
    print_title("12. Outliers and Robust Statistics")

    data_without_outlier = [
        48, 49, 50, 51, 52, 53, 54, 55, 56
    ]

    data_with_outlier = data_without_outlier + [500]

    print("Without extreme outlier:")
    describe_numeric(data_without_outlier, "Baseline")

    print("\nWith extreme outlier:")
    describe_numeric(data_with_outlier, "With Outlier")

    print("\nIQR-based outliers:")
    print(iqr_outliers(data_with_outlier))

    print("\nRobust statistics:")
    for name, value in robust_statistics(data_with_outlier).items():
        print(f"  {name}: {value:.3f}")

    print(
        "\nThe mean and standard deviation can be strongly affected by "
        "extreme observations. The median and IQR are generally more robust."
    )


# =============================================================================
# SECTION 13: EMPIRICAL CDF
# =============================================================================

def empirical_cdf(
    data: Sequence[float],
    x: float,
) -> float:
    """
    Empirical cumulative distribution function.

    ECDF(x) = number of observations <= x / n
    """
    if not data:
        raise ValueError("Data cannot be empty.")

    count = sum(value <= x for value in data)
    return count / len(data)


def empirical_cdf_demo() -> None:
    print_title("13. Empirical Cumulative Distribution Function")

    data = [2, 3, 3, 4, 5, 7, 8, 10]

    print("Data:", data)

    for x in [2, 3, 4, 6, 10]:
        print(
            f"  ECDF({x}) = {empirical_cdf(data, x):.3f}"
        )

    print(
        "\nThe ECDF does not assume normality or another theoretical "
        "distribution. It directly describes the observed sample."
    )


# =============================================================================
# SECTION 14: LAW OF LARGE NUMBERS
# =============================================================================

def law_of_large_numbers_demo() -> None:
    print_title("14. Law of Large Numbers")

    generator = random.Random(42)

    running_total = 0.0

    sample_sizes = [1, 10, 100, 1_000, 10_000]

    target_mean = 0.5

    observations = []

    for index in range(1, max(sample_sizes) + 1):
        observation = generator.random()
        observations.append(observation)

    for size in sample_sizes:
        sample_mean = mean(observations[:size])

        print(
            f"Sample size={size:>5}: "
            f"sample mean={sample_mean:.5f}, "
            f"error={sample_mean - target_mean:+.5f}"
        )

    print(
        "\nAs the number of observations increases, the sample average "
        "tends to move toward the population expectation."
    )


# =============================================================================
# SECTION 15: CENTRAL LIMIT THEOREM
# =============================================================================

def sample_mean(
    data: Sequence[float],
    sample_size: int,
    generator: random.Random,
) -> float:
    """Take a random sample with replacement and calculate its mean."""
    if not data:
        raise ValueError("Population cannot be empty.")

    if sample_size <= 0:
        raise ValueError("Sample size must be positive.")

    sample = [
        generator.choice(data)
        for _ in range(sample_size)
    ]

    return mean(sample)


def central_limit_theorem_demo() -> None:
    print_title("15. Central Limit Theorem")

    population = generate_right_skewed_data(
        size=50_000,
        seed=100,
    )

    print(
        f"Population mean approximately: {mean(population):.3f}"
    )

    generator = random.Random(123)

    sample_sizes = [5, 30, 100]

    for sample_size in sample_sizes:
        means = [
            sample_mean(population, sample_size, generator)
            for _ in range(2000)
        ]

        print_subtitle(
            f"Sampling Distribution of the Mean: n={sample_size}"
        )

        print(f"Mean of sample means: {mean(means):.4f}")
        print(f"SD of sample means:   {stdev(means):.4f}")
        print(f"Skewness:             {sample_skewness(means):.4f}")

        print_histogram(
            means,
            number_of_bins=12,
            width=40,
        )

    print(
        "\nThe Central Limit Theorem states, under common regularity "
        "conditions, that the distribution of standardized sample means "
        "approaches a normal distribution as sample size increases."
    )

    print(
        "This concerns a distribution of sample statistics, not a claim "
        "that the original population must itself be normal."
    )


# =============================================================================
# SECTION 16: STANDARD ERROR
# =============================================================================

def standard_error_of_mean(
    sample_standard_deviation: float,
    sample_size: int,
) -> float:
    """Calculate the standard error of a sample mean."""
    if sample_size <= 0:
        raise ValueError("Sample size must be positive.")

    if sample_standard_deviation < 0:
        raise ValueError("Standard deviation cannot be negative.")

    return sample_standard_deviation / math.sqrt(sample_size)


def standard_error_demo() -> None:
    print_title("16. Standard Error of the Mean")

    sigma = 20

    for n in [4, 25, 100, 400, 1600]:
        se = standard_error_of_mean(sigma, n)
        print(f"n={n:4}: SE={se:.4f}")

    print(
        "\nThe standard error decreases at a rate proportional to "
        "1/sqrt(n). Quadrupling the sample size approximately halves "
        "the standard error."
    )


# =============================================================================
# SECTION 17: SIMPLE KERNEL DENSITY ESTIMATION
# =============================================================================

def gaussian_kernel(u: float) -> float:
    """Gaussian kernel function."""
    return math.exp(-0.5 * u * u) / math.sqrt(2 * math.pi)


def kernel_density_estimate(
    data: Sequence[float],
    x: float,
    bandwidth: float,
) -> float:
    """
    Estimate density at x using Gaussian kernel density estimation.

    KDE(x) = 1/(n*h) * sum K((x-x_i)/h)
    """
    if not data:
        raise ValueError("Data cannot be empty.")

    if bandwidth <= 0:
        raise ValueError("Bandwidth must be positive.")

    total = sum(
        gaussian_kernel((x - observation) / bandwidth)
        for observation in data
    )

    return total / (len(data) * bandwidth)


def silverman_bandwidth(data: Sequence[float]) -> float:
    """
    Silverman's rule-of-thumb bandwidth.

    h = 0.9 * min(SD, IQR/1.34) * n^(-1/5)
    """
    if len(data) < 2:
        raise ValueError("At least two observations are required.")

    sample_sd = stdev(data)
    iqr = interquartile_range(data)

    scale = min(sample_sd, iqr / 1.34)

    if scale == 0:
        scale = sample_sd

    if scale == 0:
        raise ValueError("Bandwidth cannot be determined from constant data.")

    return 0.9 * scale * (len(data) ** (-1 / 5))


def kde_demo() -> None:
    print_title("17. Kernel Density Estimation")

    data = generate_normal_sample(
        size=250,
        mu=0,
        sigma=1,
        seed=7,
    )

    bandwidth = silverman_bandwidth(data)

    print(f"Estimated bandwidth: {bandwidth:.5f}")

    for x in [-3, -2, -1, 0, 1, 2, 3]:
        density = kernel_density_estimate(
            data,
            x,
            bandwidth,
        )

        print(f"  KDE({x:+.0f}) = {density:.6f}")

    print(
        "\nKDE produces a smooth estimate of an underlying density. "
        "The bandwidth controls the amount of smoothing."
    )

    print(
        "A small bandwidth can produce a noisy estimate. "
        "A large bandwidth can oversmooth important structure."
    )


# =============================================================================
# SECTION 18: QUANTILES AND PERCENTILES
# =============================================================================

def percentile_demo() -> None:
    print_title("18. Quantiles and Percentiles")

    data = [
        12, 15, 17, 19, 21,
        24, 28, 31, 35, 40,
    ]

    print("Data:", data)

    for p in [0, 10, 25, 50, 75, 90, 100]:
        print(
            f"  {p:>3}th percentile = {percentile(data, p):.2f}"
        )

    q1, q2, q3 = quartiles(data)

    print("\nQuartiles:")
    print(f"  Q1 = {q1:.2f}")
    print(f"  Q2 = {q2:.2f}")
    print(f"  Q3 = {q3:.2f}")

    print(
        "\nA percentile identifies a location in the ordered distribution. "
        "For example, the 90th percentile is a value at or below which "
        "approximately 90% of observations fall, according to the chosen "
        "percentile convention."
    )


# =============================================================================
# SECTION 19: DISTRIBUTION SHAPE
# =============================================================================

def distribution_shape_interpretation(
    data: Sequence[float],
) -> str:
    """Provide a simple shape classification using skewness."""
    skew = sample_skewness(data)

    if skew > 1:
        return "Strong right skew"

    if skew > 0.5:
        return "Moderate right skew"

    if skew < -1:
        return "Strong left skew"

    if skew < -0.5:
        return "Moderate left skew"

    return "Approximately symmetric by this skewness rule"


def distribution_shape_demo() -> None:
    print_title("19. Distribution Shape")

    datasets = {
        "Normal": generate_normal_sample(
            2000,
            0,
            1,
            seed=5,
        ),
        "Right skewed": generate_right_skewed_data(
            2000,
            seed=5,
        ),
        "Left skewed": generate_left_skewed_data(
            2000,
            seed=5,
        ),
    }

    for name, data in datasets.items():
        skew = sample_skewness(data)

        print(
            f"{name:<15} "
            f"mean={mean(data):8.3f} "
            f"median={median(data):8.3f} "
            f"skewness={skew:8.3f} "
            f"shape={distribution_shape_interpretation(data)}"
        )

    print(
        "\nSkewness is a useful numerical descriptor, but shape should "
        "not be diagnosed from one statistic alone."
    )


# =============================================================================
# SECTION 20: NORMALITY IS NOT THE SAME AS SYMMETRY
# =============================================================================

def normality_distinction_demo() -> None:
    print_title("20. Normality, Symmetry, and Distribution Shape")

    print("Important distinctions:")
    print(
        "  Symmetry means the distribution is broadly balanced around "
        "a central location."
    )
    print(
        "  Normality means the distribution follows the mathematical "
        "normal distribution."
    )
    print(
        "  A distribution can be symmetric without being normal."
    )
    print(
        "  A distribution can have skewness near zero while still "
        "differing substantially from a normal distribution."
    )
    print(
        "  A histogram alone cannot establish that data came from "
        "a normal population."
    )


# =============================================================================
# SECTION 21: DISCRETE VS CONTINUOUS DISTRIBUTIONS
# =============================================================================

def discrete_vs_continuous_demo() -> None:
    print_title("21. Discrete and Continuous Distributions")

    print("Discrete example:")
    print("  Number of support tickets = 0, 1, 2, 3, ...")
    print("  Individual values can have non-zero probability.")

    print("\nContinuous example:")
    print("  Response time = any non-negative real-valued measurement")
    print(
        "  For an ideal continuous distribution, the probability of "
        "one exact point is zero."
    )

    print("\nKey distinction:")
    print(
        "  PMF: probability assigned to discrete values."
    )
    print(
        "  PDF: density, not probability at a single point."
    )
    print(
        "  CDF: accumulated probability up to a specified value."
    )


# =============================================================================
# SECTION 22: DISCRETE DISTRIBUTION ASCII DISPLAY
# =============================================================================

def print_discrete_pmf(
    probabilities: dict[Any, float],
    width: int = 50,
) -> None:
    """Display a probability mass function using ASCII bars."""
    if not probabilities:
        return

    maximum = max(probabilities.values())

    for category, probability in probabilities.items():
        bar_length = (
            round(width * probability / maximum)
            if maximum > 0
            else 0
        )

        print(
            f"{str(category):<15} "
            f"{'#' * bar_length:<{width}} "
            f"{probability:.4f}"
        )


def pmf_visualization_demo() -> None:
    print_title("22. PMF Visualization")

    probabilities = {
        "A": 0.10,
        "B": 0.20,
        "C": 0.45,
        "D": 0.15,
        "E": 0.10,
    }

    print_discrete_pmf(probabilities)

    print(
        "\nA PMF must satisfy two fundamental conditions:"
    )
    print("  1. Every probability is between 0 and 1.")
    print("  2. All probabilities sum to 1.")


# =============================================================================
# SECTION 23: EXPECTATION AND VARIANCE OF A DISCRETE DISTRIBUTION
# =============================================================================

def discrete_expectation(
    values: Sequence[float],
    probabilities: Sequence[float],
) -> float:
    """Calculate E[X] for a finite discrete distribution."""
    if len(values) != len(probabilities):
        raise ValueError("Values and probabilities must have equal lengths.")

    if any(p < 0 for p in probabilities):
        raise ValueError("Probabilities cannot be negative.")

    if not math.isclose(sum(probabilities), 1.0, rel_tol=1e-9):
        raise ValueError("Probabilities must sum to 1.")

    return sum(
        value * probability
        for value, probability in zip(values, probabilities)
    )


def discrete_variance(
    values: Sequence[float],
    probabilities: Sequence[float],
) -> float:
    """Calculate Var(X) = E[X^2] - E[X]^2."""
    expected_value = discrete_expectation(values, probabilities)

    expected_square = sum(
        value ** 2 * probability
        for value, probability in zip(values, probabilities)
    )

    return expected_square - expected_value ** 2


def expectation_demo() -> None:
    print_title("23. Expected Value and Variance")

    values = [0, 1, 2, 3]
    probabilities = [0.1, 0.2, 0.4, 0.3]

    expected = discrete_expectation(
        values,
        probabilities,
    )

    variance_value = discrete_variance(
        values,
        probabilities,
    )

    print(f"Values:        {values}")
    print(f"Probabilities: {probabilities}")
    print(f"E[X]:          {expected:.4f}")
    print(f"Var(X):        {variance_value:.4f}")
    print(f"SD(X):         {math.sqrt(variance_value):.4f}")


# =============================================================================
# SECTION 24: DATA QUALITY AND EDGE CASES
# =============================================================================

def validate_numeric_data(
    data: Iterable[Any],
) -> list[float]:
    """
    Validate and normalize numerical observations.

    Boolean values are rejected because bool is a subclass of int in Python.
    """
    cleaned = []

    for index, value in enumerate(data):
        if isinstance(value, bool):
            raise TypeError(
                f"Observation {index} is boolean, not numerical data."
            )

        if not isinstance(value, (int, float)):
            raise TypeError(
                f"Observation {index} is not numeric: {value!r}"
            )

        numeric_value = float(value)

        if not math.isfinite(numeric_value):
            raise ValueError(
                f"Observation {index} is not finite: {value!r}"
            )

        cleaned.append(numeric_value)

    if not cleaned:
        raise ValueError("Dataset is empty.")

    return cleaned


def edge_cases_demo() -> None:
    print_title("24. Data Validation and Edge Cases")

    print("Constant data:")
    constant_data = [5, 5, 5, 5, 5]

    describe_numeric(constant_data, "Constant Data")

    print("\nImportant edge cases:")
    edge_cases = [
        "Empty dataset",
        "Single observation",
        "Constant values",
        "Missing values",
        "Infinite values",
        "NaN values",
        "Mixed numerical and categorical types",
        "Extreme outliers",
        "Very small samples",
        "Highly imbalanced categories",
    ]

    for item in edge_cases:
        print(f"  - {item}")

    print("\nValidation examples:")

    valid = validate_numeric_data([1, 2, 3.5, 4])
    print("Valid data:", valid)

    invalid_examples = [
        [],
        [1, float("nan"), 3],
        [1, float("inf"), 3],
        [1, "three", 4],
        [True, 2, 3],
    ]

    for invalid_data in invalid_examples:
        try:
            validate_numeric_data(invalid_data)
        except (TypeError, ValueError) as error:
            print(
                f"  Rejected {invalid_data!r}: "
                f"{type(error).__name__}: {error}"
            )


# =============================================================================
# SECTION 25: MISSING VALUES
# =============================================================================

def remove_nan(data: Sequence[float]) -> list[float]:
    """Remove NaN values while retaining finite numerical observations."""
    return [
        value
        for value in data
        if not math.isnan(value)
    ]


def missing_value_demo() -> None:
    print_title("25. Missing Values")

    data = [10.0, 12.0, float("nan"), 14.0, 15.0]

    print("Original data:", data)

    cleaned = remove_nan(data)

    print("After removing NaN:", cleaned)
    print(f"Mean of available values: {mean(cleaned):.2f}")

    print(
        "\nMissing data should not automatically be treated as zero. "
        "The appropriate treatment depends on why values are missing."
    )


# =============================================================================
# SECTION 26: CATEGORICAL IMBALANCE
# =============================================================================

def categorical_imbalance_demo() -> None:
    print_title("26. Categorical Imbalance")

    labels = (
        ["Normal"] * 950
        + ["Fraud"] * 50
    )

    probabilities = categorical_distribution(labels)

    print_categorical_distribution(labels)

    majority_accuracy = probabilities["Normal"]

    print(
        f"\nAlways predicting the majority class would achieve "
        f"{majority_accuracy:.2%} accuracy."
    )

    print(
        "This illustrates why a highly imbalanced categorical distribution "
        "can make raw accuracy misleading."
    )

    print(
        "Other evaluation measures may include precision, recall, F1 score, "
        "specificity, balanced accuracy, or class-specific error rates."
    )


# =============================================================================
# SECTION 27: SAMPLING AND BIAS
# =============================================================================

def sampling_bias_demo() -> None:
    print_title("27. Sampling and Distribution Bias")

    population = [
        "Urban",
        "Urban",
        "Urban",
        "Urban",
        "Rural",
        "Rural",
        "Rural",
        "Rural",
        "Rural",
        "Rural",
    ]

    biased_sample = [
        "Urban",
        "Urban",
        "Urban",
        "Urban",
        "Urban",
    ]

    population_distribution = categorical_distribution(population)
    sample_distribution = categorical_distribution(biased_sample)

    print("Population distribution:")
    for category, probability in population_distribution.items():
        print(f"  {category}: {probability:.2%}")

    print("\nBiased sample distribution:")
    for category, probability in sample_distribution.items():
        print(f"  {category}: {probability:.2%}")

    print(
        "\nA distribution calculated from a sample can differ from the "
        "population distribution because of sampling variability or bias."
    )


# =============================================================================
# SECTION 28: BIN WIDTH AND HISTOGRAM INTERPRETATION
# =============================================================================

def histogram_bin_demo() -> None:
    print_title("28. Histogram Bin Width")

    data = generate_normal_sample(
        size=1000,
        mu=0,
        sigma=1,
        seed=99,
    )

    for number_of_bins in [5, 10, 20]:
        print_subtitle(
            f"Histogram with {number_of_bins} bins"
        )

        print_histogram(
            data,
            number_of_bins=number_of_bins,
            width=40,
        )

    print(
        "\nToo few bins can hide meaningful structure. "
        "Too many bins can make random variation look like structure."
    )

    print(
        "Bin choice affects visual interpretation but does not change "
        "the underlying observations."
    )


# =============================================================================
# SECTION 29: COMPARING MEAN AND MEDIAN
# =============================================================================

def center_comparison_demo() -> None:
    print_title("29. Mean, Median, and Mode")

    datasets = {
        "Symmetric": [1, 2, 3, 4, 5, 6, 7],
        "Right-skewed": [1, 2, 2, 3, 3, 3, 4, 20],
        "Left-skewed": [0, 16, 17, 17, 18, 18, 19, 19],
    }

    for name, data in datasets.items():
        print_subtitle(name)

        print(f"Data:   {data}")
        print(f"Mean:   {mean(data):.3f}")
        print(f"Median: {median(data):.3f}")
        print(f"Mode:   {multimode(data)}")

    print(
        "\nThe mean uses every numerical observation and is sensitive "
        "to extreme values. The median depends on order and is more "
        "robust to outliers."
    )

    print(
        "The mode identifies the most frequently observed value or values."
    )


# =============================================================================
# SECTION 30: COEFFICIENT OF VARIATION
# =============================================================================

def coefficient_of_variation(
    data: Sequence[float],
) -> float:
    """
    Calculate CV = standard deviation / absolute mean.

    CV is most interpretable when the variable has a meaningful zero
    and a positive mean.
    """
    average = mean(data)

    if average == 0:
        raise ValueError(
            "Coefficient of variation is undefined when mean is zero."
        )

    return stdev(data) / abs(average)


def coefficient_of_variation_demo() -> None:
    print_title("30. Coefficient of Variation")

    datasets = {
        "Process A": [90, 95, 100, 105, 110],
        "Process B": [180, 190, 200, 210, 220],
    }

    for name, data in datasets.items():
        cv = coefficient_of_variation(data)

        print(
            f"{name}: mean={mean(data):.2f}, "
            f"SD={stdev(data):.2f}, "
            f"CV={cv:.2%}"
        )

    print(
        "\nCV expresses standard deviation relative to the magnitude of "
        "the mean. It is useful for comparing relative variability across "
        "variables on compatible ratio scales."
    )


# =============================================================================
# SECTION 31: Z-SCORE STANDARDIZATION
# =============================================================================

def standardize(data: Sequence[float]) -> list[float]:
    """Standardize data using sample mean and sample standard deviation."""
    if len(data) < 2:
        raise ValueError("At least two observations are required.")

    average = mean(data)
    sample_sd = stdev(data)

    if sample_sd == 0:
        raise ValueError("Cannot standardize constant data.")

    return [
        (value - average) / sample_sd
        for value in data
    ]


def standardization_demo() -> None:
    print_title("31. Standardization and Z-Scores")

    scores = [72, 81, 88, 90, 95, 100]

    standardized = standardize(scores)

    print("Original scores:")
    print(scores)

    print("\nStandardized scores:")
    for original, z in zip(scores, standardized):
        print(f"  {original:>3} -> z={z:+.4f}")

    print(
        "\nStandardization changes the location and scale but preserves "
        "the ordering of observations."
    )


# =============================================================================
# SECTION 32: MONTE CARLO APPROXIMATION
# =============================================================================

def monte_carlo_normal_probability(
    lower: float,
    upper: float,
    mu: float,
    sigma: float,
    trials: int = 100_000,
    seed: int = 42,
) -> float:
    """Approximate a normal probability using random simulation."""
    if trials <= 0:
        raise ValueError("Trials must be positive.")

    generator = random.Random(seed)

    successes = 0

    for _ in range(trials):
        value = generator.gauss(mu, sigma)

        if lower <= value <= upper:
            successes += 1

    return successes / trials


def monte_carlo_demo() -> None:
    print_title("32. Simulation and Monte Carlo Approximation")

    analytical = (
        normal_cdf(120, 100, 15)
        - normal_cdf(80, 100, 15)
    )

    simulated = monte_carlo_normal_probability(
        lower=80,
        upper=120,
        mu=100,
        sigma=15,
        trials=100_000,
        seed=42,
    )

    print(f"Analytical probability: {analytical:.5%}")
    print(f"Monte Carlo estimate:   {simulated:.5%}")
    print(f"Absolute difference:    {abs(analytical - simulated):.5%}")

    print(
        "\nSimulation approximates probabilities by repeated random sampling. "
        "Its accuracy depends on the number of trials and the quality of "
        "the random-number generation."
    )


# =============================================================================
# SECTION 33: COMPARING DISTRIBUTIONS
# =============================================================================

@dataclass
class DistributionProfile:
    """Compact numerical profile of a dataset."""

    name: str
    count: int
    mean: float
    median: float
    standard_deviation: float
    skewness: float
    q1: float
    q3: float

    @property
    def iqr(self) -> float:
        """Interquartile range."""
        return self.q3 - self.q1


def create_distribution_profile(
    name: str,
    data: Sequence[float],
) -> DistributionProfile:
    """Build a distribution profile."""
    if len(data) < 3:
        raise ValueError("At least three observations are required.")

    q1, middle, q3 = quartiles(data)

    return DistributionProfile(
        name=name,
        count=len(data),
        mean=mean(data),
        median=middle,
        standard_deviation=stdev(data),
        skewness=sample_skewness(data),
        q1=q1,
        q3=q3,
    )


def distribution_comparison_demo() -> None:
    print_title("33. Distribution Comparison")

    distributions = {
        "Normal": generate_normal_sample(
            1000,
            50,
            10,
            seed=1,
        ),
        "Right skew": generate_right_skewed_data(
            1000,
            seed=1,
        ),
        "Left skew": generate_left_skewed_data(
            1000,
            seed=1,
        ),
    }

    profiles = [
        create_distribution_profile(name, data)
        for name, data in distributions.items()
    ]

    print(
        f"{'Distribution':<15}"
        f"{'Mean':>10}"
        f"{'Median':>10}"
        f"{'SD':>10}"
        f"{'Skew':>10}"
        f"{'IQR':>10}"
    )

    for profile in profiles:
        print(
            f"{profile.name:<15}"
            f"{profile.mean:>10.2f}"
            f"{profile.median:>10.2f}"
            f"{profile.standard_deviation:>10.2f}"
            f"{profile.skewness:>10.2f}"
            f"{profile.iqr:>10.2f}"
        )


# =============================================================================
# SECTION 34: REAL-WORLD APPLICATIONS
# =============================================================================

def real_world_applications_demo() -> None:
    print_title("34. Real-World Applications")

    applications = {
        "Finance": [
            "Returns may be approximately symmetric over some periods but can exhibit heavy tails.",
            "Transaction amounts are often right-skewed.",
            "Loss distributions can be highly asymmetric.",
        ],
        "Business": [
            "Customer spending frequently has a long right tail.",
            "Customer segments form categorical distributions.",
            "Conversion outcomes are often binary.",
        ],
        "Healthcare": [
            "Waiting times can be right-skewed.",
            "Patient categories are categorical variables.",
            "Measurements may require domain-specific reference distributions.",
        ],
        "Machine Learning": [
            "Feature distributions influence preprocessing choices.",
            "Class imbalance is a categorical distribution issue.",
            "Standardization can improve some optimization procedures.",
        ],
        "Quality Control": [
            "Measurements can be monitored for shifts in distribution.",
            "Control limits are related to distributional assumptions.",
            "Outliers may indicate process problems or measurement errors.",
        ],
        "Operations": [
            "Service times are frequently skewed.",
            "Demand is often represented as a probability distribution.",
            "Queueing models rely on assumptions about arrival and service distributions.",
        ],
    }

    for domain, examples in applications.items():
        print_subtitle(domain)

        for example in examples:
            print(f"  • {example}")


# =============================================================================
# SECTION 35: IMPORTANT COMPARISONS
# =============================================================================

def comparison_table_demo() -> None:
    print_title("35. Important Distribution Comparisons")

    rows = [
        (
            "Normal",
            "Continuous",
            "Symmetric",
            "Mean",
            "Mean = median = mode in the ideal case",
        ),
        (
            "Right-skewed",
            "Usually continuous",
            "Long right tail",
            "Often above median",
            "Mean can be strongly affected by high values",
        ),
        (
            "Left-skewed",
            "Usually continuous",
            "Long left tail",
            "Often below median",
            "Mean can be strongly affected by low values",
        ),
        (
            "Categorical",
            "Discrete categories",
            "Not described by numerical shape",
            "Mode",
            "Use counts and proportions",
        ),
    ]

    headers = (
        "Type",
        "Data",
        "Shape",
        "Useful center",
        "Important property",
    )

    widths = [18, 22, 24, 18, 45]

    print(
        "".join(
            f"{header:<{width}}"
            for header, width in zip(headers, widths)
        )
    )

    for row in rows:
        print(
            "".join(
                f"{str(value):<{width}}"
                for value, width in zip(row, widths)
            )
        )


# =============================================================================
# SECTION 36: COMMON MISTAKES
# =============================================================================

def common_mistakes_demo() -> None:
    print_title("36. Common Mistakes")

    mistakes = [
        (
            "Treating a histogram as proof of normality",
            "A histogram is a visual diagnostic, not definitive proof."
        ),
        (
            "Confusing PDF with probability",
            "For a continuous variable, probability is an area under the density."
        ),
        (
            "Assuming mean equals median",
            "They coincide under some symmetric distributions, not universally."
        ),
        (
            "Ignoring skewness",
            "Strong skew can make mean and standard deviation poor summaries."
        ),
        (
            "Using standard deviation with severe outliers without inspection",
            "Robust measures such as median and IQR may be more informative."
        ),
        (
            "Encoding nominal categories as meaningful numbers",
            "Category codes do not automatically create numerical meaning."
        ),
        (
            "Assuming a large sample makes every distribution normal",
            "The Central Limit Theorem concerns certain sampling distributions, especially sample means."
        ),
        (
            "Using the wrong histogram bin width",
            "Poor binning can hide or exaggerate apparent patterns."
        ),
        (
            "Removing outliers automatically",
            "An extreme observation may be valid and scientifically important."
        ),
        (
            "Ignoring sampling bias",
            "A very large biased sample can still estimate the wrong population distribution."
        ),
    ]

    for mistake, correction in mistakes:
        print(f"\nMistake: {mistake}")
        print(f"Correction: {correction}")


# =============================================================================
# SECTION 37: PERFORMANCE CONSIDERATIONS
# =============================================================================

def performance_demo() -> None:
    print_title("37. Computational Considerations")

    print("Typical computational characteristics:")

    characteristics = [
        ("Frequency counting", "O(n) average with a hash table"),
        ("Sorting", "O(n log n)"),
        ("Mean", "O(n)"),
        ("Variance", "O(n)"),
        ("Naive percentile after sorting", "O(n log n)"),
        ("ECDF query after no preprocessing", "O(n) per query"),
        ("ECDF after sorting with binary search", "O(log n) per query"),
        ("Naive KDE at one point", "O(n)"),
        ("Naive KDE at m points", "O(n*m)"),
        ("Monte Carlo simulation", "O(number of trials)"),
    ]

    for operation, complexity in characteristics:
        print(f"  {operation:<42} {complexity}")

    print(
        "\nFor large datasets, production implementations often use "
        "optimized numerical libraries, vectorization, efficient sorting, "
        "streaming algorithms, approximate quantiles, or specialized "
        "density-estimation methods."
    )


# =============================================================================
# SECTION 38: SECURITY AND DATA-INTEGRITY CONSIDERATIONS
# =============================================================================

def data_integrity_demo() -> None:
    print_title("38. Data Integrity and Security Considerations")

    considerations = [
        "Validate data types before statistical calculations.",
        "Reject non-finite numerical values when the analysis requires finite data.",
        "Preserve raw observations so transformations can be audited.",
        "Record assumptions about missing values and outlier handling.",
        "Do not silently coerce categorical values into numerical quantities.",
        "Protect sensitive datasets with appropriate access controls.",
        "Avoid exposing individual records when aggregated distributions are sufficient.",
        "Check that category labels have not been corrupted during ingestion.",
        "Use deterministic seeds when reproducibility is required.",
        "Document transformations such as logarithms, scaling, winsorization, and filtering.",
    ]

    for consideration in considerations:
        print(f"  • {consideration}")


# =============================================================================
# SECTION 39: REPRODUCIBILITY
# =============================================================================

def reproducibility_demo() -> None:
    print_title("39. Reproducibility")

    first = generate_normal_sample(
        size=10,
        mu=0,
        sigma=1,
        seed=123,
    )

    second = generate_normal_sample(
        size=10,
        mu=0,
        sigma=1,
        seed=123,
    )

    third = generate_normal_sample(
        size=10,
        mu=0,
        sigma=1,
        seed=456,
    )

    print("Sample generated with seed 123:")
    print([round(value, 4) for value in first])

    print("\nSame seed again:")
    print([round(value, 4) for value in second])

    print("\nDifferent seed:")
    print([round(value, 4) for value in third])

    print(
        f"\nSame seed produces same sequence: {first == second}"
    )

    print(
        "A fixed seed is useful for demonstrations, debugging, testing, "
        "and reproducible simulations. It is not appropriate when "
        "cryptographic randomness is required."
    )


# =============================================================================
# SECTION 40: INTEGRATED MINI CASE STUDY
# =============================================================================

def integrated_case_study() -> None:
    print_title("40. Integrated Case Study: Customer Order Values")

    generator = random.Random(2026)

    # A simple synthetic business dataset:
    # most customers make relatively small purchases while a smaller number
    # make very large purchases. This creates a right-skewed distribution.
    orders = [
        generator.expovariate(1 / 75)
        for _ in range(1000)
    ]

    print("Business question:")
    print(
        "How should customer order values be described and interpreted?"
    )

    describe_numeric(orders, "Customer Order Values")

    print("\nHistogram:")
    print_histogram(
        orders,
        number_of_bins=15,
        width=50,
    )

    print("\nShape interpretation:")
    print(distribution_shape_interpretation(orders))

    print("\nMean versus median:")
    print(f"  Mean:   {mean(orders):.2f}")
    print(f"  Median: {median(orders):.2f}")

    print("\nIQR-based outliers:")
    outliers = iqr_outliers(orders)

    print(f"  Number of outliers: {len(outliers)}")

    print("\nLog transformation:")
    log_orders = safe_log_transform(orders)

    print(
        f"  Original skewness: "
        f"{sample_skewness(orders):.3f}"
    )

    print(
        f"  Log-transformed skewness: "
        f"{sample_skewness(log_orders):.3f}"
    )

    print(
        "\nInterpretation:"
    )
    print(
        "The median may better represent a typical customer order when "
        "the distribution is strongly right-skewed. The mean remains useful "
        "for aggregate financial calculations because total revenue depends "
        "on the arithmetic sum."
    )

    print(
        "\nThis illustrates why the correct summary depends on the business "
        "question rather than on a single universally best statistic."
    )


# =============================================================================
# SECTION 41: TESTS
# =============================================================================

def approximately_equal(
    actual: float,
    expected: float,
    tolerance: float = 1e-9,
) -> bool:
    """Check approximate equality for floating-point results."""
    return math.isclose(
        actual,
        expected,
        rel_tol=tolerance,
        abs_tol=tolerance,
    )


def run_tests() -> None:
    """Run lightweight built-in tests without external testing packages."""
    print_title("41. Built-In Tests")

    # PMF tests.
    assert approximately_equal(bernoulli_pmf(1, 0.7), 0.7)
    assert approximately_equal(bernoulli_pmf(0, 0.7), 0.3)

    # Binomial distribution should sum to one.
    total_binomial_probability = sum(
        binomial_pmf(k, 10, 0.4)
        for k in range(11)
    )

    assert approximately_equal(
        total_binomial_probability,
        1.0,
        tolerance=1e-10,
    )

    # Normal distribution should have CDF approaching 0 and 1.
    assert normal_cdf(-100) < 1e-12
    assert normal_cdf(100) > 1 - 1e-12

    # Z-score.
    assert approximately_equal(
        z_score(110, 100, 10),
        1.0,
    )

    # Percentile.
    sample = [1, 2, 3, 4, 5]
    assert approximately_equal(
        percentile(sample, 50),
        3.0,
    )

    # IQR.
    assert approximately_equal(
        interquartile_range(sample),
        2.0,
    )

    # Categorical probabilities.
    categories = ["A", "A", "B", "C"]
    probabilities = categorical_distribution(categories)

    assert approximately_equal(
        sum(probabilities.values()),
        1.0,
    )

    # Discrete expectation.
    expected = discrete_expectation(
        [0, 1, 2],
        [0.2, 0.3, 0.5],
    )

    assert approximately_equal(expected, 1.3)

    # Reproducibility.
    sample_one = generate_normal_sample(
        20,
        0,
        1,
        seed=123,
    )

    sample_two = generate_normal_sample(
        20,
        0,
        1,
        seed=123,
    )

    assert sample_one == sample_two

    # Validation.
    try:
        validate_numeric_data([])
    except ValueError:
        pass
    else:
        raise AssertionError("Empty data should be rejected.")

    print("All tests passed.")


# =============================================================================
# SECTION 42: STUDY CHECKLIST
# =============================================================================

def study_checklist() -> None:
    print_title("42. Concept Checklist")

    checklist = [
        "Understand what a distribution represents.",
        "Distinguish population distributions from sample distributions.",
        "Distinguish numerical and categorical variables.",
        "Construct frequency and relative-frequency tables.",
        "Understand histogram bins.",
        "Interpret mean, median, mode, variance, and standard deviation.",
        "Interpret quantiles, percentiles, and IQR.",
        "Understand normal PDFs and CDFs.",
        "Convert observations to z-scores.",
        "Use the empirical rule appropriately.",
        "Recognize right and left skew.",
        "Understand why mean and median respond differently to skew.",
        "Use robust summaries for distributions with extreme values.",
        "Represent categorical variables using counts and probabilities.",
        "Understand Bernoulli, binomial, and multinomial distributions.",
        "Distinguish PMF, PDF, and CDF.",
        "Understand joint and conditional distributions.",
        "Understand the ECDF.",
        "Understand the Law of Large Numbers.",
        "Understand the Central Limit Theorem.",
        "Distinguish population distribution from sampling distribution.",
        "Understand standard error.",
        "Understand the purpose and limitations of KDE.",
        "Recognize the effect of histogram bin width.",
        "Identify common distribution-analysis mistakes.",
        "Consider data quality, missingness, outliers, and sampling bias.",
        "Document transformations and assumptions.",
        "Use reproducible random seeds for simulation and testing.",
    ]

    for item in checklist:
        print(f"  [ ] {item}")


# =============================================================================
# SECTION 43: MAIN PROGRAM
# =============================================================================

def main() -> None:
    """
    Execute the complete educational walkthrough.

    The functions are kept separate so that individual demonstrations can
    also be imported and reused from another Python program.
    """
    explain_distribution()
    explain_population_and_sample()

    describe_numeric(
        [12, 15, 15, 16, 18, 20, 21, 22, 25],
        "Small Numerical Dataset",
    )

    print_frequency_table(
        ["A", "B", "A", "C", "B", "A", "D", "A"]
    )

    print_histogram(
        [1, 2, 2, 3, 3, 3, 4, 4, 5, 7, 8, 10],
        number_of_bins=6,
        width=40,
    )

    normal_distribution_demo()
    normal_probability_examples()
    normal_sampling_demo()

    skewness_demo()
    transformation_demo()

    categorical_demo()
    categorical_probability_demo()
    categorical_joint_demo()

    outlier_demo()
    empirical_cdf_demo()

    law_of_large_numbers_demo()
    central_limit_theorem_demo()
    standard_error_demo()

    kde_demo()
    percentile_demo()
    distribution_shape_demo()
    normality_distinction_demo()

    discrete_vs_continuous_demo()
    pmf_visualization_demo()
    expectation_demo()

    edge_cases_demo()
    missing_value_demo()
    categorical_imbalance_demo()
    sampling_bias_demo()

    histogram_bin_demo()
    center_comparison_demo()
    coefficient_of_variation_demo()
    standardization_demo()
    monte_carlo_demo()

    distribution_comparison_demo()
    real_world_applications_demo()
    comparison_table_demo()
    common_mistakes_demo()

    performance_demo()
    data_integrity_demo()
    reproducibility_demo()

    integrated_case_study()

    run_tests()
    study_checklist()

    print_title("End of Distribution Study Script")
    print(
        "The script has demonstrated theoretical distributions, empirical "
        "distributions, categorical distributions, distribution shape, "
        "sampling behavior, probability calculations, transformations, "
        "simulation, validation, and practical interpretation."
    )


if __name__ == "__main__":
    main()
