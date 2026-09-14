"""
Probability Basics and Business Applications
============================================

A self-contained study script covering probability from absolute beginner
through advanced practical applications in business.

The script uses only Python's standard library. It demonstrates:
- Probability terminology and axioms
- Sample spaces and events
- Counting principles
- Classical, empirical, and subjective probability
- Complement, union, intersection, and conditional probability
- Independence and mutual exclusivity
- Bayes' theorem
- Random variables and probability distributions
- Expected value, variance, standard deviation, covariance, and correlation
- Bernoulli, Binomial, Geometric, Poisson, and Normal distributions
- Law of Large Numbers and Central Limit Theorem through simulation
- Monte Carlo simulation
- Business applications including:
  * quality control
  * customer conversion
  * fraud detection
  * credit risk
  * inventory and demand
  * insurance
  * marketing
  * A/B testing
  * portfolio risk
  * revenue forecasting
  * decision-making under uncertainty
- Validation, edge cases, common mistakes, and implementation considerations

Run the file directly with Python 3.
"""

from __future__ import annotations

import math
import random
import statistics
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


# ============================================================================
# 1. BASIC TERMINOLOGY
# ============================================================================

def explain_probability_basics() -> None:
    """
    Introduce the core vocabulary used throughout probability.
    """
    print("\n" + "=" * 78)
    print("1. PROBABILITY BASICS")
    print("=" * 78)

    print(
        """
Probability measures uncertainty.

A probability is a number between 0 and 1:
    0     = impossible
    1     = certain
    0.50  = 50% chance

Core terminology:
    Experiment:
        A process with an uncertain outcome.

    Outcome:
        One possible result of an experiment.

    Sample space:
        The complete set of possible outcomes.

    Event:
        A set of one or more outcomes.

Example:
    Rolling a fair six-sided die.

    Sample space:
        S = {1, 2, 3, 4, 5, 6}

    Event A = rolling an even number:
        A = {2, 4, 6}

    Therefore:
        P(A) = 3 / 6 = 0.5

The three fundamental probability axioms are:

    1. Non-negativity:
       P(A) >= 0

    2. Normalization:
       P(S) = 1

    3. Additivity for mutually exclusive events:
       If A and B cannot occur together,
       P(A union B) = P(A) + P(B)
"""
    )


# ============================================================================
# 2. VALIDATION HELPERS
# ============================================================================

def validate_probability(value: float, name: str = "probability") -> None:
    """Raise an error when a value is not a valid probability."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric.")

    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite.")

    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1.")


def validate_nonnegative(value: float, name: str = "value") -> None:
    """Validate a non-negative finite numeric value."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric.")

    if not math.isfinite(float(value)) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number.")


# ============================================================================
# 3. SAMPLE SPACES AND EVENTS
# ============================================================================

def demonstrate_sample_space_and_events() -> None:
    print("\n" + "=" * 78)
    print("2. SAMPLE SPACES AND EVENTS")
    print("=" * 78)

    die = {1, 2, 3, 4, 5, 6}

    even_numbers = {2, 4, 6}
    prime_numbers = {2, 3, 5}
    high_numbers = {4, 5, 6}

    print("Sample space:", die)
    print("Even event:", even_numbers)
    print("Prime event:", prime_numbers)
    print("High-number event:", high_numbers)

    probability_even = len(even_numbers) / len(die)
    probability_prime = len(prime_numbers) / len(die)

    print(f"P(even)  = {probability_even:.4f}")
    print(f"P(prime) = {probability_prime:.4f}")

    # Event operations correspond to set operations.
    union = even_numbers | prime_numbers
    intersection = even_numbers & prime_numbers
    complement_even = die - even_numbers

    print("Even union prime:", union)
    print("Even intersection prime:", intersection)
    print("Complement of even:", complement_even)

    print(
        """
Set notation and probability notation are closely related:

    A union B:
        A or B occurs.

    A intersection B:
        Both A and B occur.

    A complement:
        A does not occur.

For finite equally likely outcomes:

    P(A) = number of outcomes in A / number of outcomes in S
"""
    )


# ============================================================================
# 4. CLASSICAL, EMPIRICAL, AND SUBJECTIVE PROBABILITY
# ============================================================================

def demonstrate_probability_interpretations() -> None:
    print("\n" + "=" * 78)
    print("3. INTERPRETATIONS OF PROBABILITY")
    print("=" * 78)

    # Classical probability.
    classical = 3 / 6
    print(f"Classical probability of rolling an even number: {classical:.3f}")

    # Empirical probability from observed data.
    observations = ["win", "loss", "win", "win", "loss", "win", "loss", "win"]
    empirical = observations.count("win") / len(observations)
    print(f"Empirical win probability: {empirical:.3f}")

    # Subjective probability is represented by an explicit estimate.
    management_estimate = 0.70
    validate_probability(management_estimate, "management estimate")
    print(f"Subjective management estimate: {management_estimate:.3f}")

    print(
        """
Classical probability is appropriate when outcomes are structurally known
to be equally likely.

Empirical probability is estimated from observed data:

    P(A) approximately equals:
        number of observed occurrences of A / total observations

Subjective probability represents a belief or assessment under uncertainty.
It can be informed by expert judgment, historical information, forecasts,
or models.

Business decisions frequently combine these perspectives.
"""
    )


# ============================================================================
# 5. COUNTING PRINCIPLES
# ============================================================================

def factorial(n: int) -> int:
    """Return n! with explicit validation."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an integer.")

    if n < 0:
        raise ValueError("n must be non-negative.")

    return math.factorial(n)


def permutations(n: int, r: int) -> int:
    """Calculate the number of ordered selections."""
    if not all(isinstance(value, int) and not isinstance(value, bool)
               for value in (n, r)):
        raise TypeError("n and r must be integers.")

    if n < 0 or r < 0 or r > n:
        raise ValueError("Require n >= r >= 0.")

    return math.factorial(n) // math.factorial(n - r)


def combinations(n: int, r: int) -> int:
    """Calculate the number of unordered selections."""
    if not all(isinstance(value, int) and not isinstance(value, bool)
               for value in (n, r)):
        raise TypeError("n and r must be integers.")

    if n < 0 or r < 0 or r > n:
        raise ValueError("Require n >= r >= 0.")

    return math.comb(n, r)


def demonstrate_counting() -> None:
    print("\n" + "=" * 78)
    print("4. COUNTING PRINCIPLES")
    print("=" * 78)

    print("5! =", factorial(5))
    print("Permutations P(10, 3) =", permutations(10, 3))
    print("Combinations C(10, 3) =", combinations(10, 3))

    print(
        """
The multiplication principle says that if one stage has m choices and
another has n choices, the combined process has m * n possibilities.

Permutations:
    Order matters.

    P(n, r) = n! / (n-r)!

Combinations:
    Order does not matter.

    C(n, r) = n! / [r!(n-r)!]

Business example:
    If a company selects 3 different products from 10 candidates and the
    order of selection does not matter, there are C(10, 3) possibilities.
"""
    )

    product_choices = 10
    selected = 3
    possible_product_sets = combinations(product_choices, selected)

    print(
        f"Possible sets of {selected} products from {product_choices}: "
        f"{possible_product_sets}"
    )


# ============================================================================
# 6. BASIC PROBABILITY OPERATIONS
# ============================================================================

def probability_of_event(
    favorable_outcomes: int,
    total_outcomes: int,
) -> float:
    """Calculate classical probability for equally likely outcomes."""
    if total_outcomes <= 0:
        raise ValueError("total_outcomes must be positive.")

    if favorable_outcomes < 0 or favorable_outcomes > total_outcomes:
        raise ValueError("favorable_outcomes must be between 0 and total.")

    return favorable_outcomes / total_outcomes


def complement_probability(probability: float) -> float:
    """Calculate P(not A) = 1 - P(A)."""
    validate_probability(probability)
    return 1 - probability


def demonstrate_basic_probability_rules() -> None:
    print("\n" + "=" * 78)
    print("5. BASIC PROBABILITY RULES")
    print("=" * 78)

    p_purchase = probability_of_event(25, 100)
    p_no_purchase = complement_probability(p_purchase)

    print(f"P(purchase)     = {p_purchase:.2%}")
    print(f"P(no purchase)  = {p_no_purchase:.2%}")

    p_a = 0.30
    p_b = 0.20

    # If A and B are mutually exclusive, P(A or B) = P(A) + P(B).
    p_a_or_b_exclusive = p_a + p_b
    print(f"P(A or B), exclusive case = {p_a_or_b_exclusive:.2%}")

    # General addition rule:
    # P(A union B) = P(A) + P(B) - P(A intersection B).
    p_intersection = 0.08
    p_a_or_b = p_a + p_b - p_intersection
    print(f"P(A or B), general rule   = {p_a_or_b:.2%}")

    print(
        """
Complement rule:
    P(A complement) = 1 - P(A)

General addition rule:
    P(A union B) =
        P(A) + P(B) - P(A intersection B)

The subtraction is necessary because the intersection is otherwise counted
twice.

For mutually exclusive events:
    P(A intersection B) = 0

Therefore:
    P(A union B) = P(A) + P(B)
"""
    )


# ============================================================================
# 7. CONDITIONAL PROBABILITY
# ============================================================================

def conditional_probability(
    p_a_and_b: float,
    p_b: float,
) -> float:
    """
    Calculate P(A | B) = P(A and B) / P(B).
    """
    validate_probability(p_a_and_b, "P(A and B)")
    validate_probability(p_b, "P(B)")

    if p_a_and_b > p_b:
        raise ValueError("P(A and B) cannot exceed P(B).")

    if p_b == 0:
        raise ZeroDivisionError("Conditional probability is undefined when P(B)=0.")

    return p_a_and_b / p_b


def demonstrate_conditional_probability() -> None:
    print("\n" + "=" * 78)
    print("6. CONDITIONAL PROBABILITY")
    print("=" * 78)

    p_purchased_and_mobile = 0.18
    p_mobile = 0.30

    p_purchase_given_mobile = conditional_probability(
        p_purchased_and_mobile,
        p_mobile,
    )

    print(
        "P(purchase | mobile visitor) = "
        f"{p_purchase_given_mobile:.2%}"
    )

    print(
        """
Conditional probability answers:

    What is the probability of A given that B has already occurred?

Formula:

    P(A | B) = P(A intersection B) / P(B)

Business example:
    Suppose 30% of website visitors are mobile users and 18% are both
    mobile users and purchasers.

    P(purchase | mobile)
        = 18% / 30%
        = 60%

The conditioning information changes the relevant population from all
visitors to mobile visitors.
"""
    )


# ============================================================================
# 8. INDEPENDENCE AND MUTUAL EXCLUSIVITY
# ============================================================================

def demonstrate_independence_and_exclusivity() -> None:
    print("\n" + "=" * 78)
    print("7. INDEPENDENCE VS MUTUAL EXCLUSIVITY")
    print("=" * 78)

    p_a = 0.40
    p_b = 0.30

    independent_intersection = p_a * p_b
    print(f"If A and B are independent, P(A and B) = {independent_intersection:.2%}")

    print(
        """
Independent events:
    One event does not change the probability of the other.

    P(A intersection B) = P(A)P(B)

Equivalent condition:
    P(A | B) = P(A)

Mutually exclusive events:
    The events cannot occur together.

    P(A intersection B) = 0

Important distinction:
    Events with positive probability generally cannot be both independent
    and mutually exclusive.

Example:
    A = customer receives a discount
    B = customer receives no discount

A and B are mutually exclusive.

By contrast:
    A = first coin toss is heads
    B = second coin toss is heads

These events can occur together and are independent for fair independent
coin tosses.
"""
    )


# ============================================================================
# 9. CONDITIONAL MULTIPLICATION RULE
# ============================================================================

def demonstrate_multiplication_rule() -> None:
    print("\n" + "=" * 78)
    print("8. MULTIPLICATION RULE")
    print("=" * 78)

    p_existing_customer = 0.40
    p_repeat_purchase_given_existing = 0.65

    p_both = p_existing_customer * p_repeat_purchase_given_existing

    print(
        "P(existing customer and repeat purchase) = "
        f"{p_both:.2%}"
    )

    print(
        """
General multiplication rule:

    P(A intersection B) = P(A | B)P(B)

It can also be written as:

    P(A intersection B) = P(B | A)P(A)

This rule is useful whenever one probability is naturally conditional
on another event.
"""
    )


# ============================================================================
# 10. BAYES' THEOREM
# ============================================================================

def bayes_theorem(
    p_b_given_a: float,
    p_a: float,
    p_b_given_not_a: float,
) -> float:
    """
    Calculate P(A | B) using Bayes' theorem.

    P(A|B) =
        P(B|A)P(A) /
        [P(B|A)P(A) + P(B|not A)P(not A)]
    """
    validate_probability(p_b_given_a, "P(B|A)")
    validate_probability(p_a, "P(A)")
    validate_probability(p_b_given_not_a, "P(B|not A)")

    p_not_a = 1 - p_a
    denominator = p_b_given_a * p_a + p_b_given_not_a * p_not_a

    if denominator == 0:
        raise ZeroDivisionError("P(B) is zero, so P(A|B) is undefined.")

    return (p_b_given_a * p_a) / denominator


def demonstrate_bayes_theorem() -> None:
    print("\n" + "=" * 78)
    print("9. BAYES' THEOREM")
    print("=" * 78)

    # Fraud screening example.
    fraud_rate = 0.01
    fraud_flag_if_fraud = 0.90
    fraud_flag_if_not_fraud = 0.05

    probability_fraud_given_flag = bayes_theorem(
        fraud_flag_if_fraud,
        fraud_rate,
        fraud_flag_if_not_fraud,
    )

    print(
        "P(fraud | flagged transaction) = "
        f"{probability_fraud_given_flag:.2%}"
    )

    print(
        """
Bayes' theorem reverses conditional probabilities.

    P(A | B) =
        P(B | A)P(A) / P(B)

Expanded form for a binary A:

    P(A | B) =
        P(B | A)P(A)
        ---------------------------------
        P(B | A)P(A) + P(B | not A)P(not A)

The prior probability matters.

Fraud example:
    Only 1% of transactions are fraudulent.
    A fraud system flags 90% of fraudulent transactions.
    It also flags 5% of legitimate transactions.

Even though the detection rate is high, the probability that a flagged
transaction is actually fraudulent is substantially lower than 90%.

This is a base-rate effect.

Bayes' theorem is important in:
    - fraud detection
    - medical testing
    - credit risk
    - quality inspection
    - customer classification
    - cybersecurity
    - forecasting
"""
    )


# ============================================================================
# 11. DISCRETE RANDOM VARIABLES
# ============================================================================

@dataclass
class DiscreteDistribution:
    """Represent a finite discrete probability distribution."""

    probabilities: dict[float, float]

    def validate(self) -> None:
        if not self.probabilities:
            raise ValueError("Distribution cannot be empty.")

        for value, probability in self.probabilities.items():
            if not isinstance(value, (int, float)):
                raise TypeError("Outcomes must be numeric.")
            validate_probability(probability, f"P(X={value})")

        total = sum(self.probabilities.values())

        if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(
                f"Probabilities must sum to 1. Current total is {total}."
            )

    def expected_value(self) -> float:
        self.validate()
        return sum(
            value * probability
            for value, probability in self.probabilities.items()
        )

    def variance(self) -> float:
        self.validate()
        mean = self.expected_value()

        return sum(
            ((value - mean) ** 2) * probability
            for value, probability in self.probabilities.items()
        )

    def standard_deviation(self) -> float:
        return math.sqrt(self.variance())

    def probability_at_least(self, threshold: float) -> float:
        self.validate()

        return sum(
            probability
            for value, probability in self.probabilities.items()
            if value >= threshold
        )


def demonstrate_random_variables() -> None:
    print("\n" + "=" * 78)
    print("10. RANDOM VARIABLES AND DISTRIBUTIONS")
    print("=" * 78)

    distribution = DiscreteDistribution(
        {
            0: 0.10,
            1: 0.20,
            2: 0.30,
            3: 0.25,
            4: 0.15,
        }
    )

    print(f"E[X] = {distribution.expected_value():.4f}")
    print(f"Var(X) = {distribution.variance():.4f}")
    print(f"SD(X) = {distribution.standard_deviation():.4f}")
    print(f"P(X >= 3) = {distribution.probability_at_least(3):.2%}")

    print(
        """
A random variable maps outcomes of a random experiment to numerical values.

Discrete random variable:
    Has countable possible values.

Continuous random variable:
    Can take values over an interval.

A probability mass function, or PMF, gives probabilities for discrete
outcomes.

For a valid PMF:
    P(X=x) >= 0
    Sum of all probabilities = 1

Expected value:
    E[X] = sum(x * P(X=x))

Variance:
    Var(X) = E[(X - E[X])^2]

Standard deviation:
    SD(X) = sqrt(Var(X))
"""
    )


# ============================================================================
# 12. BERNOULLI DISTRIBUTION
# ============================================================================

def bernoulli_pmf(x: int, p: float) -> float:
    """Probability mass function for a Bernoulli random variable."""
    validate_probability(p)

    if x == 1:
        return p
    if x == 0:
        return 1 - p

    return 0.0


def demonstrate_bernoulli_distribution() -> None:
    print("\n" + "=" * 78)
    print("11. BERNOULLI DISTRIBUTION")
    print("=" * 78)

    conversion_probability = 0.08

    print(f"P(conversion) = {bernoulli_pmf(1, conversion_probability):.2%}")
    print(f"P(no conversion) = {bernoulli_pmf(0, conversion_probability):.2%}")

    print(
        """
A Bernoulli experiment has exactly two outcomes:

    Success = 1
    Failure = 0

If P(success) = p:

    P(X=1) = p
    P(X=0) = 1-p

Mean:
    E[X] = p

Variance:
    Var(X) = p(1-p)

Business examples:
    - customer converts or does not convert
    - loan defaults or does not default
    - machine passes or fails inspection
    - transaction is fraudulent or legitimate
"""
    )


# ============================================================================
# 13. BINOMIAL DISTRIBUTION
# ============================================================================

def binomial_pmf(n: int, k: int, p: float) -> float:
    """
    Calculate P(X=k) for X ~ Binomial(n,p).
    """
    if not isinstance(n, int) or not isinstance(k, int):
        raise TypeError("n and k must be integers.")

    if n < 0:
        raise ValueError("n must be non-negative.")

    if k < 0 or k > n:
        return 0.0

    validate_probability(p)

    return combinations(n, k) * (p ** k) * ((1 - p) ** (n - k))


def binomial_cdf_at_least(n: int, k: int, p: float) -> float:
    """Calculate P(X >= k) for a binomial random variable."""
    if k <= 0:
        return 1.0

    if k > n:
        return 0.0

    return sum(binomial_pmf(n, value, p) for value in range(k, n + 1))


def demonstrate_binomial_distribution() -> None:
    print("\n" + "=" * 78)
    print("12. BINOMIAL DISTRIBUTION")
    print("=" * 78)

    n = 20
    p = 0.10

    exactly_three = binomial_pmf(n, 3, p)
    at_least_three = binomial_cdf_at_least(n, 3, p)

    print(f"P(exactly 3 conversions) = {exactly_three:.2%}")
    print(f"P(at least 3 conversions) = {at_least_three:.2%}")

    print(
        """
The binomial distribution models the number of successes in n independent
Bernoulli trials with the same success probability p.

Formula:

    P(X=k) = C(n,k)p^k(1-p)^(n-k)

Mean:
    E[X] = np

Variance:
    Var(X) = np(1-p)

Business example:
    If 20 independent prospects each have a 10% conversion probability,
    the number of conversions can be modeled with a binomial distribution.

Important assumptions:
    - fixed number of trials
    - two outcomes per trial
    - same success probability
    - independence between trials

If those assumptions fail, the binomial model may be inappropriate.
"""
    )


# ============================================================================
# 14. GEOMETRIC DISTRIBUTION
# ============================================================================

def geometric_pmf(k: int, p: float) -> float:
    """
    Calculate probability that the first success occurs on trial k.
    """
    if not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer.")

    validate_probability(p)

    if p == 0:
        return 0.0

    return ((1 - p) ** (k - 1)) * p


def demonstrate_geometric_distribution() -> None:
    print("\n" + "=" * 78)
    print("13. GEOMETRIC DISTRIBUTION")
    print("=" * 78)

    p = 0.20

    print(
        f"P(first sale occurs on 5th contact) = "
        f"{geometric_pmf(5, p):.2%}"
    )

    print(
        """
The geometric distribution models the number of independent trials needed
to obtain the first success.

For k = 1, 2, 3, ...:

    P(X=k) = (1-p)^(k-1)p

Mean:
    E[X] = 1/p

Business examples:
    - number of calls until first sale
    - number of applications until first approval
    - number of attempts until a system succeeds

The geometric distribution has the memoryless property:
    P(X > m+n | X > m) = P(X > n)
"""
    )


# ============================================================================
# 15. POISSON DISTRIBUTION
# ============================================================================

def poisson_pmf(k: int, lam: float) -> float:
    """
    Calculate P(X=k) for a Poisson random variable with rate lambda.
    """
    if not isinstance(k, int) or k < 0:
        raise ValueError("k must be a non-negative integer.")

    validate_nonnegative(lam, "lambda")

    if lam == 0:
        return 1.0 if k == 0 else 0.0

    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def demonstrate_poisson_distribution() -> None:
    print("\n" + "=" * 78)
    print("14. POISSON DISTRIBUTION")
    print("=" * 78)

    average_calls_per_hour = 8
    exactly_five = poisson_pmf(5, average_calls_per_hour)

    print(
        f"P(exactly 5 calls in an hour) = "
        f"{exactly_five:.2%}"
    )

    print(
        """
The Poisson distribution models the number of events occurring in a fixed
interval when events occur at an average rate.

PMF:

    P(X=k) = e^(-lambda) lambda^k / k!

Mean:
    E[X] = lambda

Variance:
    Var(X) = lambda

Business examples:
    - customer service calls per hour
    - website failures per day
    - insurance claims per month
    - arrivals at a store
    - machine defects per production batch

A Poisson model is most appropriate when events are count-based and the
event rate is reasonably stable over the relevant interval.
"""
    )


# ============================================================================
# 16. NORMAL DISTRIBUTION
# ============================================================================

def normal_pdf(x: float, mean: float, standard_deviation: float) -> float:
    """Calculate the normal probability density at x."""
    if standard_deviation <= 0:
        raise ValueError("standard_deviation must be positive.")

    coefficient = 1 / (
        standard_deviation * math.sqrt(2 * math.pi)
    )

    exponent = -0.5 * ((x - mean) / standard_deviation) ** 2

    return coefficient * math.exp(exponent)


def normal_cdf(
    x: float,
    mean: float = 0.0,
    standard_deviation: float = 1.0,
) -> float:
    """Calculate the normal cumulative distribution function."""
    if standard_deviation <= 0:
        raise ValueError("standard_deviation must be positive.")

    z = (x - mean) / standard_deviation

    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def demonstrate_normal_distribution() -> None:
    print("\n" + "=" * 78)
    print("15. NORMAL DISTRIBUTION")
    print("=" * 78)

    mean = 100
    sd = 15

    probability_below_130 = normal_cdf(130, mean, sd)
    probability_above_130 = 1 - probability_below_130

    print(f"P(X <= 130) = {probability_below_130:.2%}")
    print(f"P(X > 130)  = {probability_above_130:.2%}")
    print(f"PDF at x=100 = {normal_pdf(100, mean, sd):.6f}")

    print(
        """
The normal distribution is continuous and symmetric around its mean.

Its parameters are:
    mu     = mean
    sigma  = standard deviation

Standardization:

    Z = (X - mu) / sigma

The normal distribution appears frequently in statistical modeling because
sums and averages of many independent observations often become approximately
normal under suitable conditions.

Business applications:
    - forecasting
    - measurement error
    - process variation
    - service times
    - financial returns in simplified models
    - quality control

Important limitation:
    Real business data are not automatically normal. Skewness, heavy tails,
    outliers, bounded variables, and dependence can make a normal model
    inappropriate.
"""
    )


# ============================================================================
# 17. EXPECTED VALUE
# ============================================================================

def expected_value(values: Sequence[float], probabilities: Sequence[float]) -> float:
    """Calculate the expected value of a discrete random variable."""
    if len(values) != len(probabilities):
        raise ValueError("values and probabilities must have equal lengths.")

    if not values:
        raise ValueError("At least one outcome is required.")

    for probability in probabilities:
        validate_probability(probability)

    if not math.isclose(sum(probabilities), 1.0, abs_tol=1e-12):
        raise ValueError("Probabilities must sum to 1.")

    return sum(value * probability for value, probability in zip(values, probabilities))


def demonstrate_expected_value_business_case() -> None:
    print("\n" + "=" * 78)
    print("16. EXPECTED VALUE IN BUSINESS DECISIONS")
    print("=" * 78)

    outcomes = [-10000, 2000, 15000, 30000]
    probabilities = [0.10, 0.30, 0.40, 0.20]

    ev = expected_value(outcomes, probabilities)

    print("Possible project outcomes:", outcomes)
    print("Probabilities:", probabilities)
    print(f"Expected monetary value = ${ev:,.2f}")

    print(
        """
Expected value is a probability-weighted average.

For a discrete variable:

    E[X] = sum(x_i P(X=x_i))

Expected monetary value is useful for decisions involving uncertain
financial outcomes.

A positive expected value does not guarantee profit on one realization.
It represents a long-run average under the stated probability model.

Decision-making should also consider:
    - downside risk
    - liquidity
    - timing
    - risk tolerance
    - strategic effects
    - model uncertainty
"""
    )


# ============================================================================
# 18. VARIANCE, STANDARD DEVIATION, COVARIANCE, CORRELATION
# ============================================================================

def population_variance(values: Sequence[float]) -> float:
    """Calculate population variance."""
    if not values:
        raise ValueError("values cannot be empty.")

    mean = statistics.fmean(values)
    return statistics.fmean((value - mean) ** 2 for value in values)


def population_covariance(
    x_values: Sequence[float],
    y_values: Sequence[float],
) -> float:
    """Calculate population covariance."""
    if len(x_values) != len(y_values):
        raise ValueError("Both sequences must have equal lengths.")

    if not x_values:
        raise ValueError("Sequences cannot be empty.")

    x_mean = statistics.fmean(x_values)
    y_mean = statistics.fmean(y_values)

    return statistics.fmean(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(x_values, y_values)
    )


def population_correlation(
    x_values: Sequence[float],
    y_values: Sequence[float],
) -> float:
    """Calculate Pearson population correlation."""
    covariance = population_covariance(x_values, y_values)

    x_sd = math.sqrt(population_variance(x_values))
    y_sd = math.sqrt(population_variance(y_values))

    if x_sd == 0 or y_sd == 0:
        raise ZeroDivisionError(
            "Correlation is undefined when either variable has zero variance."
        )

    return covariance / (x_sd * y_sd)


def demonstrate_variance_and_correlation() -> None:
    print("\n" + "=" * 78)
    print("17. VARIANCE, COVARIANCE, AND CORRELATION")
    print("=" * 78)

    revenue = [100, 110, 95, 125, 130]
    advertising = [10, 12, 9, 15, 17]

    revenue_variance = population_variance(revenue)
    revenue_sd = math.sqrt(revenue_variance)
    covariance = population_covariance(revenue, advertising)
    correlation = population_correlation(revenue, advertising)

    print(f"Revenue variance = {revenue_variance:.2f}")
    print(f"Revenue standard deviation = {revenue_sd:.2f}")
    print(f"Revenue-advertising covariance = {covariance:.2f}")
    print(f"Revenue-advertising correlation = {correlation:.4f}")

    print(
        """
Variance measures dispersion around the mean:

    Var(X) = E[(X - mu)^2]

Standard deviation:

    SD(X) = sqrt(Var(X))

Covariance measures whether two variables tend to move together:

    Cov(X,Y) = E[(X-mu_X)(Y-mu_Y)]

Correlation standardizes covariance:

    Corr(X,Y) = Cov(X,Y) / [SD(X)SD(Y)]

Correlation lies between -1 and +1.

Important:
    Correlation measures association, not causation.

A strong correlation between advertising and revenue does not by itself
prove that advertising caused the revenue change.
"""
    )


# ============================================================================
# 19. LAW OF LARGE NUMBERS
# ============================================================================

def simulate_coin_flips(
    number_of_flips: int,
    probability_of_heads: float = 0.5,
    seed: int | None = None,
) -> float:
    """Simulate coin flips and return the observed proportion of heads."""
    if number_of_flips <= 0:
        raise ValueError("number_of_flips must be positive.")

    validate_probability(probability_of_heads)

    rng = random.Random(seed)

    heads = sum(
        rng.random() < probability_of_heads
        for _ in range(number_of_flips)
    )

    return heads / number_of_flips


def demonstrate_law_of_large_numbers() -> None:
    print("\n" + "=" * 78)
    print("18. LAW OF LARGE NUMBERS")
    print("=" * 78)

    for number_of_flips in (10, 100, 1_000, 10_000, 100_000):
        observed = simulate_coin_flips(
            number_of_flips,
            probability_of_heads=0.5,
            seed=42,
        )
        print(
            f"{number_of_flips:>7,} flips -> observed heads = {observed:.4f}"
        )

    print(
        """
The Law of Large Numbers states that, under appropriate conditions, the
sample average tends to approach the expected value as the number of
observations increases.

It does not mean:
    - short sequences must look balanced
    - every future sample will be close to the mean
    - random events compensate for previous outcomes

For example, after several heads, a fair coin is still 50% likely to
produce heads on the next independent toss.

This distinction prevents the gambler's fallacy.
"""
    )


# ============================================================================
# 20. CENTRAL LIMIT THEOREM
# ============================================================================

def demonstrate_central_limit_theorem() -> None:
    print("\n" + "=" * 78)
    print("19. CENTRAL LIMIT THEOREM")
    print("=" * 78)

    rng = random.Random(12345)

    sample_means: list[float] = []

    # A uniform distribution is not normal, but averages of many independent
    # observations become approximately normal under common CLT conditions.
    for _ in range(10_000):
        sample = [rng.random() for _ in range(30)]
        sample_means.append(statistics.fmean(sample))

    mean_of_means = statistics.fmean(sample_means)
    sd_of_means = statistics.pstdev(sample_means)

    print(f"Mean of sample means = {mean_of_means:.4f}")
    print(f"SD of sample means   = {sd_of_means:.4f}")

    print(
        """
The Central Limit Theorem states, roughly, that the sampling distribution
of the mean becomes approximately normal as sample size grows, provided
appropriate regularity conditions are satisfied.

If individual observations have:
    mean = mu
    standard deviation = sigma

then the sample mean has approximately:

    mean = mu
    standard error = sigma / sqrt(n)

The CLT is foundational for:
    - confidence intervals
    - hypothesis testing
    - sample-size calculations
    - business experiments
    - survey analysis
    - quality-control analysis
"""
    )


# ============================================================================
# 21. MONTE CARLO SIMULATION
# ============================================================================

def monte_carlo_probability(
    event_function: Callable[[random.Random], bool],
    trials: int,
    seed: int | None = None,
) -> float:
    """
    Estimate a probability by repeated random simulation.
    """
    if trials <= 0:
        raise ValueError("trials must be positive.")

    rng = random.Random(seed)

    successes = sum(
        event_function(rng)
        for _ in range(trials)
    )

    return successes / trials


def demonstrate_monte_carlo() -> None:
    print("\n" + "=" * 78)
    print("20. MONTE CARLO SIMULATION")
    print("=" * 78)

    def event_inside_unit_circle(rng: random.Random) -> bool:
        x = rng.uniform(-1, 1)
        y = rng.uniform(-1, 1)
        return x * x + y * y <= 1

    estimated_probability = monte_carlo_probability(
        event_inside_unit_circle,
        trials=100_000,
        seed=2026,
    )

    estimated_pi = 4 * estimated_probability

    print(f"Estimated probability inside circle = {estimated_probability:.5f}")
    print(f"Estimated pi = {estimated_pi:.5f}")
    print(f"Actual pi = {math.pi:.5f}")

    print(
        """
Monte Carlo simulation estimates uncertain quantities through repeated
random sampling.

General structure:

    1. Define uncertain inputs.
    2. Generate random scenarios.
    3. Evaluate the outcome.
    4. Repeat many times.
    5. Analyze the resulting distribution.

Business uses:
    - demand forecasting
    - inventory planning
    - financial risk
    - project completion risk
    - insurance loss modeling
    - capacity planning
    - pricing scenarios

A simulation is only as credible as:
    - its input distributions
    - its dependencies
    - its assumptions
    - its data
    - its number of trials
"""
    )


# ============================================================================
# 22. BUSINESS APPLICATION: CONVERSION FUNNEL
# ============================================================================

def funnel_probability(
    visit_to_signup: float,
    signup_to_trial: float,
    trial_to_customer: float,
) -> float:
    """Calculate overall conversion probability for sequential independent stages."""
    for probability in (
        visit_to_signup,
        signup_to_trial,
        trial_to_customer,
    ):
        validate_probability(probability)

    return (
        visit_to_signup
        * signup_to_trial
        * trial_to_customer
    )


def demonstrate_conversion_funnel() -> None:
    print("\n" + "=" * 78)
    print("21. BUSINESS APPLICATION: CONVERSION FUNNEL")
    print("=" * 78)

    p_signup = 0.20
    p_trial_given_signup = 0.40
    p_customer_given_trial = 0.25

    overall = funnel_probability(
        p_signup,
        p_trial_given_signup,
        p_customer_given_trial,
    )

    visitors = 50_000
    expected_customers = visitors * overall

    print(f"Overall visitor-to-customer probability = {overall:.2%}")
    print(f"Expected customers from {visitors:,} visitors = {expected_customers:,.0f}")

    print(
        """
For a sequence of stages:

    P(all stages) =
        P(stage 1)
        * P(stage 2 | stage 1)
        * P(stage 3 | stage 2)
        * ...

This decomposition is useful for business funnels.

If 50,000 visitors enter a funnel and the modeled end-to-end probability
is 2%, expected conversions are approximately 1,000.

This is an expected count, not a guarantee.
"""
    )


# ============================================================================
# 23. BUSINESS APPLICATION: EXPECTED REVENUE
# ============================================================================

def expected_revenue_per_customer(
    outcomes: Sequence[float],
    probabilities: Sequence[float],
) -> float:
    """Calculate expected revenue from one randomly selected customer."""
    return expected_value(outcomes, probabilities)


def demonstrate_expected_revenue() -> None:
    print("\n" + "=" * 78)
    print("22. BUSINESS APPLICATION: EXPECTED REVENUE")
    print("=" * 78)

    order_values = [20, 50, 100, 250]
    order_probabilities = [0.30, 0.35, 0.25, 0.10]

    expected_order_value = expected_revenue_per_customer(
        order_values,
        order_probabilities,
    )

    customers = 12_000
    expected_revenue = customers * expected_order_value

    print(f"Expected order value = ${expected_order_value:.2f}")
    print(f"Expected revenue for {customers:,} customers = ${expected_revenue:,.2f}")

    print(
        """
Expected revenue can be decomposed as:

    Expected revenue =
        expected number of customers
        * expected revenue per customer

Probability distributions allow a business to represent uncertainty in
transaction size rather than relying only on one average assumption.
"""
    )


# ============================================================================
# 24. BUSINESS APPLICATION: QUALITY CONTROL
# ============================================================================

def demonstrate_quality_control() -> None:
    print("\n" + "=" * 78)
    print("23. BUSINESS APPLICATION: QUALITY CONTROL")
    print("=" * 78)

    defect_rate = 0.02
    batch_size = 100

    probability_exactly_two_defects = binomial_pmf(
        batch_size,
        2,
        defect_rate,
    )

    probability_at_least_one_defect = 1 - binomial_pmf(
        batch_size,
        0,
        defect_rate,
    )

    print(f"P(exactly 2 defects) = {probability_exactly_two_defects:.2%}")
    print(f"P(at least 1 defect) = {probability_at_least_one_defect:.2%}")

    print(
        """
If individual units have a defect probability p and inspections are
approximately independent, the number of defects in a batch of n units
can be modeled with a binomial distribution.

The probability of no defects is:

    P(X=0) = (1-p)^n

Therefore:

    P(at least one defect) = 1 - (1-p)^n

This can help determine:
    - inspection requirements
    - acceptable quality levels
    - expected rework
    - supplier risk
    - production planning

Independence should not be assumed blindly. Manufacturing defects can be
clustered because of machine settings, raw materials, operators, or batches.
"""
    )


# ============================================================================
# 25. BUSINESS APPLICATION: INVENTORY AND DEMAND
# ============================================================================

def poisson_probability_range(
    lower: int,
    upper: int,
    lam: float,
) -> float:
    """Calculate P(lower <= X <= upper) for a Poisson random variable."""
    if lower < 0 or upper < lower:
        raise ValueError("Require 0 <= lower <= upper.")

    return sum(
        poisson_pmf(k, lam)
        for k in range(lower, upper + 1)
    )


def demonstrate_inventory_risk() -> None:
    print("\n" + "=" * 78)
    print("24. BUSINESS APPLICATION: INVENTORY AND DEMAND")
    print("=" * 78)

    average_daily_demand = 20
    inventory = 25

    stockout_probability = 1 - poisson_probability_range(
        0,
        inventory,
        average_daily_demand,
    )

    print(f"Average daily demand = {average_daily_demand}")
    print(f"Inventory available = {inventory}")
    print(f"Approximate stockout probability = {stockout_probability:.2%}")

    print(
        """
Inventory decisions involve uncertain demand.

If daily demand is modeled as a random variable D, the probability of a
stockout for inventory level Q is:

    P(D > Q)

A service-level target can be used to choose an inventory level.

For example:
    target stockout probability <= 5%

The model must reflect:
    - demand seasonality
    - promotions
    - lead times
    - product substitution
    - stockout effects
    - dependence between days
    - supply uncertainty

A simple Poisson model is useful for demonstration but may be insufficient
for highly variable or seasonal demand.
"""
    )


# ============================================================================
# 26. BUSINESS APPLICATION: FRAUD DETECTION AND BASE RATES
# ============================================================================

def fraud_confusion_matrix(
    population: int,
    fraud_rate: float,
    sensitivity: float,
    false_positive_rate: float,
) -> dict[str, float]:
    """
    Produce expected counts for a binary fraud classifier.

    sensitivity = P(flag | fraud)
    false_positive_rate = P(flag | legitimate)
    """
    for value, name in (
        (fraud_rate, "fraud_rate"),
        (sensitivity, "sensitivity"),
        (false_positive_rate, "false_positive_rate"),
    ):
        validate_probability(value, name)

    fraud = population * fraud_rate
    legitimate = population - fraud

    true_positives = fraud * sensitivity
    false_negatives = fraud * (1 - sensitivity)

    false_positives = legitimate * false_positive_rate
    true_negatives = legitimate * (1 - false_positive_rate)

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "true_negatives": true_negatives,
    }


def demonstrate_fraud_detection() -> None:
    print("\n" + "=" * 78)
    print("25. BUSINESS APPLICATION: FRAUD DETECTION")
    print("=" * 78)

    matrix = fraud_confusion_matrix(
        population=1_000_000,
        fraud_rate=0.01,
        sensitivity=0.90,
        false_positive_rate=0.05,
    )

    for label, value in matrix.items():
        print(f"{label:>18}: {value:,.0f}")

    flagged = matrix["true_positives"] + matrix["false_positives"]
    precision = matrix["true_positives"] / flagged

    print(f"Precision among flagged transactions: {precision:.2%}")

    print(
        """
Classifier terminology:

    Sensitivity / recall:
        P(flag | fraud)

    False-positive rate:
        P(flag | legitimate)

    Precision:
        P(fraud | flagged)

Sensitivity and precision are different quantities.

A system can have high sensitivity while having relatively low precision
when the underlying fraud rate is very low.

Operational consequences include:
    - investigation workload
    - customer friction
    - missed fraud
    - financial losses
    - reputational costs

Threshold selection should therefore consider business costs, not only
classification accuracy.
"""
    )


# ============================================================================
# 27. BUSINESS APPLICATION: CREDIT RISK
# ============================================================================

def expected_credit_loss(
    probability_of_default: float,
    exposure: float,
    loss_given_default: float,
) -> float:
    """
    Calculate Expected Credit Loss:

        ECL = PD * EAD * LGD
    """
    validate_probability(probability_of_default, "PD")
    validate_probability(loss_given_default, "LGD")
    validate_nonnegative(exposure, "EAD")

    return probability_of_default * exposure * loss_given_default


def demonstrate_credit_risk() -> None:
    print("\n" + "=" * 78)
    print("26. BUSINESS APPLICATION: CREDIT RISK")
    print("=" * 78)

    pd = 0.04
    ead = 500_000
    lgd = 0.45

    ecl = expected_credit_loss(pd, ead, lgd)

    print(f"Probability of default = {pd:.2%}")
    print(f"Exposure at default   = ${ead:,.2f}")
    print(f"Loss given default    = {lgd:.2%}")
    print(f"Expected credit loss  = ${ecl:,.2f}")

    print(
        """
A simplified expected credit loss framework is:

    ECL = PD * EAD * LGD

Where:
    PD  = probability of default
    EAD = exposure at default
    LGD = loss given default

Example:
    PD  = 4%
    EAD = $500,000
    LGD = 45%

Then:

    ECL = 0.04 * 500,000 * 0.45
        = $9,000

Real credit-risk systems may incorporate:
    - time horizons
    - discounting
    - macroeconomic scenarios
    - borrower segments
    - collateral
    - recovery timing
    - correlations
    - model uncertainty
"""
    )


# ============================================================================
# 28. BUSINESS APPLICATION: INSURANCE
# ============================================================================

def expected_insurance_loss(
    claim_probability: float,
    average_claim: float,
) -> float:
    """Calculate expected loss for one insured exposure."""
    validate_probability(claim_probability, "claim_probability")
    validate_nonnegative(average_claim, "average_claim")

    return claim_probability * average_claim


def demonstrate_insurance() -> None:
    print("\n" + "=" * 78)
    print("27. BUSINESS APPLICATION: INSURANCE")
    print("=" * 78)

    claim_probability = 0.03
    average_claim = 80_000

    expected_loss = expected_insurance_loss(
        claim_probability,
        average_claim,
    )

    administrative_cost = 1_500
    risk_margin = 1_000

    illustrative_premium = (
        expected_loss
        + administrative_cost
        + risk_margin
    )

    print(f"Expected claim loss = ${expected_loss:,.2f}")
    print(f"Illustrative premium = ${illustrative_premium:,.2f}")

    print(
        """
Insurance pricing starts from expected loss but does not end there.

A simplified model is:

    Expected loss = P(claim) * Expected claim amount

A practical premium may also account for:
    - operating expenses
    - capital requirements
    - uncertainty
    - reinsurance
    - taxes
    - profit or risk margin
    - claim frequency and severity distributions

Expected value alone does not capture tail risk.
"""
    )


# ============================================================================
# 29. BUSINESS APPLICATION: A/B TESTING
# ============================================================================

@dataclass
class ABTestResult:
    """Store basic conversion results for an A/B test."""

    visitors_a: int
    conversions_a: int
    visitors_b: int
    conversions_b: int

    @property
    def rate_a(self) -> float:
        if self.visitors_a <= 0:
            raise ValueError("visitors_a must be positive.")
        return self.conversions_a / self.visitors_a

    @property
    def rate_b(self) -> float:
        if self.visitors_b <= 0:
            raise ValueError("visitors_b must be positive.")
        return self.conversions_b / self.visitors_b

    @property
    def absolute_lift(self) -> float:
        return self.rate_b - self.rate_a

    @property
    def relative_lift(self) -> float:
        if self.rate_a == 0:
            raise ZeroDivisionError("Relative lift is undefined when rate A is zero.")
        return (self.rate_b - self.rate_a) / self.rate_a


def two_proportion_standard_error(
    rate_a: float,
    rate_b: float,
    n_a: int,
    n_b: int,
) -> float:
    """Calculate the unpooled standard error for a difference in proportions."""
    if n_a <= 0 or n_b <= 0:
        raise ValueError("Sample sizes must be positive.")

    validate_probability(rate_a, "rate_a")
    validate_probability(rate_b, "rate_b")

    variance = (
        rate_a * (1 - rate_a) / n_a
        + rate_b * (1 - rate_b) / n_b
    )

    return math.sqrt(variance)


def demonstrate_ab_testing() -> None:
    print("\n" + "=" * 78)
    print("28. BUSINESS APPLICATION: A/B TESTING")
    print("=" * 78)

    result = ABTestResult(
        visitors_a=10_000,
        conversions_a=800,
        visitors_b=10_000,
        conversions_b=900,
    )

    se = two_proportion_standard_error(
        result.rate_a,
        result.rate_b,
        result.visitors_a,
        result.visitors_b,
    )

    z_score = result.absolute_lift / se if se > 0 else math.inf
    approximate_two_sided_p_value = 2 * (1 - normal_cdf(abs(z_score)))

    print(f"Conversion rate A = {result.rate_a:.2%}")
    print(f"Conversion rate B = {result.rate_b:.2%}")
    print(f"Absolute lift = {result.absolute_lift:.2%}")
    print(f"Relative lift = {result.relative_lift:.2%}")
    print(f"Approximate z-score = {z_score:.3f}")
    print(f"Approximate two-sided p-value = {approximate_two_sided_p_value:.6f}")

    print(
        """
A/B testing compares outcomes under two variants.

For a binary outcome such as conversion:

    conversion rate = conversions / visitors

Useful quantities include:

    Absolute lift:
        rate_B - rate_A

    Relative lift:
        (rate_B - rate_A) / rate_A

Probability and sampling theory are used to determine whether an observed
difference could plausibly arise from random variation.

A proper experiment requires attention to:
    - random assignment
    - adequate sample size
    - consistent measurement
    - exposure windows
    - sample-ratio mismatch
    - repeated testing
    - practical significance
    - statistical significance

A small p-value does not automatically imply a large or economically
important effect.
"""
    )


# ============================================================================
# 30. BUSINESS APPLICATION: PORTFOLIO EXPECTED RETURN
# ============================================================================

def portfolio_expected_return(
    returns: Sequence[float],
    weights: Sequence[float],
) -> float:
    """Calculate a weighted portfolio expected return."""
    if len(returns) != len(weights):
        raise ValueError("returns and weights must have equal lengths.")

    if not returns:
        raise ValueError("At least one asset is required.")

    if not math.isclose(sum(weights), 1.0, abs_tol=1e-12):
        raise ValueError("Portfolio weights must sum to 1.")

    return sum(
        asset_return * weight
        for asset_return, weight in zip(returns, weights)
    )


def demonstrate_portfolio_probability() -> None:
    print("\n" + "=" * 78)
    print("29. BUSINESS APPLICATION: PORTFOLIO EXPECTED RETURN")
    print("=" * 78)

    expected_returns = [0.08, 0.12, 0.05]
    weights = [0.50, 0.30, 0.20]

    portfolio_return = portfolio_expected_return(
        expected_returns,
        weights,
    )

    print(f"Expected portfolio return = {portfolio_return:.2%}")

    print(
        """
For a portfolio with asset weights w_i and expected returns E[R_i]:

    E[R_p] = sum(w_i E[R_i])

Risk depends on covariance as well as individual asset volatility.

Therefore:
    Expected return does not determine portfolio risk.

Two portfolios can have the same expected return but very different
risk because their asset returns may have different correlations.
"""
    )


# ============================================================================
# 31. SIMULATION OF BUSINESS DEMAND
# ============================================================================

def simulate_daily_demand(
    days: int,
    average_demand: float,
    seed: int | None = None,
) -> list[int]:
    """
    Simulate daily demand using a Poisson distribution.

    Uses inverse-transform sampling without external libraries.
    """
    if days <= 0:
        raise ValueError("days must be positive.")

    validate_nonnegative(average_demand, "average_demand")

    rng = random.Random(seed)
    demand_values: list[int] = []

    if average_demand == 0:
        return [0] * days

    for _ in range(days):
        threshold = math.exp(-average_demand)
        probability = 1.0
        k = 0

        while probability > threshold:
            k += 1
            probability *= rng.random()

        demand_values.append(k - 1)

    return demand_values


def demonstrate_demand_simulation() -> None:
    print("\n" + "=" * 78)
    print("30. SIMULATED DEMAND DISTRIBUTION")
    print("=" * 78)

    demand = simulate_daily_demand(
        days=10_000,
        average_demand=30,
        seed=2026,
    )

    print(f"Simulated mean demand = {statistics.fmean(demand):.2f}")
    print(f"Simulated demand SD   = {statistics.pstdev(demand):.2f}")
    print(f"Minimum demand        = {min(demand)}")
    print(f"Maximum demand        = {max(demand)}")

    print(
        """
Simulation converts probability assumptions into many possible business
scenarios.

For inventory planning, a simulation can estimate:
    - average demand
    - demand volatility
    - stockout frequency
    - excess inventory
    - service levels

Simulation is especially useful when several uncertain variables interact
and closed-form formulas become difficult.
"""
    )


# ============================================================================
# 32. JOINT PROBABILITY AND CONTINGENCY TABLES
# ============================================================================

def conditional_from_counts(
    joint_count: int,
    conditioning_count: int,
) -> float:
    """Calculate conditional probability from observed counts."""
    if joint_count < 0 or conditioning_count < 0:
        raise ValueError("Counts must be non-negative.")

    if joint_count > conditioning_count:
        raise ValueError("Joint count cannot exceed conditioning count.")

    if conditioning_count == 0:
        raise ZeroDivisionError("Conditioning count cannot be zero.")

    return joint_count / conditioning_count


def demonstrate_contingency_table() -> None:
    print("\n" + "=" * 78)
    print("31. JOINT PROBABILITIES AND CONTINGENCY TABLES")
    print("=" * 78)

    # Rows: customer segment
    # Columns: purchased or did not purchase
    new_customers = {"purchase": 180, "no_purchase": 820}
    returning_customers = {"purchase": 240, "no_purchase": 760}

    p_purchase_given_new = conditional_from_counts(
        new_customers["purchase"],
        sum(new_customers.values()),
    )

    p_purchase_given_returning = conditional_from_counts(
        returning_customers["purchase"],
        sum(returning_customers.values()),
    )

    print(f"P(purchase | new customer) = {p_purchase_given_new:.2%}")
    print(
        "P(purchase | returning customer) = "
        f"{p_purchase_given_returning:.2%}"
    )

    print(
        """
Contingency tables organize observed counts by categories.

They can answer questions such as:
    P(purchase | customer segment)
    P(default | risk category)
    P(churn | subscription plan)

The key is to use the correct denominator.

For:

    P(purchase | returning)

the denominator is the number of returning customers, not the total number
of customers.
"""
    )


# ============================================================================
# 33. TOTAL PROBABILITY
# ============================================================================

def law_of_total_probability(
    conditional_probabilities: Sequence[float],
    group_probabilities: Sequence[float],
) -> float:
    """
    Calculate P(A) using a partition:

        P(A) = sum P(A|B_i)P(B_i)
    """
    if len(conditional_probabilities) != len(group_probabilities):
        raise ValueError("Sequences must have equal lengths.")

    if not conditional_probabilities:
        raise ValueError("At least one group is required.")

    for probability in conditional_probabilities:
        validate_probability(probability)

    for probability in group_probabilities:
        validate_probability(probability)

    if not math.isclose(sum(group_probabilities), 1.0, abs_tol=1e-12):
        raise ValueError("Group probabilities must sum to 1.")

    return sum(
        conditional * group
        for conditional, group in zip(
            conditional_probabilities,
            group_probabilities,
        )
    )


def demonstrate_total_probability() -> None:
    print("\n" + "=" * 78)
    print("32. LAW OF TOTAL PROBABILITY")
    print("=" * 78)

    # Customer segments.
    segment_probabilities = [0.50, 0.30, 0.20]
    conversion_given_segment = [0.04, 0.07, 0.12]

    overall_conversion = law_of_total_probability(
        conversion_given_segment,
        segment_probabilities,
    )

    print(f"Overall conversion probability = {overall_conversion:.2%}")

    print(
        """
If B1, B2, ..., Bn form a partition of the sample space:

    P(A) = sum P(A | B_i)P(B_i)

This is valuable in business when an overall probability is driven by
different customer, product, geographic, or risk segments.

Changing the composition of the population can change the overall rate
even when each segment's conditional rate stays constant.
"""
    )


# ============================================================================
# 34. ODDS AND PROBABILITY
# ============================================================================

def probability_to_odds(probability: float) -> float:
    """Convert probability to odds in favor."""
    validate_probability(probability)

    if probability == 1:
        return math.inf

    if probability == 0:
        return 0.0

    return probability / (1 - probability)


def odds_to_probability(odds: float) -> float:
    """Convert odds in favor to probability."""
    validate_nonnegative(odds, "odds")
    return odds / (1 + odds)


def demonstrate_odds() -> None:
    print("\n" + "=" * 78)
    print("33. PROBABILITY AND ODDS")
    print("=" * 78)

    probability = 0.20
    odds = probability_to_odds(probability)
    recovered_probability = odds_to_probability(odds)

    print(f"Probability = {probability:.2%}")
    print(f"Odds in favor = {odds:.4f}")
    print(f"Probability recovered from odds = {recovered_probability:.2%}")

    print(
        """
Probability and odds are related but are not the same.

Odds in favor:

    odds = p / (1-p)

Probability from odds:

    p = odds / (1+odds)

Odds are common in:
    - logistic regression
    - betting
    - credit scoring
    - risk modeling

A probability of 20% corresponds to odds of:

    0.20 / 0.80 = 0.25

or 1 to 4 in favor.
"""
    )


# ============================================================================
# 35. SIMULATING A BINOMIAL BUSINESS PROCESS
# ============================================================================

def simulate_binomial(
    n: int,
    p: float,
    trials: int,
    seed: int | None = None,
) -> list[int]:
    """Simulate repeated binomial experiments."""
    if n < 0 or trials <= 0:
        raise ValueError("n must be non-negative and trials must be positive.")

    validate_probability(p)

    rng = random.Random(seed)

    return [
        sum(rng.random() < p for _ in range(n))
        for _ in range(trials)
    ]


def demonstrate_conversion_simulation() -> None:
    print("\n" + "=" * 78)
    print("34. SIMULATED CUSTOMER CONVERSIONS")
    print("=" * 78)

    simulated_conversions = simulate_binomial(
        n=100,
        p=0.05,
        trials=10_000,
        seed=7,
    )

    observed_mean = statistics.fmean(simulated_conversions)
    observed_sd = statistics.pstdev(simulated_conversions)

    print(f"Average simulated conversions = {observed_mean:.3f}")
    print(f"SD of simulated conversions    = {observed_sd:.3f}")
    print(
        "Theoretical mean              = "
        f"{100 * 0.05:.3f}"
    )
    print(
        "Theoretical SD                = "
        f"{math.sqrt(100 * 0.05 * 0.95):.3f}"
    )

    print(
        """
Simulation provides a way to check whether theoretical calculations match
the behavior of repeated random experiments.

For X ~ Binomial(n,p):

    E[X] = np

    SD(X) = sqrt(np(1-p))

The simulated results should approach the theoretical quantities as the
number of simulation trials increases.
"""
    )


# ============================================================================
# 36. PROBABILITY OF AT LEAST ONE SUCCESS
# ============================================================================

def probability_at_least_one_success(
    n: int,
    p: float,
) -> float:
    """
    Calculate P(at least one success) among n independent trials.

        1 - (1-p)^n
    """
    if n < 0:
        raise ValueError("n must be non-negative.")

    validate_probability(p)

    return 1 - (1 - p) ** n


def demonstrate_at_least_one_success() -> None:
    print("\n" + "=" * 78)
    print("35. PROBABILITY OF AT LEAST ONE SUCCESS")
    print("=" * 78)

    probability = probability_at_least_one_success(
        n=12,
        p=0.08,
    )

    print(f"P(at least one conversion in 12 prospects) = {probability:.2%}")

    print(
        """
For independent trials with success probability p:

    P(no success) = (1-p)^n

Therefore:

    P(at least one success) = 1 - (1-p)^n

This is often more efficient than adding the probabilities of exactly
1, exactly 2, exactly 3, and so on.

Business uses include:
    - probability of at least one sale
    - probability of at least one defect
    - probability of at least one claim
    - probability of at least one failure
"""
    )


# ============================================================================
# 37. CONDITIONAL RISK WITH SEGMENTATION
# ============================================================================

@dataclass
class RiskSegment:
    """Represent a business risk segment."""

    name: str
    population_share: float
    event_probability: float

    def validate(self) -> None:
        validate_probability(self.population_share, "population_share")
        validate_probability(self.event_probability, "event_probability")


def segment_weighted_risk(segments: Sequence[RiskSegment]) -> float:
    """Calculate population-weighted event probability."""
    if not segments:
        raise ValueError("At least one segment is required.")

    for segment in segments:
        segment.validate()

    total_share = sum(segment.population_share for segment in segments)

    if not math.isclose(total_share, 1.0, abs_tol=1e-12):
        raise ValueError("Population shares must sum to 1.")

    return sum(
        segment.population_share * segment.event_probability
        for segment in segments
    )


def demonstrate_segmented_risk() -> None:
    print("\n" + "=" * 78)
    print("36. SEGMENTED BUSINESS RISK")
    print("=" * 78)

    segments = [
        RiskSegment("Low risk", 0.50, 0.01),
        RiskSegment("Medium risk", 0.30, 0.05),
        RiskSegment("High risk", 0.20, 0.15),
    ]

    overall_risk = segment_weighted_risk(segments)

    print(f"Population-weighted event risk = {overall_risk:.2%}")

    for segment in segments:
        print(
            f"{segment.name:>12}: "
            f"share={segment.population_share:.0%}, "
            f"risk={segment.event_probability:.0%}"
        )

    print(
        """
Segment-level probabilities can be combined using weighted averages.

This is useful because a business often contains heterogeneous groups.

An overall risk rate can change because:
    1. risk within segments changes, or
    2. the population mix changes.

This distinction is important when interpreting KPI changes.
"""
    )


# ============================================================================
# 38. SAMPLING ERROR AND STANDARD ERROR
# ============================================================================

def proportion_standard_error(
    probability: float,
    sample_size: int,
) -> float:
    """Calculate the standard error of a sample proportion."""
    validate_probability(probability)

    if sample_size <= 0:
        raise ValueError("sample_size must be positive.")

    return math.sqrt(
        probability * (1 - probability) / sample_size
    )


def approximate_margin_of_error(
    probability: float,
    sample_size: int,
    z_value: float = 1.96,
) -> float:
    """
    Approximate margin of error for a proportion.

    z=1.96 is commonly associated with an approximate 95% normal interval.
    """
    if z_value <= 0:
        raise ValueError("z_value must be positive.")

    return z_value * proportion_standard_error(
        probability,
        sample_size,
    )


def demonstrate_sampling_error() -> None:
    print("\n" + "=" * 78)
    print("37. SAMPLING ERROR")
    print("=" * 78)

    estimated_conversion = 0.10

    for sample_size in (100, 1_000, 10_000):
        se = proportion_standard_error(
            estimated_conversion,
            sample_size,
        )
        margin = approximate_margin_of_error(
            estimated_conversion,
            sample_size,
        )

        print(
            f"n={sample_size:>5}: "
            f"SE={se:.4f}, "
            f"approx. 95% margin={margin:.4f}"
        )

    print(
        """
Larger samples generally reduce sampling uncertainty.

For a proportion p:

    SE(p_hat) = sqrt[p(1-p)/n]

An approximate normal margin of error is:

    z * SE

For approximately 95% coverage, z is about 1.96 under the standard normal
approximation.

Sampling error is different from:
    - measurement error
    - selection bias
    - nonresponse bias
    - model error
    - data leakage

Increasing sample size does not automatically eliminate systematic bias.
"""
    )


# ============================================================================
# 39. RISK METRICS FROM A DISCRETE OUTCOME DISTRIBUTION
# ============================================================================

def weighted_quantile(
    values: Sequence[float],
    probabilities: Sequence[float],
    quantile: float,
) -> float:
    """
    Find the smallest value whose cumulative probability reaches quantile.
    """
    if len(values) != len(probabilities):
        raise ValueError("values and probabilities must have equal lengths.")

    validate_probability(quantile, "quantile")

    pairs = sorted(zip(values, probabilities), key=lambda item: item[0])

    total_probability = sum(probability for _, probability in pairs)

    if not math.isclose(total_probability, 1.0, abs_tol=1e-12):
        raise ValueError("Probabilities must sum to 1.")

    cumulative = 0.0

    for value, probability in pairs:
        cumulative += probability
        if cumulative >= quantile:
            return value

    return pairs[-1][0]


def demonstrate_business_risk_distribution() -> None:
    print("\n" + "=" * 78)
    print("38. BUSINESS RISK DISTRIBUTION AND QUANTILES")
    print("=" * 78)

    profit_outcomes = [-100_000, -20_000, 30_000, 80_000, 200_000]
    probabilities = [0.05, 0.10, 0.35, 0.35, 0.15]

    ev = expected_value(profit_outcomes, probabilities)
    p_loss = sum(
        probability
        for value, probability in zip(profit_outcomes, probabilities)
        if value < 0
    )

    median = weighted_quantile(
        profit_outcomes,
        probabilities,
        0.50,
    )

    percentile_5 = weighted_quantile(
        profit_outcomes,
        probabilities,
        0.05,
    )

    print(f"Expected profit = ${ev:,.2f}")
    print(f"P(loss) = {p_loss:.2%}")
    print(f"Median outcome = ${median:,.2f}")
    print(f"5th percentile outcome = ${percentile_5:,.2f}")

    print(
        """
A complete probability distribution contains more information than a
single expected value.

Useful risk measures include:
    - probability of loss
    - quantiles
    - downside scenarios
    - variance
    - standard deviation
    - tail probabilities

A decision-maker should inspect the distribution of outcomes rather than
relying solely on the expected value.
"""
    )


# ============================================================================
# 40. EDGE CASES AND NUMERICAL ISSUES
# ============================================================================

def demonstrate_edge_cases() -> None:
    print("\n" + "=" * 78)
    print("39. EDGE CASES AND EXCEPTIONS")
    print("=" * 78)

    cases = [
        ("Probability 0", lambda: complement_probability(0.0)),
        ("Probability 1", lambda: complement_probability(1.0)),
        ("Zero Poisson rate", lambda: poisson_pmf(0, 0.0)),
        ("Impossible binomial count", lambda: binomial_pmf(10, 20, 0.5)),
        ("Normal CDF at mean", lambda: normal_cdf(0.0)),
    ]

    for name, operation in cases:
        try:
            print(f"{name}: {operation()}")
        except Exception as error:
            print(f"{name}: ERROR -> {error}")

    invalid_operations = [
        (
            "Probability outside range",
            lambda: validate_probability(1.5),
        ),
        (
            "Negative factorial input",
            lambda: factorial(-1),
        ),
        (
            "Zero denominator",
            lambda: conditional_probability(0.0, 0.0),
        ),
        (
            "Invalid distribution",
            lambda: DiscreteDistribution({1: 0.6, 2: 0.6}).validate(),
        ),
    ]

    for name, operation in invalid_operations:
        try:
            operation()
        except (ValueError, TypeError, ZeroDivisionError) as error:
            print(f"{name}: correctly rejected -> {error}")

    print(
        """
Important edge cases include:

    Probability:
        Must remain within [0,1].

    Conditional probability:
        Undefined when the conditioning event has probability zero.

    Normal distribution:
        Standard deviation must be positive.

    Discrete distributions:
        Probabilities must sum to 1.

    Binomial:
        k outside [0,n] has probability 0.

    Poisson:
        lambda must be non-negative.

Numerical considerations:
    Floating-point calculations can produce tiny rounding differences.
    Use math.isclose when comparing calculated probabilities with 1.0 or
    other theoretically exact values.
"""
    )


# ============================================================================
# 41. COMMON PROBABILITY MISTAKES
# ============================================================================

def demonstrate_common_mistakes() -> None:
    print("\n" + "=" * 78)
    print("40. COMMON PROBABILITY MISTAKES")
    print("=" * 78)

    mistakes = {
        "Confusing P(A|B) with P(B|A)": (
            "Conditional probabilities generally are not interchangeable."
        ),
        "Ignoring base rates": (
            "Rare events can make positive test results less predictive."
        ),
        "Assuming independence": (
            "Business observations may share customers, markets, suppliers, "
            "or time periods."
        ),
        "Confusing mutually exclusive with independent": (
            "Mutually exclusive positive-probability events are not independent."
        ),
        "Treating expected value as guaranteed": (
            "Expected value describes an average, not a certain outcome."
        ),
        "Assuming correlation proves causation": (
            "Association alone does not establish a causal relationship."
        ),
        "Using a normal distribution automatically": (
            "Real data may be skewed, bounded, discrete, or heavy-tailed."
        ),
        "Increasing sample size to fix bias": (
            "Larger biased samples can produce more precise biased estimates."
        ),
        "Overlooking selection effects": (
            "Observed data may not represent the target population."
        ),
    }

    for mistake, explanation in mistakes.items():
        print(f"\n{mistake}")
        print(f"    {explanation}")

    print(
        """
Probability calculations are only as good as the event definitions,
data-generating assumptions, and measurement process behind them.
"""
    )


# ============================================================================
# 42. INDEPENDENCE CHECK FROM OBSERVED DATA
# ============================================================================

def empirical_probability(
    successes: int,
    observations: int,
) -> float:
    """Calculate empirical probability from counts."""
    if observations <= 0:
        raise ValueError("observations must be positive.")

    if successes < 0 or successes > observations:
        raise ValueError("successes must be between 0 and observations.")

    return successes / observations


def demonstrate_empirical_independence_check() -> None:
    print("\n" + "=" * 78)
    print("41. CHECKING INDEPENDENCE USING OBSERVED RATES")
    print("=" * 78)

    total = 10_000
    campaign_exposed = 4_000
    campaign_converted = 360
    not_exposed = 6_000
    not_exposed_converted = 360

    p_conversion_given_exposed = empirical_probability(
        campaign_converted,
        campaign_exposed,
    )

    p_conversion_given_not_exposed = empirical_probability(
        not_exposed_converted,
        not_exposed,
    )

    print(
        "P(conversion | exposed)     = "
        f"{p_conversion_given_exposed:.2%}"
    )
    print(
        "P(conversion | not exposed) = "
        f"{p_conversion_given_not_exposed:.2%}"
    )

    print(
        """
If:

    P(A | B) approximately equals P(A | not B)

the data may be consistent with little association between A and B.

This is only an exploratory comparison, not a complete statistical test
of independence or causality.

Randomized experiments are stronger for causal conclusions because random
assignment is designed to balance confounding factors in expectation.
"""
    )


# ============================================================================
# 43. BUSINESS DECISION TREE USING EXPECTED VALUE
# ============================================================================

@dataclass
class DecisionOption:
    """Represent a decision option with uncertain monetary outcomes."""

    name: str
    outcomes: Sequence[float]
    probabilities: Sequence[float]

    def expected_value(self) -> float:
        return expected_value(self.outcomes, self.probabilities)


def demonstrate_decision_analysis() -> None:
    print("\n" + "=" * 78)
    print("42. DECISION ANALYSIS UNDER UNCERTAINTY")
    print("=" * 78)

    options = [
        DecisionOption(
            "Conservative launch",
            [10_000, 20_000, 30_000],
            [0.20, 0.50, 0.30],
        ),
        DecisionOption(
            "Aggressive launch",
            [-20_000, 40_000, 100_000],
            [0.30, 0.40, 0.30],
        ),
    ]

    for option in options:
        print(
            f"{option.name}: expected value = "
            f"${option.expected_value():,.2f}"
        )

    print(
        """
Decision analysis compares uncertain outcomes using probability-weighted
metrics.

A higher expected value is not automatically the preferred decision.

For example, an aggressive strategy can have:
    - higher expected value
    - larger probability of a major loss
    - greater variance
    - higher capital requirements

Expected value should therefore be combined with risk and strategic
constraints.
"""
    )


# ============================================================================
# 44. CONDITIONAL EXPECTATION
# ============================================================================

def conditional_expected_value(
    values: Sequence[float],
    probabilities: Sequence[float],
) -> float:
    """
    Calculate an expected value from a conditional distribution.

    The function emphasizes that the probabilities must describe the
    conditional population being analyzed.
    """
    return expected_value(values, probabilities)


def demonstrate_conditional_expectation() -> None:
    print("\n" + "=" * 78)
    print("43. CONDITIONAL EXPECTATION")
    print("=" * 78)

    revenue_new_customers = [20, 50, 100]
    probabilities_new_customers = [0.50, 0.35, 0.15]

    revenue_returning_customers = [30, 75, 150]
    probabilities_returning_customers = [0.30, 0.45, 0.25]

    expected_new = conditional_expected_value(
        revenue_new_customers,
        probabilities_new_customers,
    )

    expected_returning = conditional_expected_value(
        revenue_returning_customers,
        probabilities_returning_customers,
    )

    print(f"E(revenue | new customer) = ${expected_new:.2f}")
    print(f"E(revenue | returning customer) = ${expected_returning:.2f}")

    print(
        """
Conditional expectation asks for an expected value within a specified
condition or subgroup.

Examples:

    E(revenue | customer segment)

    E(loss | default)

    E(demand | promotion)

This is important because averages can differ substantially across
segments.
"""
    )


# ============================================================================
# 45. PERFORMANCE CONSIDERATIONS
# ============================================================================

def demonstrate_performance_considerations() -> None:
    print("\n" + "=" * 78)
    print("44. PERFORMANCE CONSIDERATIONS")
    print("=" * 78)

    print(
        """
Probability calculations vary greatly in computational cost.

Simple arithmetic:
    O(1)

Binomial probability for one k:
    O(1) when combinations are computed efficiently.

Naive binomial cumulative probability:
    O(n) because probabilities for multiple k values are summed.

Monte Carlo simulation:
    O(N) for N simulated trials.

Large simulations require attention to:
    - number of trials
    - random-number generation
    - memory usage
    - numerical stability
    - reproducibility
    - parallel execution

For production analytics, specialized numerical libraries can provide
vectorization and optimized probability distributions. This educational
script intentionally uses the standard library to keep the implementation
transparent.

For extreme parameter values, directly computing factorials or powers may
overflow or lose numerical precision. Logarithmic probability calculations
or specialized statistical functions are preferable in such cases.
"""
    )


# ============================================================================
# 46. SECURITY AND GOVERNANCE CONSIDERATIONS
# ============================================================================

def demonstrate_security_and_governance() -> None:
    print("\n" + "=" * 78)
    print("45. SECURITY, DATA, AND MODEL GOVERNANCE")
    print("=" * 78)

    print(
        """
Probability code used in business systems can affect financial and
operational decisions.

Important considerations:

Data integrity:
    Incorrect counts, duplicate records, missing observations, or corrupted
    inputs can produce incorrect probabilities.

Privacy:
    Customer-level data used to estimate probabilities may contain
    sensitive information and should be handled according to applicable
    privacy requirements.

Model transparency:
    Business users should understand major assumptions behind probability
    estimates.

Reproducibility:
    Use controlled random seeds for tests and simulations when reproducible
    results are required.

Auditability:
    Store model versions, input assumptions, data windows, and calculation
    logic for important decisions.

Bias:
    Historical probabilities can encode historical bias. An empirical
    probability is not automatically an objective or fair probability.

Security:
    Validate external inputs and avoid executing arbitrary code supplied
    through user-controlled data.

Model risk:
    A mathematically correct implementation can still produce poor decisions
    when the probability model is inappropriate.
"""
    )


# ============================================================================
# 47. PRODUCTION DESIGN PRINCIPLES
# ============================================================================

def demonstrate_production_design() -> None:
    print("\n" + "=" * 78)
    print("46. PRODUCTION DESIGN PRINCIPLES")
    print("=" * 78)

    print(
        """
A production probability component should separate:

    1. Input validation
    2. Data preparation
    3. Probability estimation
    4. Mathematical calculation
    5. Simulation
    6. Reporting
    7. Monitoring

Recommended practices:

    - Validate probability ranges.
    - Validate sample sizes and counts.
    - Handle zero denominators explicitly.
    - Document assumptions.
    - Use deterministic seeds for tests.
    - Test boundary cases.
    - Monitor changes in input distributions.
    - Compare model predictions with realized outcomes.
    - Track calibration where probabilities are used for prediction.
    - Avoid silently converting invalid data into plausible numbers.

Probability systems should be treated as decision infrastructure when they
drive pricing, credit, fraud, inventory, staffing, or financial decisions.
"""
    )


# ============================================================================
# 48. PROBABILITY CALIBRATION
# ============================================================================

def demonstrate_calibration() -> None:
    print("\n" + "=" * 78)
    print("47. PROBABILITY CALIBRATION")
    print("=" * 78)

    predicted_probabilities = [
        0.10, 0.20, 0.30, 0.40, 0.50,
        0.60, 0.70, 0.80, 0.90, 0.90,
    ]

    actual_outcomes = [
        0, 0, 1, 0, 1,
        1, 1, 1, 0, 1,
    ]

    brier_score = statistics.fmean(
        (prediction - outcome) ** 2
        for prediction, outcome
        in zip(predicted_probabilities, actual_outcomes)
    )

    print(f"Brier score = {brier_score:.4f}")

    print(
        """
A probability forecast should be evaluated as a probability, not only as
a binary classification.

Calibration asks whether events assigned approximately p probability occur
approximately p proportion of the time within comparable groups.

Example:
    Among transactions assigned a 20% fraud probability, approximately
    20% should be fraudulent over a sufficiently large and representative
    evaluation set if the probabilities are well calibrated.

The Brier score for binary outcomes is:

    mean((predicted probability - actual outcome)^2)

Lower is better.

Calibration matters when probability values themselves drive decisions,
such as:
    - credit limits
    - fraud investigation thresholds
    - insurance pricing
    - resource allocation
"""
    )


# ============================================================================
# 49. BUSINESS SCENARIO: COMBINING PROBABILITY COMPONENTS
# ============================================================================

def demonstrate_integrated_business_case() -> None:
    print("\n" + "=" * 78)
    print("48. INTEGRATED BUSINESS CASE")
    print("=" * 78)

    visitors = 100_000

    # Segment mix.
    segment_share = {
        "new": 0.65,
        "returning": 0.35,
    }

    conversion_rate = {
        "new": 0.03,
        "returning": 0.08,
    }

    average_order_value = {
        "new": 55,
        "returning": 80,
    }

    overall_conversion = sum(
        segment_share[segment] * conversion_rate[segment]
        for segment in segment_share
    )

    expected_orders = visitors * overall_conversion

    expected_order_value = sum(
        segment_share[segment]
        * conversion_rate[segment]
        / overall_conversion
        * average_order_value[segment]
        for segment in segment_share
    )

    expected_revenue = expected_orders * expected_order_value

    print(f"Overall conversion probability = {overall_conversion:.2%}")
    print(f"Expected orders = {expected_orders:,.0f}")
    print(f"Expected order value = ${expected_order_value:.2f}")
    print(f"Expected revenue = ${expected_revenue:,.2f}")

    print(
        """
This integrated example combines:

    - segmentation
    - conditional conversion probabilities
    - weighted averages
    - expected order volume
    - expected revenue

The important principle is to define the probability model around the
business process rather than applying one overall average indiscriminately.

Segment composition matters because segments have different probabilities
and different economic values.
"""
    )


# ============================================================================
# 50. PRACTICAL REFERENCE TABLE
# ============================================================================

def print_reference_table() -> None:
    print("\n" + "=" * 78)
    print("49. PROBABILITY REFERENCE")
    print("=" * 78)

    reference = [
        ("Complement", "P(not A)", "1 - P(A)"),
        ("Union", "P(A or B)", "P(A)+P(B)-P(A and B)"),
        ("Conditional", "P(A|B)", "P(A and B)/P(B)"),
        ("Independent", "P(A and B)", "P(A)P(B)"),
        ("Bayes", "P(A|B)", "P(B|A)P(A)/P(B)"),
        ("Expected value", "E[X]", "sum(xP(X=x))"),
        ("Variance", "Var(X)", "E[(X-mu)^2]"),
        ("Standard deviation", "SD(X)", "sqrt(Var(X))"),
        ("Binomial", "P(X=k)", "C(n,k)p^k(1-p)^(n-k)"),
        ("Poisson", "P(X=k)", "e^(-lambda)lambda^k/k!"),
        ("Normal Z-score", "Z", "(X-mu)/sigma"),
    ]

    for name, notation, formula in reference:
        print(f"{name:<20} | {notation:<18} | {formula}")

    print(
        """
Model selection should follow the data-generating process:

    Binary single trial      -> Bernoulli
    Fixed independent trials -> Binomial
    Trials until success     -> Geometric
    Count in interval        -> Poisson
    Continuous bell-shaped   -> Normal, when assumptions are appropriate
    Complex uncertainty      -> Simulation may be useful
"""
    )


# ============================================================================
# 51. MINI TEST SUITE
# ============================================================================

def run_tests() -> None:
    print("\n" + "=" * 78)
    print("50. BASIC SELF-TESTS")
    print("=" * 78)

    assert math.isclose(
        complement_probability(0.25),
        0.75,
    )

    assert math.isclose(
        conditional_probability(0.20, 0.40),
        0.50,
    )

    assert math.isclose(
        binomial_pmf(1, 1, 0.70),
        0.70,
    )

    assert math.isclose(
        poisson_pmf(0, 0),
        1.0,
    )

    assert math.isclose(
        normal_cdf(0),
        0.5,
        abs_tol=1e-12,
    )

    assert math.isclose(
        expected_value([10, 20], [0.5, 0.5]),
        15.0,
    )

    assert math.isclose(
        probability_at_least_one_success(1, 0.3),
        0.3,
    )

    assert math.isclose(
        odds_to_probability(
            probability_to_odds(0.2)
        ),
        0.2,
    )

    print("All self-tests passed.")


# ============================================================================
# 52. MAIN PROGRAM
# ============================================================================

def main() -> None:
    """
    Run the complete educational demonstration.
    """
    print("=" * 78)
    print("PROBABILITY BASICS AND BUSINESS APPLICATIONS")
    print("=" * 78)
    print(
        "A comprehensive standard-library-only study script."
    )

    explain_probability_basics()
    demonstrate_sample_space_and_events()
    demonstrate_probability_interpretations()
    demonstrate_counting()
    demonstrate_basic_probability_rules()
    demonstrate_conditional_probability()
    demonstrate_independence_and_exclusivity()
    demonstrate_multiplication_rule()
    demonstrate_bayes_theorem()
    demonstrate_random_variables()
    demonstrate_bernoulli_distribution()
    demonstrate_binomial_distribution()
    demonstrate_geometric_distribution()
    demonstrate_poisson_distribution()
    demonstrate_normal_distribution()
    demonstrate_expected_value_business_case()
    demonstrate_variance_and_correlation()
    demonstrate_law_of_large_numbers()
    demonstrate_central_limit_theorem()
    demonstrate_monte_carlo()
    demonstrate_conversion_funnel()
    demonstrate_expected_revenue()
    demonstrate_quality_control()
    demonstrate_inventory_risk()
    demonstrate_fraud_detection()
    demonstrate_credit_risk()
    demonstrate_insurance()
    demonstrate_ab_testing()
    demonstrate_portfolio_probability()
    demonstrate_demand_simulation()
    demonstrate_contingency_table()
    demonstrate_total_probability()
    demonstrate_odds()
    demonstrate_conversion_simulation()
    demonstrate_at_least_one_success()
    demonstrate_segmented_risk()
    demonstrate_sampling_error()
    demonstrate_business_risk_distribution()
    demonstrate_edge_cases()
    demonstrate_common_mistakes()
    demonstrate_empirical_independence_check()
    demonstrate_decision_analysis()
    demonstrate_conditional_expectation()
    demonstrate_performance_considerations()
    demonstrate_security_and_governance()
    demonstrate_production_design()
    demonstrate_calibration()
    demonstrate_integrated_business_case()
    print_reference_table()
    run_tests()

    print("\n" + "=" * 78)
    print("END OF PROBABILITY STUDY SCRIPT")
    print("=" * 78)


if __name__ == "__main__":
    main()
