"""
Sampling Bias: Selection Bias, Survivorship Bias, and Sampling Errors

A self-contained study program covering:
- Population, sample, parameter, statistic
- Probability and non-probability sampling
- Sampling error versus sampling bias
- Selection bias and major mechanisms
- Survivorship bias
- Undercoverage, nonresponse, voluntary response, convenience sampling
- Collider and conditioning effects
- Sampling-frame problems
- Stratified, cluster, systematic, and multistage sampling
- Weighting and post-stratification
- Simulation-based demonstrations
- Bootstrap and repeated-sampling reasoning
- Diagnostic checks
- Practical survey design
- Statistical and engineering considerations

The program uses only the Python standard library.
"""

from __future__ import annotations

import math
import random
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def heading(title: str) -> None:
    """Print a readable section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def subheading(title: str) -> None:
    """Print a smaller section heading."""
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


def mean(values: Sequence[float]) -> float:
    """Return an arithmetic mean, with an explicit empty-sample error."""
    if not values:
        raise ValueError("Cannot calculate a mean from an empty sequence.")
    return sum(values) / len(values)


def proportion(values: Sequence[bool]) -> float:
    """Return the proportion of True observations."""
    if not values:
        raise ValueError("Cannot calculate a proportion from an empty sequence.")
    return sum(values) / len(values)


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def format_number(value: float) -> str:
    return f"{value:,.3f}"


# ---------------------------------------------------------------------------
# Fundamental statistical terminology
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Person:
    """
    A synthetic population member.

    income:
        A continuous outcome of interest.
    experience:
        A latent characteristic that can affect both outcomes and selection.
    success:
        A binary outcome.
    employed:
        Whether the person is currently employed.
    response_probability:
        Probability that this person responds to a survey.
    """
    person_id: int
    income: float
    experience: float
    success: bool
    employed: bool
    response_probability: float


def population_mean(population: Sequence[Person]) -> float:
    return mean([person.income for person in population])


def sample_mean(sample: Sequence[Person]) -> float:
    return mean([person.income for person in sample])


def create_population(
    size: int = 10_000,
    seed: int = 42,
) -> list[Person]:
    """
    Construct a synthetic population.

    The data-generating process is deliberately simple enough to inspect:
    experience is related to income, and employment/success are correlated
    with the underlying characteristics.
    """
    rng = random.Random(seed)
    population: list[Person] = []

    for person_id in range(size):
        experience = max(0.0, rng.gauss(8.0, 4.0))

        # Income is related to experience but retains substantial variation.
        income = max(
            12_000.0,
            28_000.0
            + 4_000.0 * experience
            + rng.gauss(0.0, 18_000.0),
        )

        # A logistic probability creates a realistic binary outcome.
        success_logit = -1.0 + 0.12 * experience + (income - 50_000) / 150_000
        success_probability = 1 / (1 + math.exp(-success_logit))
        success = rng.random() < success_probability

        employment_probability = min(
            0.98,
            max(0.05, 0.45 + 0.045 * experience),
        )
        employed = rng.random() < employment_probability

        # Survey response is allowed to depend on experience and employment.
        # This creates a nonresponse mechanism for later demonstrations.
        response_probability = min(
            0.95,
            max(
                0.05,
                0.25
                + 0.035 * min(experience, 10)
                + (0.12 if employed else -0.04),
            ),
        )

        population.append(
            Person(
                person_id=person_id,
                income=income,
                experience=experience,
                success=success,
                employed=employed,
                response_probability=response_probability,
            )
        )

    return population


# ---------------------------------------------------------------------------
# Simple random sampling
# ---------------------------------------------------------------------------

def simple_random_sample(
    population: Sequence[Person],
    sample_size: int,
    rng: random.Random,
) -> list[Person]:
    """
    Simple random sampling without replacement.

    Every population member has the same first-order inclusion probability
    when the sample size is fixed.
    """
    if sample_size <= 0:
        raise ValueError("sample_size must be positive.")
    if sample_size > len(population):
        raise ValueError("sample_size cannot exceed population size.")
    return rng.sample(list(population), sample_size)


def sampling_error(
    population_parameter: float,
    sample_statistic: float,
) -> float:
    """Sampling error is statistic minus target population parameter."""
    return sample_statistic - population_parameter


# ---------------------------------------------------------------------------
# Sampling distributions
# ---------------------------------------------------------------------------

def repeated_simple_random_sampling(
    population: Sequence[Person],
    sample_size: int,
    repetitions: int,
    seed: int = 123,
) -> list[float]:
    """
    Simulate the sampling distribution of the sample mean.
    """
    rng = random.Random(seed)
    estimates = []

    for _ in range(repetitions):
        sample = simple_random_sample(population, sample_size, rng)
        estimates.append(sample_mean(sample))

    return estimates


def summarize_estimates(
    estimates: Sequence[float],
    target: float,
) -> dict[str, float]:
    errors = [estimate - target for estimate in estimates]

    return {
        "mean_estimate": mean(estimates),
        "standard_deviation": statistics.stdev(estimates)
        if len(estimates) > 1
        else 0.0,
        "mean_error": mean(errors),
        "mean_absolute_error": mean([abs(error) for error in errors]),
        "minimum": min(estimates),
        "maximum": max(estimates),
    }


# ---------------------------------------------------------------------------
# Selection bias
# ---------------------------------------------------------------------------

def convenience_sample(
    population: Sequence[Person],
    sample_size: int,
) -> list[Person]:
    """
    A deliberately biased convenience sample.

    Here, the sampling mechanism chooses people with unusually high
    experience. This is not a probability sample.
    """
    if sample_size <= 0:
        raise ValueError("sample_size must be positive.")

    ordered = sorted(
        population,
        key=lambda person: person.experience,
        reverse=True,
    )
    return ordered[:sample_size]


def volunteer_response_sample(
    population: Sequence[Person],
    sample_size: int,
) -> list[Person]:
    """
    A stylized voluntary-response sample.

    People with extreme experience are made more likely to participate.
    This illustrates self-selection rather than a valid probability design.
    """
    if sample_size <= 0:
        raise ValueError("sample_size must be positive.")

    ordered = sorted(
        population,
        key=lambda person: abs(person.experience - 8.0),
        reverse=True,
    )
    return ordered[:sample_size]


def nonresponse_sample(
    population: Sequence[Person],
    seed: int = 44,
) -> list[Person]:
    """
    Simulate survey nonresponse.

    Each person's response probability is used independently. The resulting
    respondents need not represent the population when response is related
    to variables associated with the outcome.
    """
    rng = random.Random(seed)
    return [
        person
        for person in population
        if rng.random() < person.response_probability
    ]


# ---------------------------------------------------------------------------
# Undercoverage
# ---------------------------------------------------------------------------

def undercoverage_sample(
    population: Sequence[Person],
    sample_size: int,
) -> list[Person]:
    """
    Simulate an incomplete sampling frame.

    People with very low experience are excluded from the frame.
    """
    frame = [
        person
        for person in population
        if person.experience >= 4.0
    ]

    if sample_size > len(frame):
        raise ValueError("Requested sample is larger than the available frame.")

    rng = random.Random(88)
    return rng.sample(frame, sample_size)


# ---------------------------------------------------------------------------
# Survivorship bias
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Company:
    company_id: int
    initial_capital: float
    annual_return: float
    survived: bool
    years_observed: int


def simulate_companies(
    count: int = 10_000,
    years: int = 10,
    seed: int = 71,
) -> list[Company]:
    """
    Generate companies with heterogeneous annual returns.

    A company is classified as surviving if its capital remains above a
    failure threshold throughout the observation period.
    """
    rng = random.Random(seed)
    companies: list[Company] = []

    for company_id in range(count):
        annual_return = rng.gauss(0.10, 0.30)
        capital = 100_000.0
        survived = True
        years_observed = years

        for year in range(years):
            capital *= 1.0 + annual_return

            if capital < 25_000:
                survived = False
                years_observed = year + 1
                break

        companies.append(
            Company(
                company_id=company_id,
                initial_capital=100_000.0,
                annual_return=annual_return,
                survived=survived,
                years_observed=years_observed,
            )
        )

    return companies


# ---------------------------------------------------------------------------
# Conditioning and collider bias
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AdmissionCase:
    case_id: int
    preparation: float
    natural_ability: float
    admitted: bool


def simulate_admissions(
    count: int = 20_000,
    seed: int = 91,
) -> list[AdmissionCase]:
    """
    Simulate an admissions process where preparation and natural ability both
    contribute to admission.

    Conditioning on admission can create a negative association between the
    two causes even if they were independently generated.
    """
    rng = random.Random(seed)
    cases = []

    for case_id in range(count):
        preparation = rng.gauss(0.0, 1.0)
        natural_ability = rng.gauss(0.0, 1.0)

        score = preparation + natural_ability + rng.gauss(0.0, 0.25)
        admitted = score > 1.25

        cases.append(
            AdmissionCase(
                case_id=case_id,
                preparation=preparation,
                natural_ability=natural_ability,
                admitted=admitted,
            )
        )

    return cases


def correlation(x: Sequence[float], y: Sequence[float]) -> float:
    """Pearson correlation implemented from first principles."""
    if len(x) != len(y):
        raise ValueError("x and y must have the same length.")
    if len(x) < 2:
        raise ValueError("At least two observations are required.")

    x_mean = mean(x)
    y_mean = mean(y)

    numerator = sum(
        (x_value - x_mean) * (y_value - y_mean)
        for x_value, y_value in zip(x, y)
    )

    x_sum = sum((x_value - x_mean) ** 2 for x_value in x)
    y_sum = sum((y_value - y_mean) ** 2 for y_value in y)

    denominator = math.sqrt(x_sum * y_sum)

    if denominator == 0:
        raise ValueError("Correlation is undefined for a constant variable.")

    return numerator / denominator


# ---------------------------------------------------------------------------
# Stratified sampling
# ---------------------------------------------------------------------------

def create_strata(
    population: Sequence[Person],
) -> dict[str, list[Person]]:
    """
    Divide the population into experience strata.

    Stratification can improve precision when strata are internally
    homogeneous and appropriately represented.
    """
    strata: dict[str, list[Person]] = {
        "low": [],
        "medium": [],
        "high": [],
    }

    for person in population:
        if person.experience < 5:
            strata["low"].append(person)
        elif person.experience < 10:
            strata["medium"].append(person)
        else:
            strata["high"].append(person)

    return strata


def proportional_stratified_sample(
    population: Sequence[Person],
    sample_size: int,
    seed: int = 11,
) -> list[Person]:
    """
    Draw a proportional stratified sample.

    Rounding is handled using a largest-remainder allocation.
    """
    strata = create_strata(population)

    raw_sizes
