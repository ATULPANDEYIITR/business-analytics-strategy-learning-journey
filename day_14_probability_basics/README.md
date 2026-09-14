# Probability basics and business applications

## Introduction

Probability is the mathematical framework for describing uncertainty. It assigns numerical values to uncertain events and provides a structured way to reason about possible outcomes.

In business, uncertainty appears in customer conversion, product demand, credit defaults, fraud detection, insurance claims, quality defects, financial returns, project outcomes, and operational failures. Probability allows these uncertain situations to be represented quantitatively and used in forecasting and decision analysis.

The accompanying Python script develops probability from elementary concepts through probability distributions, simulation, statistical reasoning, and practical business applications. The implementation uses only the Python standard library so that the mathematical mechanisms remain visible in the source code.

## Fundamental probability terminology

An **experiment** is a process whose result is uncertain.

An **outcome** is one possible result of an experiment.

A **sample space** is the complete set of possible outcomes.

An **event** is a collection of outcomes from the sample space.

For example, when a six-sided die is rolled, the sample space is:

    {1, 2, 3, 4, 5, 6}

The event of obtaining an even number is:

    {2, 4, 6}

Because three of the six outcomes are even, the probability of an even result is:

    P(even) = 3 / 6 = 0.5

A probability always lies between 0 and 1 inclusive. A probability of 0 represents an impossible event, while a probability of 1 represents a certain event.

## Probability axioms

Probability is governed by three fundamental axioms.

### Non-negativity

For every event A:

    P(A) >= 0

### Normalization

The probability of the entire sample space is:

    P(S) = 1

### Additivity

For mutually exclusive events A and B:

    P(A union B) = P(A) + P(B)

These axioms provide the mathematical foundation for the probability rules demonstrated in the script.

## Classical, empirical, and subjective probability

### Classical probability

Classical probability is appropriate when outcomes are known to be equally likely.

For a finite equally likely sample space:

    P(A) = number of favorable outcomes / number of possible outcomes

Dice and cards provide standard examples.

### Empirical probability

Empirical probability is estimated from observed data:

    empirical probability =
        observed occurrences of an event / total observations

For example, if 80 of 1,000 customers purchase a product, the observed purchase rate is 8%.

Empirical probabilities are central to business analytics because organizations frequently estimate future behavior from historical observations.

### Subjective probability

Subjective probability represents an informed assessment of uncertainty. It may be based on expert judgment, forecasts, scenario analysis, or incomplete information.

Business planning commonly uses subjective probabilities when historical data are insufficient, such as estimating the probability of a new product succeeding in a new market.

## Counting principles

Counting provides the foundation for many classical probability calculations.

The factorial of a non-negative integer n is:

    n! = n × (n-1) × ... × 2 × 1

Permutations count ordered selections:

    P(n,r) = n! / (n-r)!

Combinations count unordered selections:

    C(n,r) = n! / [r!(n-r)!]

The distinction between permutations and combinations is important. If selecting three products where the order of selection has no meaning, combinations are appropriate. If assigning three people to three distinct positions, ordering matters and permutations are appropriate.

## Complements

The complement of event A represents the event that A does not occur.

The complement rule is:

    P(not A) = 1 - P(A)

This is especially useful for "at least one" calculations.

If the probability of a single customer converting is p, the probability that none of n independent customers converts is:

    P(no conversions) = (1-p)^n

Therefore:

    P(at least one conversion) = 1 - (1-p)^n

The Python script uses this relationship in customer conversion and operational examples.

## Union and intersection

The **union** of A and B means that A occurs, B occurs, or both occur.

The **intersection** means that both A and B occur.

The general addition rule is:

    P(A union B) =
        P(A) + P(B) - P(A intersection B)

The intersection is subtracted because it would otherwise be counted twice.

When A and B are mutually exclusive:

    P(A intersection B) = 0

so:

    P(A union B) = P(A) + P(B)

## Conditional probability

Conditional probability measures the probability of one event when information about another event is already known.

The formula is:

    P(A | B) = P(A intersection B) / P(B)

The vertical bar means "given."

For example, suppose 30% of website visitors are mobile users and 18% are both mobile users and purchasers.

Then:

    P(purchase | mobile)
        = 0.18 / 0.30
        = 0.60

The relevant denominator is the mobile population rather than all visitors.

Conditional probability is fundamental to segmentation. Businesses frequently need probabilities such as:

    P(purchase | customer segment)

    P(default | borrower category)

    P(churn | subscription plan)

    P(fraud | transaction flagged)

## Multiplication rule

The general multiplication rule is:

    P(A intersection B) = P(A | B)P(B)

An equivalent form is:

    P(A intersection B) = P(B | A)P(A)

This rule is useful when an event occurs as part of a sequence of conditional stages.

For a customer funnel:

    P(customer)
        =
        P(signup)
        × P(trial | signup)
        × P(customer | trial)

The multiplication rule allows the probability of a complete business process to be decomposed into measurable stages.

## Independence

Two events are independent when knowledge that one occurred does not change the probability of the other.

For independent events:

    P(A intersection B) = P(A)P(B)

An equivalent condition is:

    P(A | B) = P(A)

Independence is a strong assumption. It should not be introduced merely because it makes a calculation easier.

Business observations can be dependent because customers belong to the same households, products share supply chains, transactions occur during the same market conditions, or observations are collected over time.

## Mutual exclusivity

Mutually exclusive events cannot occur simultaneously.

For mutually exclusive A and B:

    P(A intersection B) = 0

Mutual exclusivity is not the same as independence.

For example, a customer receiving a discount and the same customer receiving no discount are mutually exclusive outcomes. They are not independent when both have positive probability.

## Bayes' theorem

Bayes' theorem reverses conditional probabilities:

    P(A | B) =
        P(B | A)P(A) / P(B)

For a binary partition:

    P(A | B) =
        P(B | A)P(A)
        /
        [P(B | A)P(A) + P(B | not A)P(not A)]

Bayes' theorem is particularly important when a business observes evidence and wants to estimate the probability of an underlying condition.

Applications include:

- fraud detection
- credit risk
- medical testing
- quality inspection
- cybersecurity
- customer classification
- risk assessment

### Base-rate effects

Suppose fraud occurs in only 1% of transactions. A detection system identifies 90% of fraudulent transactions but also flags 5% of legitimate transactions.

The probability that a flagged transaction is actually fraudulent is not 90%. The large population of legitimate transactions generates many false positives.

This is a base-rate effect.

The example demonstrates why the probability of an observation given a condition is not interchangeable with the probability of the condition given the observation.

## Law of total probability

Suppose B1, B2, ..., Bn form a partition of the sample space.

Then:

    P(A) = sum P(A | Bi)P(Bi)

This is the law of total probability.

It is useful when the overall business probability depends on several customer or risk segments.

For example, if different customer groups have different conversion rates, the overall conversion rate is a weighted combination of their conditional conversion rates.

This also means that an overall business KPI can change even when individual segment-level probabilities remain constant if the composition of the customer population changes.

## Random variables

A random variable maps outcomes of a random experiment to numerical values.

A **discrete random variable** has countable possible values.

A **continuous random variable** can take values over an interval.

For a discrete random variable, a probability mass function assigns a probability to each possible value.

A valid discrete distribution satisfies:

    P(X=x) >= 0

and:

    sum P(X=x) = 1

The script implements a reusable discrete distribution class with methods for expected value, variance, standard deviation, and threshold probabilities.

## Expected value

Expected value is the probability-weighted average of possible outcomes.

For a discrete random variable:

    E[X] = sum xP(X=x)

Consider possible project outcomes:

    -$10,000
    $2,000
    $15,000
    $30,000

Each outcome has an associated probability. The expected monetary value is calculated by multiplying every outcome by its probability and adding the results.

Expected value is useful for comparing uncertain alternatives.

It does not mean that the expected outcome is guaranteed. A project can produce a result far above or below its expected value.

## Variance and standard deviation

Variance measures the dispersion of outcomes around their expected value:

    Var(X) = E[(X-mu)^2]

Standard deviation is the square root of variance:

    SD(X) = sqrt(Var(X))

Variance is expressed in squared units, while standard deviation uses the same units as the original variable.

For business decisions, standard deviation can describe the scale of uncertainty around an expected result.

## Covariance and correlation

Covariance measures whether two variables tend to move together:

    Cov(X,Y) = E[(X-mu_X)(Y-mu_Y)]

Correlation standardizes covariance:

    Corr(X,Y) =
        Cov(X,Y) / [SD(X)SD(Y)]

Correlation ranges from -1 to +1.

A positive correlation indicates that higher values of one variable tend to be associated with higher values of the other. A negative correlation indicates an inverse relationship.

Correlation does not prove causation.

For example, advertising expenditure and revenue may be positively correlated. That alone does not prove that advertising caused the entire observed revenue change because seasonality, pricing, market growth, or other factors may also be involved.

## Bernoulli distribution

A Bernoulli random variable has exactly two possible outcomes.

Usually:

    success = 1
    failure = 0

If the success probability is p:

    P(X=1) = p

    P(X=0) = 1-p

The mean is:

    E[X] = p

The variance is:

    Var(X) = p(1-p)

Business examples include:

- conversion versus no conversion
- default versus no default
- fraud versus legitimate transaction
- defective versus acceptable product
- machine failure versus successful operation

## Binomial distribution

The binomial distribution counts successes across a fixed number of independent Bernoulli trials with the same probability of success.

Its probability mass function is:

    P(X=k) = C(n,k)p^k(1-p)^(n-k)

Its mean is:

    E[X] = np

Its variance is:

    Var(X) = np(1-p)

The standard assumptions are:

- fixed number of trials
- two possible outcomes per trial
- constant probability of success
- independence between trials

For example, if 20 prospects each have a 10% conversion probability and the trials are treated as independent, the number of conversions can be modeled as binomial.

The model becomes questionable when conversion probabilities vary substantially between customers or when customer outcomes are dependent.

## Geometric distribution

The geometric distribution models the number of independent trials required to obtain the first success.

For the first success on trial k:

    P(X=k) = (1-p)^(k-1)p

The expected number of trials is:

    E[X] = 1/p

Business examples include:

- calls until the first sale
- applications until the first approval
- attempts until a system succeeds

The geometric distribution has the memoryless property. Past failures do not change the probability structure of future independent trials.

## Poisson distribution

The Poisson distribution models the number of events occurring within a fixed interval when the process can reasonably be represented by a stable average event rate.

Its probability mass function is:

    P(X=k) = e^(-lambda)lambda^k / k!

Its mean and variance are both:

    E[X] = lambda

    Var(X) = lambda

Business applications include:

- customer calls per hour
- insurance claims per month
- website incidents per day
- store arrivals
- machine defects

A Poisson model should not be applied automatically. Strong seasonality, changing event rates, clustering, or dependence can violate the assumptions.

## Normal distribution

The normal distribution is continuous and symmetric around its mean.

It is characterized by:

    mean = mu
    standard deviation = sigma

A value can be standardized using:

    Z = (X-mu)/sigma

The Python script implements the normal probability density function and cumulative distribution function using the standard library.

Normal distributions are commonly used in:

- process variation
- forecasting
- measurement error
- statistical inference
- sampling distributions
- simplified financial models

Real business data do not automatically follow a normal distribution. Skewed, bounded, discrete, multimodal, and heavy-tailed data may require other models.

## Law of Large Numbers

The Law of Large Numbers states that under appropriate conditions, an empirical average approaches the expected value as the number of observations increases.

The script demonstrates this by repeatedly simulating coin flips.

The principle does not imply that every short sequence must be balanced.

It also does not mean that a random event is "due" to occur after a sequence of opposite results.

A fair coin remains 50% likely to produce heads on an independent next toss regardless of previous results.

This distinction prevents the gambler's fallacy.

## Central Limit Theorem

The Central Limit Theorem states, under appropriate conditions, that the sampling distribution of an average becomes approximately normal as sample size increases.

If individual observations have mean mu and standard deviation sigma, the standard error of the sample mean is approximately:

    sigma / sqrt(n)

The Central Limit Theorem supports many statistical procedures used in business:

- confidence intervals
- hypothesis testing
- sample-size calculations
- survey analysis
- A/B testing
- quality control

The theorem concerns the distribution of a statistic such as a sample mean. It does not state that the underlying individual observations must themselves be normally distributed.

## Monte Carlo simulation

Monte Carlo simulation estimates uncertain quantities by generating many random scenarios.

A typical process is:

    1. Define uncertain inputs.
    2. Generate random scenarios.
    3. Calculate an outcome for each scenario.
    4. Repeat the experiment many times.
    5. Analyze the resulting distribution.

The script demonstrates Monte Carlo estimation using a geometric experiment and business demand simulation.

Monte Carlo methods are useful when a problem contains multiple interacting uncertainties for which a simple analytical formula is inconvenient or unavailable.

Applications include:

- demand forecasting
- inventory planning
- project risk
- financial risk
- capacity planning
- insurance
- pricing
- resource allocation

Simulation does not eliminate assumptions. It propagates those assumptions through many possible scenarios.

## Business application: conversion funnels

Business funnels frequently contain sequential stages.

For example:

    visitor
        -> signup
        -> trial
        -> customer

The overall probability can be expressed as:

    P(customer)
        =
        P(signup)
        × P(trial | signup)
        × P(customer | trial)

This decomposition makes it possible to identify the stages where improvement could have the largest effect.

If 50,000 visitors have an end-to-end conversion probability of 2%, the expected number of customers is approximately 1,000.

The actual number will vary because customer outcomes are uncertain.

## Business application: expected revenue

Expected revenue can be represented as:

    Expected revenue =
        expected number of customers
        × expected revenue per customer

If customers can generate different order values, a probability distribution provides a more informative model than assuming every order has the same value.

For order values x_i:

    E[order value] = sum x_iP(X=x_i)

This approach can support revenue forecasting and scenario analysis.

## Business application: quality control

If individual products have an approximately independent defect probability p, the number of defective units in a batch of n can be modeled using the binomial distribution.

The probability of zero defects is:

    P(X=0) = (1-p)^n

Therefore:

    P(at least one defect) = 1-(1-p)^n

This can support:

- inspection planning
- quality targets
- rework estimates
- supplier analysis
- production planning

Independence should be evaluated rather than assumed. Manufacturing defects may cluster because of machine settings, raw material problems, production batches, or operator effects.

## Business application: inventory and demand

Inventory decisions are fundamentally probabilistic because future demand is uncertain.

If daily demand is represented by a random variable D and inventory is Q, the probability of a stockout is:

    P(D > Q)

A business can choose inventory levels based on a target service level or stockout probability.

A Poisson model can be useful for certain count-based demand processes, but real demand may include:

- seasonality
- promotions
- holidays
- changing prices
- lead-time uncertainty
- customer substitution
- product interactions

A model that ignores these factors may underestimate inventory risk.

## Business application: fraud detection

Fraud detection demonstrates the importance of conditional probability and base rates.

Important classification quantities include:

### Sensitivity

    P(flag | fraud)

This measures how often fraudulent transactions are successfully flagged.

### False-positive rate

    P(flag | legitimate)

This measures how often legitimate transactions are incorrectly flagged.

### Precision

    P(fraud | flagged)

This answers a different question from sensitivity.

A low underlying fraud rate can result in many false positives even when sensitivity is high.

Operational decisions should therefore consider investigation capacity, customer friction, financial loss, and the cost of false positives.

## Business application: credit risk

A simplified expected credit loss model is:

    ECL = PD × EAD × LGD

where:

**PD** is probability of default.

**EAD** is exposure at default.

**LGD** is loss given default.

For example:

    PD  = 4%
    EAD = $500,000
    LGD = 45%

Then:

    ECL = 0.04 × 500,000 × 0.45
        = $9,000

Production credit-risk systems may incorporate time horizons, discounting, collateral, recovery timing, economic scenarios, borrower characteristics, and portfolio dependencies.

## Business application: insurance

A simplified expected claim loss is:

    Expected loss =
        probability of claim
        × expected claim amount

Insurance pricing also needs to account for costs and uncertainty.

Potential components include:

- expected claims
- operating expenses
- capital requirements
- reinsurance
- taxes
- uncertainty
- risk margin
- profit

Expected loss alone does not capture extreme or catastrophic outcomes.

## Business application: A/B testing

A/B testing compares outcomes between two variants.

For conversion:

    conversion rate =
        conversions / visitors

Absolute lift is:

    rate_B - rate_A

Relative lift is:

    (rate_B - rate_A) / rate_A

Probability and sampling theory help determine whether an observed difference may be explained by random sampling variation.

A valid A/B test requires attention to:

- random assignment
- sample size
- consistent measurement
- experiment duration
- exposure
- repeated testing
- sample-ratio problems
- statistical significance
- practical significance

Statistical significance and business significance are different concepts. A very small effect can become statistically detectable with a sufficiently large sample while remaining economically unimportant.

## Sampling error

For a sample proportion p with sample size n, an approximate standard error is:

    SE(p) = sqrt[p(1-p)/n]

An approximate normal margin of error is:

    z × SE

For an approximately 95% normal interval, z is commonly about 1.96.

Increasing sample size generally reduces sampling uncertainty.

It does not automatically remove:

- selection bias
- measurement bias
- nonresponse bias
- model error
- data leakage
- incorrect population definitions

A very large biased sample can produce a highly precise estimate of the wrong quantity.

## Probability distributions and risk

An expected value alone can hide important business risk.

Consider a project with outcomes ranging from a substantial loss to a large profit.

Two projects can have the same expected profit while having very different:

- probability of loss
- variance
- downside exposure
- tail behavior
- capital requirements

Useful risk measures include:

- expected value
- probability of loss
- standard deviation
- quantiles
- tail probabilities
- scenario probabilities

Decision-making should therefore consider the full distribution whenever the consequences of uncertainty are material.

## Odds and probability

Probability and odds represent the same underlying uncertainty using different scales.

Odds in favor are:

    odds = p / (1-p)

Probability from odds is:

    p = odds / (1+odds)

A probability of 20% corresponds to odds of:

    0.20 / 0.80 = 0.25

Odds are particularly common in logistic regression and some forms of risk modeling.

## Contingency tables

A contingency table organizes observations by categories.

For example, customers may be grouped by:

- new versus returning
- purchased versus did not purchase

Conditional probabilities can then be calculated from the appropriate row or column totals.

For:

    P(purchase | returning customer)

the denominator must be the number of returning customers.

Using the total customer population instead would calculate a different probability.

This denominator discipline is one of the most important practical skills in business probability.

## Segmented probability

Business populations are rarely homogeneous.

Suppose a population consists of:

- low-risk customers
- medium-risk customers
- high-risk customers

Each segment may have a different event probability.

The overall probability is:

    P(A) = sum P(A | segment)P(segment)

This is a weighted probability.

An overall KPI can change because the probability within each segment changed, because the population mix changed, or because both changed.

This distinction is important when interpreting changes in conversion, default, churn, fraud, or defect rates.

## Conditional expectation

Expected value can also be calculated conditionally.

Examples include:

    E(revenue | customer segment)

    E(loss | default)

    E(demand | promotion)

    E(order value | returning customer)

Conditional expectations are useful for understanding heterogeneous populations rather than relying on a single overall average.

## Portfolio probability and risk

For a portfolio with weights w_i and expected returns E[R_i]:

    E[R_p] = sum(w_iE[R_i])

Expected return is not enough to determine portfolio risk.

Portfolio risk depends on:

- individual volatility
- covariance
- correlation
- portfolio weights

Two portfolios can have similar expected returns but very different risk because their assets interact differently.

This illustrates a general principle of probability: relationships between uncertain variables matter, not only their individual distributions.

## Probability calibration

When probabilities are used as predictions, their numerical quality matters.

Suppose a model assigns a group of transactions a 20% probability of fraud. If those probabilities are well calibrated, approximately 20% of comparable transactions should actually be fraudulent over a sufficiently large and representative evaluation sample.

The script demonstrates the Brier score:

    Brier score =
        mean((predicted probability - actual outcome)^2)

Lower values indicate better probabilistic prediction under this metric.

Calibration is important when probability estimates directly determine business actions such as credit limits, fraud investigations, insurance decisions, and resource allocation.

## Common mistakes

### Confusing P(A|B) with P(B|A)

These are generally different probabilities.

### Ignoring base rates

The frequency of an underlying event affects the interpretation of evidence.

### Assuming independence

Independence is a modeling assumption, not a default property of business data.

### Confusing mutual exclusivity with independence

Mutually exclusive events cannot happen together. Independent events can happen together without one changing the probability of the other.

### Treating expected value as a guarantee

Expected value is a long-run probability-weighted quantity, not a prediction of the exact next outcome.

### Treating correlation as causation

Correlation identifies association, not necessarily a causal mechanism.

### Applying a normal distribution without checking assumptions

Business variables can be skewed, bounded, discrete, multimodal, or heavy-tailed.

### Believing that more data automatically fixes bias

More observations reduce sampling variability but do not necessarily correct systematic bias.

### Using the wrong denominator

Conditional probability depends on the population specified by the conditioning event.

## Edge cases and exceptions

Probability implementations must handle mathematical boundary conditions explicitly.

A valid probability must satisfy:

    0 <= p <= 1

A conditional probability is undefined when the conditioning probability is zero.

A normal distribution requires:

    standard deviation > 0

A discrete probability distribution must sum to 1.

For a binomial distribution, a count outside 0 through n has probability zero.

For a Poisson distribution, the rate parameter must be non-negative.

The Python implementation explicitly validates these cases and raises appropriate exceptions rather than silently producing misleading results.

## Numerical considerations

Probability calculations can encounter floating-point precision limitations.

For example, mathematically exact values such as 1 can sometimes be represented internally as a number extremely close to 1.

The script therefore uses `math.isclose` when validating values that theoretically should equal a specific quantity.

Large factorials, powers, and very small probabilities can also create numerical overflow or underflow.

For high-scale production statistical systems, logarithmic probability calculations and specialized numerical libraries are often preferable.

## Performance considerations

Simple probability calculations are generally inexpensive.

Monte Carlo simulation has approximately linear computational cost with the number of simulated trials:

    O(N)

A naive binomial cumulative probability that calculates every probability from 0 through n requires work proportional to n.

Large simulations require attention to:

- execution time
- memory usage
- random-number generation
- numerical stability
- reproducibility
- parallel processing

The script intentionally implements many calculations directly so that the mathematical logic is visible. Production systems can use optimized numerical libraries when performance and scale require them.

## Reproducibility

Random simulations are inherently variable.

A pseudorandom number generator with a fixed seed can reproduce a simulation sequence.

The script uses local `random.Random` instances with explicit seeds in demonstration functions.

This approach is preferable to relying on global random state when reproducibility is important.

Reproducibility is particularly useful for:

- testing
- debugging
- model validation
- experiment comparison
- audit trails

A fixed seed does not make a stochastic process deterministic in the real world. It only makes the computational simulation repeatable.

## Security and data governance

Probability calculations used in business systems can influence important decisions.

Input validation is necessary because invalid counts, probabilities, or parameters can silently distort results.

Customer-level data may contain confidential or sensitive information. Data handling should follow applicable privacy, security, and governance requirements.

Important controls include:

- input validation
- access control
- auditability
- reproducible calculations
- documented assumptions
- model versioning
- data-quality monitoring
- bias analysis
- outcome monitoring

A mathematically correct formula does not guarantee a valid business decision if the underlying data or assumptions are inappropriate.

## Model risk

Probability models simplify reality.

A model can fail because:

- the selected distribution is inappropriate
- probabilities change over time
- observations are dependent
- the sample is not representative
- important variables are missing
- historical relationships no longer hold
- rare events are underestimated
- data contain measurement errors

Model validation should therefore examine both mathematical implementation and real-world assumptions.

## Production implementation considerations

A production probability component should separate several responsibilities:

1. Input validation
2. Data preparation
3. Probability estimation
4. Mathematical calculation
5. Simulation
6. Reporting
7. Monitoring

Important implementation practices include:

- validate probabilities before calculations
- validate sample sizes and counts
- handle zero denominators explicitly
- document assumptions
- test boundary conditions
- use controlled random seeds for reproducible tests
- monitor changes in input distributions
- compare predictions with realized outcomes
- monitor probability calibration
- preserve model and data versions
- avoid silently converting invalid data into valid-looking values

Probability becomes decision infrastructure when it drives pricing, credit, fraud, inventory, staffing, investment, or financial planning.

## Practical reference

| Concept | Notation | Core relationship |
|---|---|---|
| Complement | P(not A) | 1 - P(A) |
| Union | P(A or B) | P(A) + P(B) - P(A and B) |
| Conditional probability | P(A\|B) | P(A and B) / P(B) |
| Independence | P(A and B) | P(A)P(B) |
| Bayes' theorem | P(A\|B) | P(B\|A)P(A) / P(B) |
| Expected value | E[X] | sum of xP(X=x) |
| Variance | Var(X) | E[(X-mu)^2] |
| Standard deviation | SD(X) | sqrt(Var(X)) |
| Bernoulli | P(X=x) | Two possible outcomes |
| Binomial | P(X=k) | C(n,k)p^k(1-p)^(n-k) |
| Geometric | P(X=k) | (1-p)^(k-1)p |
| Poisson | P(X=k) | e^(-lambda)lambda^k/k! |
| Normal standardization | Z | (X-mu)/sigma |
| Credit loss | ECL | PD × EAD × LGD |
| Proportion standard error | SE(p) | sqrt[p(1-p)/n] |
| Odds | odds | p/(1-p) |

## Relationship between probability models and business problems

| Business problem | Useful probability concept |
|---|---|
| Customer conversion | Bernoulli, binomial, conditional probability |
| Conversion funnel | Conditional and multiplication rules |
| Fraud detection | Bayes' theorem, base rates, conditional probability |
| Credit risk | Expected value and conditional probability |
| Insurance | Expected loss and severity probability |
| Quality control | Binomial probability |
| Customer arrivals | Poisson distribution |
| Inventory | Demand distributions and tail probabilities |
| A/B testing | Sampling distributions and probability |
| Revenue forecasting | Expected value and conditional expectation |
| Portfolio analysis | Expected return, variance, covariance |
| Project decisions | Expected monetary value |
| Risk analysis | Probability distributions and simulation |
| Forecast evaluation | Calibration and probabilistic scoring |

## Structure of the Python implementation

The script is organized into progressively more advanced sections.

The early functions introduce terminology, sample spaces, event operations, counting, complements, unions, intersections, and conditional probability.

The middle sections implement probability distributions and mathematical quantities such as expected value, variance, covariance, correlation, and standard errors.

The later sections connect these concepts to business use cases including conversion funnels, revenue, quality control, inventory, fraud, credit, insurance, A/B testing, portfolio analysis, and decision analysis.

The final sections address edge cases, common mistakes, performance, security, model governance, calibration, and production design.

The script also includes a small self-test suite. Running it directly executes the demonstrations and validates several core mathematical functions.
