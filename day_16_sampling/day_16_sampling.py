"""
Sampling: Population, Samples and Sampling Techniques
======================================================

A self-contained study and demonstration program covering:
- Population and sample
- Sampling frames and sampling units
- Parameters and statistics
- Sampling error and nonsampling error
- Probability and non-probability sampling
- Simple random sampling
- Systematic sampling
- Stratified sampling
- Cluster sampling
- Multistage sampling
- Convenience, quota, purposive and snowball sampling
- Sample-size estimation
- Sampling distributions
- Bias and representativeness
- Weighting
- Confidence intervals
- Design effects
- Reproducibility
- Edge cases and validation
- A practical survey simulation

The program uses only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, sqrt
from random import Random
from statistics import mean, median, stdev
from typing import Callable, Iterable, Sequence


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL TERMINOLOGY
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Person:
    """One sampling unit in a synthetic finite population."""
    person_id: int
    age: int
    region: str
    employment: str
    monthly_income: float
    satisfaction: float
    cluster: str


Population = list[Person]


def population_parameter(values: Sequence[float]) -> dict[str, float]:
    """
    Calculate population quantities.

    A parameter describes the complete population. It is not an estimate
    obtained from a sample.
    """
    if not values:
        raise ValueError("Population values cannot be empty.")

    population_mean = sum(values) / len(values)
    variance = sum((x - population_mean) ** 2 for x in values) / len(values)

    return {
        "N": float(len(values)),
        "mean": population_mean,
        "variance": variance,
        "standard_deviation": sqrt(variance),
        "minimum": min(values),
        "maximum": max(values),
    }


def sample_statistics(values: Sequence[float]) -> dict[str, float]:
    """
    Calculate statistics from a sample.

    A statistic is calculated from observed sample data and can be used
    to estimate an unknown population parameter.
    """
    if not values:
        raise ValueError("Sample cannot be empty.")

    sample_mean = mean(values)

    return {
        "n": float(len(values)),
        "mean": sample_mean,
        "median": median(values),
        "sample_standard_deviation": stdev(values) if len(values) > 1 else 0.0,
        "minimum": min(values),
        "maximum": max(values),
    }


# ---------------------------------------------------------------------------
# 2. POPULATION GENERATION
# ---------------------------------------------------------------------------

def build_population(size: int = 5000, seed: int = 42) -> Population:
    """Create a reproducible synthetic population."""
    if size <= 0:
        raise ValueError("Population size must be positive.")

    rng = Random(seed)

    regions = ["North", "South", "East", "West"]
    employment_types = ["Student", "Employed", "Self-employed", "Unemployed"]
    clusters = [f"District-{i:02d}" for i in range(1, 21)]

    population = []

    for person_id in range(1, size + 1):
        age = rng.randint(18, 70)
        region = rng.choices(regions, weights=[35, 25, 20, 20], k=1)[0]
        employment = rng.choices(
            employment_types,
            weights=[15, 50, 25, 10],
            k=1,
        )[0]

        base_income = {
            "Student": 12000,
            "Employed": 50000,
            "Self-employed": 60000,
            "Unemployed": 10000,
        }[employment]

        income = max(
            0.0,
            rng.gauss(base_income, max(3000, base_income * 0.25)),
        )

        satisfaction = max(
            1.0,
            min(10.0, rng.gauss(6.0 + (income / 200000), 1.5)),
        )

        cluster = clusters[(person_id - 1) % len(clusters)]

        population.append(
            Person(
                person_id=person_id,
                age=age,
                region=region,
                employment=employment,
                monthly_income=income,
                satisfaction=satisfaction,
                cluster=cluster,
            )
        )

    return population


# ---------------------------------------------------------------------------
# 3. VALIDATION HELPERS
# ---------------------------------------------------------------------------

def validate_sample_size(population_size: int, sample_size: int) -> None:
    """Validate finite-population sample sizes."""
    if population_size <= 0:
        raise ValueError("Population size must be positive.")
    if sample_size <= 0:
        raise ValueError("Sample size must be positive.")
    if sample_size > population_size:
        raise ValueError("Sample size cannot exceed population size.")


def ensure_unique_ids(sample: Sequence[Person]) -> None:
    """Verify that sampling without replacement produced unique units."""
    ids = [person.person_id for person in sample]
    if len(ids) != len(set(ids)):
        raise AssertionError("Duplicate sampling units detected.")


# ---------------------------------------------------------------------------
# 4. SIMPLE RANDOM SAMPLING
# ---------------------------------------------------------------------------

def simple_random_sample(
    population: Population,
    sample_size: int,
    seed: int = 42,
) -> Population:
    """
    Simple random sampling without replacement.

    Every possible sample of size n has the same probability of selection.
    """
    validate_sample_size(len(population), sample_size)

    rng = Random(seed)
    sample = rng.sample(population, sample_size)
    ensure_unique_ids(sample)
    return sample


# ---------------------------------------------------------------------------
# 5. SYSTEMATIC SAMPLING
# ---------------------------------------------------------------------------

def systematic_sample(
    population: Population,
    sample_size: int,
    seed: int = 42,
) -> Population:
    """
    Systematic sampling.

    The sampling interval is approximately N/n. A random starting point
    is selected, followed by every k-th population unit.

    A poorly ordered sampling frame can create periodicity problems.
    """
    validate_sample_size(len(population), sample_size)

    n = len(population)
    interval = n / sample_size
    rng = Random(seed)

    start = rng.uniform(0, interval)
    indices = [
        min(n - 1, int(start + i * interval))
        for i in range(sample_size)
    ]

    sample = [population[index] for index in indices]
    ensure_unique_ids(sample)
    return sample


# ---------------------------------------------------------------------------
# 6. STRATIFIED SAMPLING
# ---------------------------------------------------------------------------

def stratified_sample(
    population: Population,
    sample_size: int,
    stratum_function: Callable[[Person], str],
    seed: int = 42,
) -> Population:
    """
    Proportionate stratified random sampling.

    The population is divided into mutually meaningful strata, and units
    are randomly selected from each stratum in proportion to its size.

    Stratification can improve precision when strata are internally
    homogeneous and meaningfully different from one another.
    """
    validate_sample_size(len(population), sample_size)

    rng = Random(seed)

    strata: dict[str, list[Person]] = {}
    for person in population:
        strata.setdefault(stratum_function(person), []).append(person)

    counts = {
        key: int(round(len(units) / len(population) * sample_size))
        for key, units in strata.items()
    }

    # Correct rounding so the final allocation is exactly sample_size.
    difference = sample_size - sum(counts.values())

    ordered_keys = sorted(
        strata,
        key=lambda key: len(strata[key]),
        reverse=True,
    )

    index = 0
    while difference != 0:
        key = ordered_keys[index % len(ordered_keys)]

        if difference > 0:
            if counts[key] < len(strata[key]):
                counts[key] += 1
                difference -= 1
        else:
            if counts[key] > 0:
                counts[key] -= 1
                difference += 1

        index += 1

    result = []

    for key, units in strata.items():
        count = counts[key]
        result.extend(rng.sample(units, count))

    rng.shuffle(result)
    ensure_unique_ids(result)
    return result


# ---------------------------------------------------------------------------
# 7. CLUSTER SAMPLING
# ---------------------------------------------------------------------------

def cluster_sample(
    population: Population,
    number_of_clusters: int,
    seed: int = 42,
) -> Population:
    """
    One-stage cluster sampling.

    Entire naturally occurring groups are sampled rather than individual
    units. This can reduce fieldwork cost but often increases sampling
    variance when people within a cluster resemble each other.
    """
    if number_of_clusters <= 0:
        raise ValueError("Number of clusters must be positive.")

    rng = Random(seed)

    clusters: dict[str, list[Person]] = {}
    for person in population:
        clusters.setdefault(person.cluster, []).append(person)

    if number_of_clusters > len(clusters):
        raise ValueError("Too many clusters requested.")

    selected_names = rng.sample(list(clusters), number_of_clusters)

    result = []
    for name in selected_names:
        result.extend(clusters[name])

    return result


# ---------------------------------------------------------------------------
# 8. MULTISTAGE SAMPLING
# ---------------------------------------------------------------------------

def multistage_sample(
    population: Population,
    cluster_count: int,
    units_per_cluster: int,
    seed: int = 42,
) -> Population:
    """
    Two-stage sampling.

    Stage 1: select clusters.
    Stage 2: randomly select people inside each selected cluster.
    """
    if cluster_count <= 0 or units_per_cluster <= 0:
        raise ValueError("Stage sizes must be positive.")

    rng = Random(seed)

    clusters: dict[str, list[Person]] = {}
    for person in population:
        clusters.setdefault(person.cluster, []).append(person)

    if cluster_count > len(clusters):
        raise ValueError("Too many clusters requested.")

    selected_clusters = rng.sample(list(clusters), cluster_count)
    result = []

    for cluster_name in selected_clusters:
        units = clusters[cluster_name]
        count = min(units_per_cluster, len(units))
        result.extend(rng.sample(units, count))

    ensure_unique_ids(result)
    return result


# ---------------------------------------------------------------------------
# 9. NON-PROBABILITY SAMPLING
# ---------------------------------------------------------------------------

def convenience_sample(
    population: Population,
    sample_size: int,
) -> Population:
    """
    Convenience sampling selects easily accessible units.

    It is operationally simple but generally does not provide the same
    probability-based inference framework as a probability sample.
    """
    validate_sample_size(len(population), sample_size)
    return list(population[:sample_size])


def quota_sample(
    population: Population,
    sample_size: int,
    attribute: Callable[[Person], str],
    quotas: dict[str, int],
) -> Population:
    """
    Simple quota sampling.

    Quotas specify target counts, but selection inside a quota can be
    non-random. Therefore quota sampling is not automatically equivalent
    to stratified random sampling.
    """
    if sum(quotas.values()) != sample_size:
        raise ValueError("Quota totals must equal sample size.")

    result = []
    used: set[int] = set()

    for category, quota in quotas.items():
        candidates = [
            person
            for person in population
            if attribute(person) == category
            and person.person_id not in used
        ]

        if len(candidates) < quota:
            raise ValueError(f"Insufficient units for quota: {category}")

        selected = candidates[:quota]
        result.extend(selected)
        used.update(person.person_id for person in selected)

    return result


# ---------------------------------------------------------------------------
# 10. ESTIMATORS AND SAMPLING ERROR
# ---------------------------------------------------------------------------

def mean_estimate(sample: Sequence[Person]) -> float:
    """Estimate the population mean using the sample mean."""
    if not sample:
        raise ValueError("Sample cannot be empty.")
    return mean(person.monthly_income for person in sample)


def sampling_error(
    population_mean: float,
    estimated_mean: float,
) -> float:
    """Signed difference between estimate and population parameter."""
    return estimated_mean - population_mean


def absolute_sampling_error(
    population_mean: float,
    estimated_mean: float,
) -> float:
    return abs(sampling_error(population_mean, estimated_mean))


# ---------------------------------------------------------------------------
# 11. SAMPLE-SIZE CALCULATION
# ---------------------------------------------------------------------------

def cochran_sample_size(
    confidence_z: float,
    proportion: float,
    margin_of_error: float,
    population_size: int | None = None,
) -> int:
    """
    Cochran-style sample-size calculation for a population proportion.

    n0 = z² p(1-p) / e²

    For a finite population, apply:
    n = n0 / (1 + (n0 - 1)/N)

    p=0.5 is conservative because it maximizes p(1-p).
    """
    if confidence_z <= 0:
        raise ValueError("Z value must be positive.")
    if not 0 < proportion < 1:
        raise ValueError("Proportion must be between 0 and 1.")
    if not 0 < margin_of_error < 1:
        raise ValueError("Margin of error must be between 0 and 1.")

    n0 = (
        confidence_z**2
        * proportion
        * (1 - proportion)
        / margin_of_error**2
    )

    if population_size is None:
        return ceil(n0)

    if population_size <= 0:
        raise ValueError("Population size must be positive.")

    corrected = n0 / (1 + (n0 - 1) / population_size)
    return min(population_size, ceil(corrected))


# ---------------------------------------------------------------------------
# 12. STANDARD ERROR AND CONFIDENCE INTERVAL
# ---------------------------------------------------------------------------

def mean_confidence_interval(
    sample: Sequence[float],
    z_value: float = 1.96,
) -> tuple[float, float, float]:
    """
    Approximate normal-theory confidence interval for a mean.

    This example uses a z critical value for teaching purposes.
    For small samples, a t critical value is generally more appropriate.
    """
    if len(sample) < 2:
        raise ValueError("At least two observations are required.")

    sample_mean = mean(sample)
    standard_error = stdev(sample) / sqrt(len(sample))
    margin = z_value * standard_error

    return (
        sample_mean,
        standard_error,
        margin,
    )


# ---------------------------------------------------------------------------
# 13. WEIGHTED ESTIMATION
# ---------------------------------------------------------------------------

def weighted_mean(
    observations: Iterable[tuple[float, float]],
) -> float:
    """
    Weighted mean.

    Each pair contains (value, weight). Weights can represent unequal
    selection probabilities, nonresponse adjustments, or post-stratification.
    """
    pairs = list(observations)

    if not pairs:
        raise ValueError("At least one observation is required.")

    total_weight = sum(weight for _, weight in pairs)

    if total_weight <= 0:
        raise ValueError("Total weight must be positive.")

    return sum(value * weight for value, weight in pairs) / total_weight


# ---------------------------------------------------------------------------
# 14. REPEATED-SAMPLING SIMULATION
# ---------------------------------------------------------------------------

def simulation_of_sampling_distribution(
    population: Population,
    sample_size: int,
    repetitions: int = 500,
) -> dict[str, float]:
    """
    Repeatedly sample from the same population.

    The distribution of sample means illustrates the sampling distribution.
    """
    if repetitions <= 0:
        raise ValueError("Repetitions must be positive.")

    true_mean = mean(person.monthly_income for person in population)
    estimates = []

    for repetition in range(repetitions):
        sample = simple_random_sample(
            population,
            sample_size,
            seed=1000 + repetition,
        )
        estimates.append(mean_estimate(sample))

    return {
        "true_population_mean": true_mean,
        "mean_of_sample_means": mean(estimates),
        "standard_deviation_of_sample_means": stdev(estimates),
        "minimum_sample_mean": min(estimates),
        "maximum_sample_mean": max(estimates),
    }


# ---------------------------------------------------------------------------
# 15. BIAS DEMONSTRATION
# ---------------------------------------------------------------------------

def compare_sampling_bias(
    population: Population,
    sample_size: int,
) -> dict[str, float]:
    """
    Compare random sampling with a convenience sample.

    The purpose is not to claim that every convenience sample is biased,
    but to demonstrate how the sampling mechanism can create systematic
    differences between a sample and its population.
    """
    true_mean = mean(person.monthly_income for person in population)

    random_sample = simple_random_sample(
        population,
        sample_size,
        seed=7,
    )

    convenient = convenience_sample(
        sorted(
            population,
            key=lambda person: person.monthly_income,
            reverse=True,
        ),
        sample_size,
    )

    random_mean = mean_estimate(random_sample)
    convenience_mean = mean_estimate(convenient)

    return {
        "population_mean": true_mean,
        "random_sample_mean": random_mean,
        "convenience_sample_mean": convenience_mean,
        "random_absolute_error": absolute_sampling_error(
            true_mean,
            random_mean,
        ),
        "convenience_absolute_error": absolute_sampling_error(
            true_mean,
            convenience_mean,
        ),
    }


# ---------------------------------------------------------------------------
# 16. PRACTICAL SURVEY PIPELINE
# ---------------------------------------------------------------------------

def run_survey_pipeline(population: Population) -> None:
    """Run a complete educational sampling workflow."""
    income_values = [person.monthly_income for person in population]
    population_stats = population_parameter(income_values)

    print("\nPOPULATION")
    print(f"Size: {int(population_stats['N'])}")
    print(f"Mean monthly income: {population_stats['mean']:.2f}")
    print(f"Population SD: {population_stats['standard_deviation']:.2f}")

    sample_size = 250

    print("\nSIMPLE RANDOM SAMPLING")
    random_sample = simple_random_sample(population, sample_size)
    random_stats = sample_statistics(
        [person.monthly_income for person in random_sample]
    )
    print(f"Sample size: {int(random_stats['n'])}")
    print(f"Estimated mean: {random_stats['mean']:.2f}")
    print(
        "Sampling error: "
        f"{sampling_error(population_stats['mean'], random_stats['mean']):.2f}"
    )

    print("\nSYSTEMATIC SAMPLING")
    systematic = systematic_sample(population, sample_size)
    systematic_mean = mean_estimate(systematic)
    print(f"Estimated mean: {systematic_mean:.2f}")

    print("\nSTRATIFIED SAMPLING BY REGION")
    stratified = stratified_sample(
        population,
        sample_size,
        lambda person: person.region,
        seed=21,
    )
    stratified_mean = mean_estimate(stratified)
    print(f"Estimated mean: {stratified_mean:.2f}")

    print("\nCLUSTER SAMPLING")
    clusters = cluster_sample(
        population,
        number_of_clusters=3,
        seed=9,
    )
    print(f"Selected clusters contain {len(clusters)} people.")
    print(f"Estimated mean: {mean_estimate(clusters):.2f}")

    print("\nMULTISTAGE SAMPLING")
    multistage = multistage_sample(
        population,
        cluster_count=5,
        units_per_cluster=20,
        seed=15,
    )
    print(f"Final sample size: {len(multistage)}")
    print(f"Estimated mean: {mean_estimate(multistage):.2f}")

    print("\nCONFIDENCE INTERVAL")
    confidence_data = mean_confidence_interval(
        [person.monthly_income for person in random_sample]
    )
    estimated_mean, standard_error, margin = confidence_data
    print(f"Estimate: {estimated_mean:.2f}")
    print(f"Standard error: {standard_error:.2f}")
    print(
        f"Approximate 95% interval: "
        f"{estimated_mean - margin:.2f} to "
        f"{estimated_mean + margin:.2f}"
    )

    print("\nSAMPLE SIZE")
    required = cochran_sample_size(
        confidence_z=1.96,
        proportion=0.50,
        margin_of_error=0.05,
        population_size=len(population),
    )
    print(f"Estimated required sample size: {required}")

    print("\nSAMPLING DISTRIBUTION")
    simulation = simulation_of_sampling_distribution(
        population,
        sample_size=100,
        repetitions=200,
    )
    for key, value in simulation.items():
        print(f"{key}: {value:.2f}")

    print("\nBIAS DEMONSTRATION")
    bias_results = compare_sampling_bias(population, 100)
    for key, value in bias_results.items():
        print(f"{key}: {value:.2f}")


# ---------------------------------------------------------------------------
# 17. EDGE CASES AND COMMON MISTAKES
# ---------------------------------------------------------------------------

def demonstrate_edge_cases(population: Population) -> None:
    print("\nEDGE CASES")

    try:
        simple_random_sample(population, 0)
    except ValueError as error:
        print(f"Invalid zero sample: {error}")

    try:
        simple_random_sample(population, len(population) + 1)
    except ValueError as error:
        print(f"Sample larger than population: {error}")

    try:
        cochran_sample_size(1.96, 1.2, 0.05)
    except ValueError as error:
        print(f"Invalid proportion: {error}")

    try:
        weighted_mean([(100, 0), (200, 0)])
    except ValueError as error:
        print(f"Invalid weights: {error}")

    # A census is not sampling: every population unit is observed.
    census = list(population)
    print(f"Census size: {len(census)}")
    print(
        "Census mean equals population mean: "
        f"{mean_estimate(census) == mean_estimate(population)}"
    )


# ---------------------------------------------------------------------------
# 18. TOPIC MAP
# ---------------------------------------------------------------------------

def print_topic_map() -> None:
    concepts = [
        ("Population", "Entire group of units relevant to a study."),
        ("Sample", "Subset of the population actually observed."),
        ("Parameter", "Numerical property of a population."),
        ("Statistic", "Numerical quantity calculated from a sample."),
        ("Sampling frame", "Operational list or structure from which units are selected."),
        ("Sampling unit", "Basic unit eligible for selection."),
        ("Probability sampling", "Selection probabilities are known and non-zero."),
        ("Simple random", "Units are selected randomly without replacement."),
        ("Systematic", "Select a random start and then approximately every k-th unit."),
        ("Stratified", "Divide the population into strata and sample within each."),
        ("Cluster", "Select groups rather than individual units."),
        ("Multistage", "Use sampling stages, such as clusters followed by individuals."),
        ("Convenience", "Select accessible units."),
        ("Quota", "Fill category quotas without requiring random selection."),
        ("Purposive", "Select units according to a research purpose or criterion."),
        ("Snowball", "Participants help recruit additional participants."),
        ("Sampling error", "Random difference between an estimate and the population parameter."),
        ("Nonresponse error", "Bias or loss of information caused by eligible units not responding."),
        ("Coverage error", "Mismatch between the sampling frame and target population."),
        ("Measurement error", "Difference caused by inaccurate measurement or responses."),
        ("Weighting", "Adjust contributions to account for unequal representation."),
    ]

    print("\nCONCEPT MAP")
    for name, definition in concepts:
        print(f"{name:22} {definition}")


# ---------------------------------------------------------------------------
# 19. MAIN PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("SAMPLING: POPULATION, SAMPLES AND SAMPLING TECHNIQUES")
    print("=" * 72)

    print_topic_map()

    population = build_population(size=5000, seed=42)

    run_survey_pipeline(population)
    demonstrate_edge_cases(population)

    print("\nFIRST FIVE POPULATION UNITS")
    for person in population[:5]:
        print(person)

    print("\nSTRATIFIED SAMPLE COMPOSITION")
    stratified = stratified_sample(
        population,
        sample_size=200,
        stratum_function=lambda person: person.region,
        seed=123,
    )

    region_counts: dict[str, int] = {}
    for person in stratified:
        region_counts[person.region] = region_counts.get(person.region, 0) + 1

    for region, count in sorted(region_counts.items()):
        print(f"{region:10}: {count}")

    print("\nWEIGHTED ESTIMATION EXAMPLE")
    observations = [
        (100.0, 1.0),
        (200.0, 2.0),
        (300.0, 1.0),
    ]
    print(f"Weighted mean: {weighted_mean(observations):.2f}")

    print("\nPROGRAM COMPLETE")


if __name__ == "__main__":
    main()
