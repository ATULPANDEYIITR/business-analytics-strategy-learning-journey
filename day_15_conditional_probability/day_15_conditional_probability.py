"""
Conditional Probability for Business Decisions Under Uncertainty
=================================================================

A self-contained study program covering conditional probability from
beginner to advanced level, with business-oriented examples.

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, sqrt, exp, pi
from random import Random
from typing import Callable, Dict, Iterable, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# 1. FOUNDATIONS
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def subsection(title: str) -> None:
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


def probability(event_count: int, total_count: int) -> float:
    """Calculate empirical probability with validation."""
    if total_count <= 0:
        raise ValueError("The total number of observations must be positive.")
    if event_count < 0 or event_count > total_count:
        raise ValueError("Event count must be between 0 and total count.")
    return event_count / total_count


def show_probability(name: str, value: float) -> None:
    print(f"{name}: {value:.4f} ({value:.2%})")


section("1. Probability fundamentals")

print("Probability measures uncertainty on a scale from 0 to 1.")
print("0 means impossible, 1 means certain, and intermediate values represent")
print("degrees of uncertainty.")

customers = 1000
purchased = 180
p_purchase = probability(purchased, customers)
show_probability("Empirical probability of purchase", p_purchase)

print("\nBusiness interpretation:")
print("If 1,000 comparable visitors produced 180 purchases, the observed")
print("purchase rate is 18%.")


# ---------------------------------------------------------------------------
# 2. CONDITIONAL PROBABILITY
# ---------------------------------------------------------------------------

section("2. Conditional probability")

print("Conditional probability answers questions of the form:")
print("P(A | B) = probability of A given that B has occurred.")
print()
print("The fundamental rule is:")
print("P(A | B) = P(A and B) / P(B), provided P(B) > 0.")

total_customers = 10000
mobile_customers = 6000
mobile_and_purchase = 1500

p_mobile = mobile_customers / total_customers
p_mobile_purchase = mobile_and_purchase / total_customers
p_purchase_given_mobile = p_mobile_purchase / p_mobile

show_probability("P(Mobile)", p_mobile)
show_probability("P(Mobile and Purchase)", p_mobile_purchase)
show_probability("P(Purchase | Mobile)", p_purchase_given_mobile)

print(
    "\nThe distinction matters: P(Purchase | Mobile) is not the same "
    "question as P(Mobile | Purchase)."
)


# ---------------------------------------------------------------------------
# 3. JOINT, MARGINAL, AND CONDITIONAL PROBABILITIES
# ---------------------------------------------------------------------------

section("3. Joint, marginal, and conditional probabilities")

# Rows are customer device categories; columns are outcomes.
customer_table = {
    "Mobile": {"Purchased": 1500, "Did not purchase": 4500},
    "Desktop": {"Purchased": 1000, "Did not purchase": 3000},
}

print("Customer table:")
for device, outcomes in customer_table.items():
    print(f"{device:10s}: {outcomes}")

total = sum(sum(row.values()) for row in customer_table.values())
purchased_total = sum(row["Purchased"] for row in customer_table.values())
mobile_total = sum(customer_table["Mobile"].values())

p_purchase = purchased_total / total
p_mobile = mobile_total / total
p_purchase_and_mobile = customer_table["Mobile"]["Purchased"] / total
p_purchase_given_mobile = p_purchase_and_mobile / p_mobile

show_probability("Marginal P(Purchase)", p_purchase)
show_probability("Marginal P(Mobile)", p_mobile)
show_probability("Joint P(Purchase and Mobile)", p_purchase_and_mobile)
show_probability("Conditional P(Purchase | Mobile)", p_purchase_given_mobile)


# ---------------------------------------------------------------------------
# 4. CONDITIONAL PROBABILITY FROM COUNTS
# ---------------------------------------------------------------------------

section("4. A reusable conditional probability function")


def conditional_probability(
    joint_count: int,
    conditioning_count: int,
) -> float:
    """
    Calculate P(A | B) from counts.

    joint_count represents observations satisfying both A and B.
    conditioning_count represents observations satisfying B.
    """
    if conditioning_count <= 0:
        raise ValueError("Conditioning event must have a positive count.")
    if joint_count < 0 or joint_count > conditioning_count:
        raise ValueError("Joint count must lie between 0 and conditioning count.")
    return joint_count / conditioning_count


p = conditional_probability(320, 800)
show_probability("P(Positive response | Targeted)", p)


# ---------------------------------------------------------------------------
# 5. COMPLEMENT RULE
# ---------------------------------------------------------------------------

section("5. Complement rule")

print("For an event A:")
print("P(not A) = 1 - P(A)")

p_churn = 0.08
p_retention = 1 - p_churn

show_probability("P(Churn)", p_churn)
show_probability("P(Retain)", p_retention)


# ---------------------------------------------------------------------------
# 6. ADDITION RULE
# ---------------------------------------------------------------------------

section("6. Addition rule")

print("For two events A and B:")
print("P(A or B) = P(A) + P(B) - P(A and B)")

p_discount = 0.30
p_email = 0.25
p_both = 0.12

p_discount_or_email = p_discount + p_email - p_both

show_probability("P(Discount or Email)", p_discount_or_email)


# ---------------------------------------------------------------------------
# 7. MULTIPLICATION RULE
# ---------------------------------------------------------------------------

section("7. Multiplication rule")

print("P(A and B) = P(A | B) P(B)")
print("This is especially useful when a business process unfolds in stages.")

p_lead = 0.40
p_demo_given_lead = 0.35

p_lead_and_demo = p_demo_given_lead * p_lead

show_probability("P(Lead)", p_lead)
show_probability("P(Demo | Lead)", p_demo_given_lead)
show_probability("P(Lead and Demo)", p_lead_and_demo)


# ---------------------------------------------------------------------------
# 8. INDEPENDENCE
# ---------------------------------------------------------------------------

section("8. Independence")

print("Events A and B are independent when:")
print("P(A | B) = P(A)")
print("Equivalently:")
print("P(A and B) = P(A)P(B)")

p_ad = 0.20
p_weekend = 0.30
p_ad_and_weekend = 0.06

independent_expected = p_ad * p_weekend
print(f"Observed joint probability: {p_ad_and_weekend:.4f}")
print(f"Expected if independent:    {independent_expected:.4f}")
print(f"Independent: {abs(p_ad_and_weekend - independent_expected) < 1e-12}")


# ---------------------------------------------------------------------------
# 9. BAYES' THEOREM
# ---------------------------------------------------------------------------

section("9. Bayes' theorem")

print("Bayes' theorem reverses conditional probability:")
print()
print("P(A | B) = P(B | A) P(A) / P(B)")
print()
print("The denominator can be expanded using the law of total probability.")

# Fraud detection example.
p_fraud = 0.01
p_flag_given_fraud = 0.95
p_flag_given_legitimate = 0.05

p_legitimate = 1 - p_fraud
p_flag = (
    p_flag_given_fraud * p_fraud
    + p_flag_given_legitimate * p_legitimate
)
p_fraud_given_flag = p_flag_given_fraud * p_fraud / p_flag

show_probability("Prior P(Fraud)", p_fraud)
show_probability("P(Flag | Fraud)", p_flag_given_fraud)
show_probability("P(Flag | Legitimate)", p_flag_given_legitimate)
show_probability("P(Flag)", p_flag)
show_probability("Posterior P(Fraud | Flag)", p_fraud_given_flag)

print(
    "\nEven a highly sensitive fraud system can produce many false positives "
    "when fraud is rare. The base rate is critical."
)


# ---------------------------------------------------------------------------
# 10. LAW OF TOTAL PROBABILITY
# ---------------------------------------------------------------------------

section("10. Law of total probability")

regions = {
    "North": {"share": 0.25, "conversion": 0.12},
    "South": {"share": 0.35, "conversion": 0.08},
    "East": {"share": 0.20, "conversion": 0.15},
    "West": {"share": 0.20, "conversion": 0.10},
}

overall_conversion = sum(
    data["share"] * data["conversion"]
    for data in regions.values()
)

show_probability("Overall conversion", overall_conversion)

print("This is a weighted average of conditional conversion rates.")


# ---------------------------------------------------------------------------
# 11. EXPECTED VALUE
# ---------------------------------------------------------------------------

section("11. Expected value for business decisions")

print("Expected value converts uncertain outcomes into a probability-weighted")
print("average.")

scenarios = [
    ("High demand", 0.25, 200000),
    ("Medium demand", 0.50, 80000),
    ("Low demand", 0.25, -60000),
]

expected_profit = sum(probability * profit for _, probability, profit in scenarios)

for name, p_scenario, profit in scenarios:
    print(f"{name:15s}: probability={p_scenario:.2%}, payoff=₹{profit:,.0f}")

print(f"Expected profit: ₹{expected_profit:,.0f}")


# ---------------------------------------------------------------------------
# 12. EXPECTED VALUE OF PERFECT INFORMATION
# ---------------------------------------------------------------------------

section("12. Expected value of perfect information")

print(
    "Suppose a company must choose between two strategies before demand "
    "is known."
)

decision_payoffs = {
    "Expand": {"High": 200000, "Low": -100000},
    "Do not expand": {"High": 90000, "Low": 30000},
}
demand_probability = {"High": 0.40, "Low": 0.60}

expected_without_information = {
    decision: sum(
        demand_probability[demand] * payoff
        for demand, payoff in outcomes.items()
    )
    for decision, outcomes in decision_payoffs.items()
}

for decision, value in expected_without_information.items():
    print(f"{decision}: expected payoff = ₹{value:,.0f}")

best_without_information = max(expected_without_information.values())

expected_with_perfect_information = sum(
    demand_probability[demand]
    * max(payoffs[demand] for payoffs in decision_payoffs.values())
    for demand in demand_probability
)

evpi = expected_with_perfect_information - best_without_information

print(f"Best decision without information: ₹{best_without_information:,.0f}")
print(f"Expected value with perfect information: ₹{expected_with_perfect_information:,.0f}")
print(f"EVPI: ₹{evpi:,.0f}")


# ---------------------------------------------------------------------------
# 13. CONDITIONAL EXPECTATION
# ---------------------------------------------------------------------------

section("13. Conditional expectation")

customer_segments = {
    "Enterprise": {"probability": 0.20, "revenue": 1200},
    "SMB": {"probability": 0.50, "revenue": 500},
    "Consumer": {"probability": 0.30, "revenue": 100},
}

expected_revenue = sum(
    item["probability"] * item["revenue"]
    for item in customer_segments.values()
)

show_probability("Expected revenue per customer, normalized", expected_revenue / 1200)
print(f"Expected revenue per customer: ₹{expected_revenue:,.2f}")


# ---------------------------------------------------------------------------
# 14. BINOMIAL PROBABILITY
# ---------------------------------------------------------------------------

section("14. Binomial probability")

print(
    "For n independent trials with success probability p, the probability "
    "of exactly k successes is C(n,k)p^k(1-p)^(n-k)."
)


def binomial_probability(n: int, k: int, p: float) -> float:
    if n < 0 or k < 0 or k > n:
        raise ValueError("Require n >= 0 and 0 <= k <= n.")
    if not 0 <= p <= 1:
        raise ValueError("p must be between 0 and 1.")
    return comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


p_exact_3 = binomial_probability(10, 3, 0.20)
show_probability("P(exactly 3 purchases from 10)", p_exact_3)

p_at_least_1 = 1 - binomial_probability(10, 0, 0.20)
show_probability("P(at least 1 purchase from 10)", p_at_least_1)


# ---------------------------------------------------------------------------
# 15. SEQUENTIAL CONDITIONAL PROBABILITY
# ---------------------------------------------------------------------------

section("15. Sequential business funnel")

funnel = {
    "Visited": 1.00,
    "Signed up | Visited": 0.40,
    "Activated | Signed up": 0.60,
    "Paid | Activated": 0.30,
}

p_paid = (
    funnel["Signed up | Visited"]
    * funnel["Activated | Signed up"]
    * funnel["Paid | Activated"]
)

show_probability("P(Paid)", p_paid)

print(
    "A funnel probability is obtained by multiplying the relevant "
    "conditional probabilities along the path."
)


# ---------------------------------------------------------------------------
# 16. MONTE CARLO SIMULATION
# ---------------------------------------------------------------------------

section("16. Monte Carlo simulation")

rng = Random(42)
trials = 100_000
successes = 0

for _ in range(trials):
    if rng.random() < 0.18:
        successes += 1

simulation_probability = successes / trials
show_probability("Simulated conversion rate", simulation_probability)
show_probability("Theoretical conversion rate", 0.18)

print(
    "Simulation approximates theoretical probabilities and is useful when "
    "analytical calculations become complicated."
)


# ---------------------------------------------------------------------------
# 17. CONDITIONAL SIMULATION
# ---------------------------------------------------------------------------

section("17. Simulating conditional outcomes")

rng = Random(123)
visitors = 100_000
mobile_count = 0
mobile_purchases = 0

for _ in range(visitors):
    is_mobile = rng.random() < 0.60
    if is_mobile:
        mobile_count += 1
        if rng.random() < 0.25:
            mobile_purchases += 1

simulated_mobile_conversion = mobile_purchases / mobile_count

show_probability(
    "Simulated P(Purchase | Mobile)",
    simulated_mobile_conversion,
)
show_probability("Target P(Purchase | Mobile)", 0.25)


# ---------------------------------------------------------------------------
# 18. CONFUSION MATRIX AND CONDITIONAL PROBABILITY
# ---------------------------------------------------------------------------

section("18. Classification metrics as conditional probabilities")

confusion_matrix = {
    "True Positive": 760,
    "False Positive": 140,
    "True Negative": 8500,
    "False Negative": 600,
}

tp = confusion_matrix["True Positive"]
fp = confusion_matrix["False Positive"]
tn = confusion_matrix["True Negative"]
fn = confusion_matrix["False Negative"]

precision = tp / (tp + fp)
recall = tp / (tp + fn)
specificity = tn / (tn + fp)

show_probability("Precision P(Actual positive | Predicted positive)", precision)
show_probability("Recall P(Predicted positive | Actual positive)", recall)
show_probability("Specificity P(Predicted negative | Actual negative)", specificity)


# ---------------------------------------------------------------------------
# 19. RISK SEGMENTATION
# ---------------------------------------------------------------------------

section("19. Conditional probability for customer risk")

risk_segments = {
    "Low": {"share": 0.60, "default_rate": 0.02},
    "Medium": {"share": 0.30, "default_rate": 0.08},
    "High": {"share": 0.10, "default_rate": 0.25},
}

overall_default_rate = sum(
    segment["share"] * segment["default_rate"]
    for segment in risk_segments.values()
)

show_probability("Overall default probability", overall_default_rate)

high_share = risk_segments["High"]["share"]
p_high_given_default = (
    high_share * risk_segments["High"]["default_rate"]
    / overall_default_rate
)

show_probability("P(High risk | Default)", p_high_given_default)


# ---------------------------------------------------------------------------
# 20. DECISION TREE WITH CONDITIONAL PROBABILITIES
# ---------------------------------------------------------------------------

section("20. Decision analysis under uncertainty")

@dataclass
class Scenario:
    name: str
    probability: float
    payoff: float


def expected_value(scenarios: Sequence[Scenario]) -> float:
    total_probability = sum(s.probability for s in scenarios)
    if abs(total_probability - 1.0) > 1e-9:
        raise ValueError("Scenario probabilities must sum to 1.")
    return sum(s.probability * s.payoff for s in scenarios)


launch = [
    Scenario("Strong market", 0.30, 500000),
    Scenario("Normal market", 0.50, 150000),
    Scenario("Weak market", 0.20, -200000),
]

print(f"Launch expected value: ₹{expected_value(launch):,.0f}")


# ---------------------------------------------------------------------------
# 21. BAYESIAN UPDATING
# ---------------------------------------------------------------------------

section("21. Bayesian updating")

print(
    "Bayesian reasoning updates a prior probability after observing new "
    "evidence."
)

prior = 0.20
likelihood_evidence_if_good = 0.75
likelihood_evidence_if_bad = 0.25

p_good = prior
p_bad = 1 - prior

evidence_probability = (
    likelihood_evidence_if_good * p_good
    + likelihood_evidence_if_bad * p_bad
)

posterior_good = (
    likelihood_evidence_if_good * p_good / evidence_probability
)

show_probability("Prior P(Good market)", prior)
show_probability("Evidence probability", evidence_probability)
show_probability("Posterior P(Good market | Evidence)", posterior_good)


# ---------------------------------------------------------------------------
# 22. BASE-RATE FALLACY
# ---------------------------------------------------------------------------

section("22. Base-rate fallacy")

print(
    "A common business mistake is to focus on P(Evidence | Condition) "
    "without calculating P(Condition | Evidence)."
)

base_rate = 0.005
detection_rate = 0.99
false_positive_rate = 0.02

posterior = (
    detection_rate * base_rate
    / (
        detection_rate * base_rate
        + false_positive_rate * (1 - base_rate)
    )
)

show_probability("Base rate", base_rate)
show_probability("Detection rate", detection_rate)
show_probability("False positive rate", false_positive_rate)
show_probability("P(Condition | Positive signal)", posterior)


# ---------------------------------------------------------------------------
# 23. SIMPSON'S PARADOX
# ---------------------------------------------------------------------------

section("23. Simpson's paradox")

print(
    "Aggregated data can reverse a relationship observed within groups."
)

# Treatment A and B are compared in two customer segments.
groups = {
    "High-value": {
        "A": (90, 100),
        "B": (180, 200),
    },
    "Low-value": {
        "A": (9, 10),
        "B": (1, 2),
    },
}

for group, treatments in groups.items():
    a_success, a_total = treatments["A"]
    b_success, b_total = treatments["B"]
    print(
        f"{group}: A={a_success/a_total:.2%}, "
        f"B={b_success/b_total:.2%}"
    )

a_success_total = sum(v["A"][0] for v in groups.values())
a_total_total = sum(v["A"][1] for v in groups.values())
b_success_total = sum(v["B"][0] for v in groups.values())
b_total_total = sum(v["B"][1] for v in groups.values())

print(f"Aggregated A: {a_success_total/a_total_total:.2%}")
print(f"Aggregated B: {b_success_total/b_total_total:.2%}")

print(
    "The example illustrates why segmentation and conditioning can be "
    "essential for correct business interpretation."
)


# ---------------------------------------------------------------------------
# 24. CORRELATION IS NOT CONDITIONAL CAUSATION
# ---------------------------------------------------------------------------

section("24. Correlation, conditional probability, and causation")

print(
    "A high P(A | B) does not establish that B causes A. Confounding "
    "variables, selection effects, reverse causality, and measurement "
    "bias can create conditional associations."
)

print("Business example:")
print("P(Purchase | Email recipient) > P(Purchase | Non-recipient)")
print("does not by itself prove that email caused the purchases.")
print("Recipients may have been selected because they were already likely to buy.")


# ---------------------------------------------------------------------------
# 25. AB TESTING
# ---------------------------------------------------------------------------

section("25. Conditional probability in A/B testing")

control_visitors = 5000
control_conversions = 450
treatment_visitors = 5000
treatment_conversions = 550

control_rate = control_conversions / control_visitors
treatment_rate = treatment_conversions / treatment_visitors
absolute_lift = treatment_rate - control_rate
relative_lift = absolute_lift / control_rate

show_probability("Control conversion", control_rate)
show_probability("Treatment conversion", treatment_rate)
print(f"Absolute lift: {absolute_lift:.2%}")
print(f"Relative lift: {relative_lift:.2%}")


# ---------------------------------------------------------------------------
# 26. STANDARD ERROR OF A PROPORTION
# ---------------------------------------------------------------------------

section("26. Sampling uncertainty")

def proportion_standard_error(p: float, n: int) -> float:
    if not 0 <= p <= 1:
        raise ValueError("p must be between 0 and 1.")
    if n <= 0:
        raise ValueError("n must be positive.")
    return sqrt(p * (1 - p) / n)


standard_error = proportion_standard_error(treatment_rate, treatment_visitors)
approx_margin = 1.96 * standard_error

print(f"Treatment rate: {treatment_rate:.2%}")
print(f"Approximate standard error: {standard_error:.4f}")
print(f"Approximate 95% margin of error: ±{approx_margin:.2%}")


# ---------------------------------------------------------------------------
# 27. EXPECTED LOSS AND DECISION THRESHOLDS
# ---------------------------------------------------------------------------

section("27. Decision thresholds")

print(
    "A rational decision can depend on the probability of an adverse event "
    "and the financial consequences of each action."
)

cost_of_action = 10000
loss_if_event_without_action = 80000
loss_if_event_with_action = 10000

risk_reduction = loss_if_event_without_action - loss_if_event_with_action

break_even_probability = cost_of_action / risk_reduction

print(f"Cost of preventive action: ₹{cost_of_action:,.0f}")
print(f"Risk reduction if event occurs: ₹{risk_reduction:,.0f}")
show_probability(
    "Break-even event probability",
    break_even_probability,
)

print(
    "If the estimated event probability exceeds the break-even probability, "
    "the preventive action has positive expected monetary value."
)


# ---------------------------------------------------------------------------
# 28. CONDITIONAL PROBABILITY CLASS
# ---------------------------------------------------------------------------

section("28. A small probability table abstraction")

class ProbabilityTable:
    """Represent a finite joint probability table."""

    def __init__(self, table: Dict[str, Dict[str, float]]) -> None:
        self.table = table
        self._validate()

    def _validate(self) -> None:
        if not self.table:
            raise ValueError("Probability table cannot be empty.")

        total = 0.0
        for row in self.table.values():
            if not row:
                raise ValueError("Each row must contain outcomes.")
            for value in row.values():
                if value < 0:
                    raise ValueError("Probabilities cannot be negative.")
                total += value

        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"Joint probabilities must sum to 1, got {total}.")

    def marginal_row(self, row_name: str) -> float:
        return sum(self.table[row_name].values())

    def marginal_column(self, column_name: str) -> float:
        return sum(
            row.get(column_name, 0.0)
            for row in self.table.values()
        )

    def joint(self, row_name: str, column_name: str) -> float:
        return self.table[row_name][column_name]

    def conditional_column_given_row(
        self,
        column_name: str,
        row_name: str,
    ) -> float:
        denominator = self.marginal_row(row_name)
        if denominator == 0:
            raise ZeroDivisionError("Conditioning event has probability zero.")
        return self.joint(row_name, column_name) / denominator

    def conditional_row_given_column(
        self,
        row_name: str,
        column_name: str,
    ) -> float:
        denominator = self.marginal_column(column_name)
        if denominator == 0:
            raise ZeroDivisionError("Conditioning event has probability zero.")
        return self.joint(row_name, column_name) / denominator


table = ProbabilityTable(
    {
        "New": {"Buy": 0.08, "No Buy": 0.42},
        "Returning": {"Buy": 0.20, "No Buy": 0.30},
    }
)

show_probability(
    "P(Buy | Returning)",
    table.conditional_column_given_row("Buy", "Returning"),
)
show_probability(
    "P(Returning | Buy)",
    table.conditional_row_given_column("Returning", "Buy"),
)


# ---------------------------------------------------------------------------
# 29. ZERO-PROBABILITY CONDITIONING
# ---------------------------------------------------------------------------

section("29. Edge case: conditioning on an impossible event")

try:
    conditional_probability(0, 0)
except ValueError as error:
    print(f"Handled invalid conditioning event: {error}")


# ---------------------------------------------------------------------------
# 30. PRODUCT AND REVENUE DECISION MODEL
# ---------------------------------------------------------------------------

section("30. Integrated business decision model")

@dataclass
class MarketState:
    name: str
    probability: float


@dataclass
class ProductDecision:
    name: str
    payoffs: Dict[str, float]


market_states = [
    MarketState("High demand", 0.30),
    MarketState("Normal demand", 0.50),
    MarketState("Low demand", 0.20),
]

decisions = [
    ProductDecision(
        "Launch large",
        {
            "High demand": 600000,
            "Normal demand": 180000,
            "Low demand": -250000,
        },
    ),
    ProductDecision(
        "Launch small",
        {
            "High demand": 300000,
            "Normal demand": 140000,
            "Low demand": 20000,
        },
    ),
    ProductDecision(
        "Delay launch",
        {
            "High demand": 100000,
            "Normal demand": 80000,
            "Low demand": 50000,
        },
    ),
]

decision_values: Dict[str, float] = {}

for decision in decisions:
    value = sum(
        state.probability * decision.payoffs[state.name]
        for state in market_states
    )
    decision_values[decision.name] = value
    print(f"{decision.name:15s}: ₹{value:,.0f}")

best_decision = max(decision_values, key=decision_values.get)
print(f"Recommended decision under expected value: {best_decision}")


# ---------------------------------------------------------------------------
# 31. RISK-ADJUSTED DECISION MAKING
# ---------------------------------------------------------------------------

section("31. Expected value versus risk")

def expected_value_and_variance(
    outcomes: Sequence[Tuple[float, float]]
) -> Tuple[float, float]:
    """
    outcomes contains (probability, payoff).
    Returns expected payoff and population variance.
    """
    total_probability = sum(p for p, _ in outcomes)
    if abs(total_probability - 1) > 1e-9:
        raise ValueError("Probabilities must sum to 1.")

    mean = sum(p * payoff for p, payoff in outcomes)
    variance = sum(
        p * (payoff - mean) ** 2
        for p, payoff in outcomes
    )
    return mean, variance


risky = [(0.50, 300000), (0.50, -100000)]
stable = [(0.90, 120000), (0.10, 80000)]

for name, outcomes in [("Risky", risky), ("Stable", stable)]:
    mean, variance = expected_value_and_variance(outcomes)
    print(
        f"{name}: expected=₹{mean:,.0f}, "
        f"standard deviation=₹{sqrt(variance):,.0f}"
    )


# ---------------------------------------------------------------------------
# 32. VALUE OF INFORMATION FROM A SIGNAL
# ---------------------------------------------------------------------------

section("32. Imperfect information")

print(
    "Real business information is rarely perfect. A signal can be evaluated "
    "using its conditional probabilities rather than assuming certainty."
)

p_good = 0.40
p_signal_good_given_good = 0.80
p_signal_good_given_bad = 0.30

p_signal_good = (
    p_signal_good_given_good * p_good
    + p_signal_good_given_bad * (1 - p_good)
)

p_good_given_signal = (
    p_signal_good_given_good * p_good / p_signal_good
)

show_probability("P(Good market)", p_good)
show_probability("P(Signal | Good market)", p_signal_good_given_good)
show_probability("P(Signal | Bad market)", p_signal_good_given_bad)
show_probability("P(Signal)", p_signal_good)
show_probability("P(Good market | Signal)", p_good_given_signal)


# ---------------------------------------------------------------------------
# 33. PRACTICAL CHECKLIST
# ---------------------------------------------------------------------------

section("33. Conditional probability checklist")

checklist = [
    "Define the event of interest clearly.",
    "Define the conditioning event clearly.",
    "Distinguish P(A | B) from P(B | A).",
    "Check whether the conditioning event has positive probability.",
    "Use joint probability and the correct denominator.",
    "Consider base rates before interpreting signals.",
    "Check whether events are actually independent.",
    "Segment data when aggregation can hide differences.",
    "Separate association from causation.",
    "Quantify uncertainty before making high-stakes decisions.",
    "Use expected value when comparing uncertain financial outcomes.",
]

for number, item in enumerate(checklist, start=1):
    print(f"{number:2d}. {item}")


# ---------------------------------------------------------------------------
# 34. MINI TEST SUITE
# ---------------------------------------------------------------------------

section("34. Embedded validation tests")

def run_tests() -> None:
    assert abs(conditional_probability(25, 100) - 0.25) < 1e-12
    assert abs(binomial_probability(1, 1, 0.7) - 0.7) < 1e-12
    assert abs(binomial_probability(1, 0, 0.7) - 0.3) < 1e-12
    assert abs(1 - (p_churn + p_retention)) < 1e-12

    try:
        conditional_probability(1, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("Zero conditioning count should fail.")

    try:
        binomial_probability(5, 6, 0.5)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid k should fail.")

    try:
        ProbabilityTable({"A": {"X": 0.4}})
    except ValueError:
        pass
    else:
        raise AssertionError("Joint probability table must sum to 1.")

    print("All embedded tests passed.")


run_tests()


# ---------------------------------------------------------------------------
# 35. FINAL BUSINESS INTERPRETATION
# ---------------------------------------------------------------------------

section("35. Final interpretation")

print(
    "Conditional probability is a framework for reasoning about uncertainty "
    "when information is available."
)
print(
    "In business, the conditioning information might be a customer segment, "
    "market condition, observed signal, product interaction, risk category, "
    "or previous stage in a process."
)
print(
    "The most important discipline is to identify exactly what is being "
    "conditioned on before calculating or interpreting a probability."
)
