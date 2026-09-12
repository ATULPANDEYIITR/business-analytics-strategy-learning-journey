# Data distributions: normal, skewed and categorical distributions

## Introduction

A data distribution describes how observations are arranged across possible values or categories. Distribution analysis is one of the foundations of statistics because it provides a structured way to understand the center, spread, frequency, probability, shape, variability, and unusual observations within a dataset.

A distribution can describe an observed dataset, a sample drawn from a population, or a theoretical probability model. The distinction matters because an empirical distribution is based on actual observations, while a theoretical distribution describes an assumed mathematical process.

This study script develops distribution concepts from basic frequency tables through probability distributions, normal distributions, skewness, categorical distributions, sampling distributions, the Central Limit Theorem, empirical cumulative distributions, kernel density estimation, simulation, and practical data-quality considerations.

The Python implementation uses only the standard library. It is therefore possible to run the complete script without installing a numerical or plotting package.

## What a distribution represents

Suppose a dataset contains:

    2, 3, 3, 4, 4, 4, 5, 5, 6

The distribution tells us how frequently each value occurs.

The value 4 occurs three times, so its empirical relative frequency is:

    3 / 9 = 0.3333

This means approximately 33.33% of the observations are equal to 4.

A distribution therefore contains information about both individual values and their frequencies.

For numerical data, distribution analysis commonly considers:

- location
- spread
- shape
- tails
- outliers
- quantiles
- probability
- dependence on other variables

For categorical data, the primary focus is usually:

- category counts
- category proportions
- dominant categories
- rare categories
- imbalance
- joint category frequencies
- conditional proportions

## Population and sample distributions

A population is the complete collection of units relevant to a statistical question.

A sample is a subset of that population.

For example, if a company has 100,000 customers, the complete customer population contains 100,000 customers. A survey of 1,000 customers represents a sample.

The population distribution describes the actual distribution across all population members. The sample distribution describes the observations obtained from the sample.

These two distributions are not normally identical. Even a properly selected random sample can differ from the population because of sampling variability.

There is also an important third concept: the sampling distribution.

A sampling distribution is the probability distribution of a statistic calculated from repeated samples. For example, repeatedly drawing samples and calculating their means produces a sampling distribution of the sample mean.

This distinction is central to inferential statistics.

## Types of variables

The script distinguishes several important variable types.

### Nominal variables

Nominal variables contain categories without an inherent mathematical ordering.

Examples include:

- department
- country
- product type
- browser
- payment method

If the categories are encoded as 1, 2, and 3, those numbers are labels rather than quantities. Arithmetic operations on the codes are generally meaningless.

### Ordinal variables

Ordinal variables have a meaningful order but not necessarily equal numerical distances between categories.

Examples include:

- poor, fair, good, excellent
- low, medium, high
- bronze, silver, gold

The fact that one category is above another does not automatically mean that the numerical distance between categories is known.

### Discrete variables

Discrete numerical variables have countable possible values.

Examples include:

- number of purchases
- number of employees
- number of defects
- number of support tickets

### Continuous variables

Continuous variables can theoretically take any value within an interval.

Examples include:

- height
- weight
- temperature
- elapsed time
- distance

A measured continuous variable is usually represented with finite precision in a dataset even though the underlying quantity may conceptually be continuous.

## Frequency distributions

A frequency distribution records how many observations occur at each value or category.

For categorical data, a frequency table might contain:

    Category     Frequency
    Basic        4
    Premium      5
    Enterprise   3

A relative-frequency distribution divides each frequency by the total number of observations.

If a category occurs 5 times in a dataset containing 12 observations:

    Relative frequency = 5 / 12

which is approximately 41.67%.

Relative frequencies are especially useful when comparing datasets of different sizes.

## Histograms

A histogram groups numerical observations into intervals called bins.

Unlike a categorical bar chart, a histogram represents numerical ranges. The width and placement of the bins influence how the distribution appears visually.

The script implements an ASCII histogram so the concept can be studied without a plotting library.

For example, a histogram may reveal:

- concentration around a central value
- a long right tail
- a long left tail
- multiple clusters
- gaps
- unusually extreme observations

Histogram interpretation should be performed carefully because different bin widths can create different visual impressions.

Too few bins can hide meaningful structure.

Too many bins can make random variation appear to be meaningful structure.

A histogram is a descriptive diagnostic, not proof that a dataset follows a particular probability distribution.

## Mean

The arithmetic mean is:

    mean = sum(x_i) / n

The mean uses every numerical observation.

For example:

    Data = 2, 4, 6

    Mean = (2 + 4 + 6) / 3
         = 4

The mean is useful for many analytical and financial calculations, but it is sensitive to extreme observations.

Consider:

    10, 11, 12, 13, 100

The observation 100 substantially increases the mean even though most observations are close to 10 through 13.

## Median

The median is the middle location after observations are ordered.

For an odd number of observations, it is the central observation.

For an even number, a percentile convention generally determines the value between the two central observations. The script uses linear interpolation for percentile calculations.

The median is more robust to extreme values than the mean.

This makes it especially useful for strongly skewed variables such as:

- income
- transaction value
- house prices
- customer spending
- waiting time

## Mode

The mode is the most frequently occurring value or category.

A distribution may have:

- one mode
- multiple modes
- no uniquely dominant mode

The mode is especially useful for categorical data because the mean is generally not meaningful for nominal categories.

## Variance

Population variance measures average squared deviation from the population mean:

    Var(X) = E[(X - μ)^2]

For a finite population:

    variance = sum((x_i - μ)^2) / N

Sample variance generally uses n - 1 in the denominator:

    s² = sum((x_i - x̄)^2) / (n - 1)

The distinction between population variance and sample variance matters in statistical estimation.

The Python script explicitly implements population variance while also using Python's standard-library sample variance function.

## Standard deviation

Standard deviation is the square root of variance.

It is expressed in the same units as the original variable.

For example, if a dataset measures revenue in dollars, the standard deviation is also expressed in dollars.

This makes standard deviation easier to interpret than variance in many practical settings.

Standard deviation is highly sensitive to extreme observations.

## Quantiles and percentiles

Quantiles divide an ordered distribution into portions.

Common quartiles are:

- Q1: 25th percentile
- Q2: 50th percentile
- Q3: 75th percentile

The second quartile is the median.

The interquartile range is:

    IQR = Q3 - Q1

The IQR describes the spread of the middle 50% of observations.

Percentiles are useful for:

- performance rankings
- income analysis
- examination scores
- latency analysis
- risk analysis
- service-level analysis

The script implements percentile calculation using linear interpolation.

Different statistical software packages can use different percentile conventions, especially for small datasets. Percentile results should therefore be interpreted together with the chosen calculation method.

## Normal distribution

The normal distribution is a continuous probability distribution characterized by a mean and standard deviation.

It is written as:

    X ~ N(μ, σ²)

where:

- μ is the mean
- σ is the standard deviation
- σ² is the variance

The probability density function is:

    f(x) =
        1 / (σ sqrt(2π))
        × exp(-0.5 ((x - μ) / σ)²)

The normal distribution is:

- continuous
- symmetric
- unimodal
- bell-shaped
- completely determined by its mean and standard deviation

For an ideal normal distribution:

    mean = median = mode

This equality is a consequence of symmetry and the particular shape of the normal distribution. It should not be treated as a universal rule for all datasets.

## Normal probability density function

A probability density function, or PDF, describes density rather than assigning ordinary point probabilities.

For a continuous random variable:

    P(X = x) = 0

for an individual exact point under the standard continuous interpretation.

Probabilities are obtained from areas under the density curve.

For example:

    P(a < X < b)

is the area under the normal density between a and b.

This is an important distinction between PDFs and PMFs.

## Normal cumulative distribution function

The cumulative distribution function, or CDF, is:

    F(x) = P(X <= x)

For a normal distribution, the CDF can be calculated using the error function.

The script implements the normal CDF through Python's mathematical error-function support.

The CDF allows calculations such as:

    P(X < 60)

and:

    P(40 < X < 60)

using:

    P(40 < X < 60)
    =
    F(60) - F(40)

## Z-scores

A z-score standardizes an observation relative to a mean and standard deviation:

    z = (x - μ) / σ

A z-score indicates how many standard deviations an observation lies above or below the mean.

For example, if:

    μ = 100
    σ = 15
    x = 130

then:

    z = (130 - 100) / 15
      = 2

The observation is two standard deviations above the mean.

Z-scores are useful for:

- comparing observations on different scales
- standardization
- detecting unusually distant observations
- interpreting normal probabilities

A z-score does not automatically imply that a value is an outlier. Its interpretation depends on the distribution and analytical context.

## Empirical rule

For an ideal normal distribution:

- approximately 68% of observations fall within ±1 standard deviation
- approximately 95% fall within ±2 standard deviations
- approximately 99.7% fall within ±3 standard deviations

This is often called the 68-95-99.7 rule.

It applies specifically to normal distributions or situations where the normal approximation is justified.

It should not be blindly applied to strongly skewed or otherwise non-normal datasets.

## Skewed distributions

Skewness describes asymmetry in a distribution.

A right-skewed distribution has a longer tail toward larger values.

Typical examples can include:

- customer spending
- income
- transaction sizes
- waiting times
- claim amounts

A left-skewed distribution has a longer tail toward smaller values.

In many right-skewed datasets:

    mean > median

In many left-skewed datasets:

    mean < median

This is a useful diagnostic relationship but not a mathematical definition of skewness.

## Right skew

A right-skewed distribution concentrates observations toward relatively small or moderate values while maintaining a long tail toward larger values.

For example, customer purchase values might contain many small purchases and a smaller number of very large purchases.

The large values can increase the arithmetic mean substantially.

For such data, the median may provide a better description of a typical observation.

The mean may still be important for business calculations because total revenue is based on the sum of transaction values.

Therefore, the choice between mean and median depends on the question being asked.

## Left skew

A left-skewed distribution has a longer tail toward smaller values.

This can occur when most observations are near a high boundary and a smaller number of observations are much lower.

In many left-skewed distributions:

    mean < median

Again, this is a common pattern rather than an absolute rule.

## Skewness statistic

The script implements an adjusted sample skewness measure.

Positive skewness generally indicates a longer or heavier right tail.

Negative skewness generally indicates a longer or heavier left tail.

Skewness close to zero indicates limited third-moment asymmetry, but it does not prove normality.

A distribution can have skewness near zero while still being:

- heavy-tailed
- multimodal
- bounded
- otherwise different from a normal distribution

Therefore, skewness should be interpreted together with graphical and numerical evidence.

## Kurtosis

The script also calculates adjusted excess kurtosis.

Excess kurtosis compares tail and peak characteristics relative to the normal distribution under the particular kurtosis definition used.

Approximately:

    Normal excess kurtosis = 0

Kurtosis is often misunderstood as simply describing whether a distribution is "peaked." In practical analysis, tail behavior is an important part of what kurtosis captures.

Kurtosis should not be interpreted in isolation.

## Transformations

A distribution may be transformed to obtain a more convenient analytical scale.

The script demonstrates:

    log(1 + x)

for non-negative data.

Log transformations are often useful when:

- values span several orders of magnitude
- multiplicative relationships are present
- right skew is substantial
- variance increases with the level of the variable

A logarithmic transformation changes the scale and therefore changes the interpretation of differences.

A transformed variable should not be treated as if it were identical to the original variable.

Transformation should be motivated by the statistical problem rather than performed simply to make a histogram look normal.

## Categorical distributions

Categorical distributions describe frequencies or probabilities of categories.

For example:

    Basic
    Premium
    Enterprise

The empirical probability of a category is:

    P(category) =
        category count / total observations

Categorical distributions are usually represented using:

- frequency tables
- relative-frequency tables
- bar charts
- probability tables

Histograms are generally intended for numerical data, not nominal categories.

## Bernoulli distribution

The Bernoulli distribution describes one binary trial.

The outcome is usually represented as:

    X = 1
    X = 0

If:

    P(X = 1) = p

then:

    P(X = 0) = 1 - p

Examples include:

- purchase versus no purchase
- default versus no default
- success versus failure
- defective versus non-defective

The Bernoulli distribution has only two possible outcomes.

## Binomial distribution

The binomial distribution describes the number of successes in a fixed number of independent Bernoulli trials with constant success probability.

It is written:

    X ~ Binomial(n, p)

Its PMF is:

    P(X = k)
    =
    C(n,k) p^k (1-p)^(n-k)

where:

- n is the number of trials
- k is the number of successes
- p is the probability of success

The script calculates the binomial PMF and verifies that the probabilities across all possible k values sum to one.

## Multinomial distribution

The multinomial distribution generalizes the binomial model to more than two categories.

If category probabilities are:

    p1, p2, ..., pk

then:

    p1 + p2 + ... + pk = 1

For category counts:

    n1, n2, ..., nk

the probability is:

    n! / (n1! n2! ... nk!)
    ×
    p1^n1 p2^n2 ... pk^nk

This model is useful when every observation belongs to exactly one of several possible categories.

## PMF, PDF, and CDF

These three concepts must be distinguished carefully.

### PMF

A probability mass function is used for discrete random variables.

It directly assigns probability to possible discrete outcomes.

Example:

    P(X = 3) = 0.20

### PDF

A probability density function is used for continuous distributions.

It describes density rather than the probability of an individual point.

Probability is obtained through an interval or area.

### CDF

A cumulative distribution function gives:

    F(x) = P(X <= x)

The CDF can be used for both discrete and continuous distributions.

The relationship between these concepts is fundamental to probability modeling.

## Joint distributions

A joint distribution describes combinations of multiple variables.

For example:

    Outcome     Device
    Buy         Mobile
    No Buy      Desktop
    Buy         Tablet

A joint frequency table records how often each combination occurs.

Joint distributions allow questions such as:

    How frequently do mobile users buy?

and:

    How frequently do desktop users not buy?

## Conditional distributions

A conditional distribution describes one variable after conditioning on another.

The conditional probability formula is:

    P(A | B) = P(A and B) / P(B)

For example:

    P(Buy | Mobile)

means the probability of buying given that the device is mobile.

Conditional distributions are widely used in:

- business analytics
- segmentation
- classification
- medical statistics
- risk analysis
- probabilistic modeling

## Empirical cumulative distribution function

The empirical cumulative distribution function, or ECDF, is constructed directly from observed data.

For a sample of n observations:

    ECDF(x)
    =
    number of observations <= x
    /
    n

Unlike a theoretical normal CDF, the ECDF does not require the assumption that the observations follow a normal distribution.

It is useful for comparing empirical distributions and understanding percentile locations.

## Outliers

An outlier is an observation that is unusually distant from the majority of the data.

An extreme observation can result from:

- data-entry error
- measurement error
- fraud
- rare but legitimate behavior
- structural differences
- a different population
- genuine extreme events

An outlier should therefore not be deleted automatically.

The script uses the conventional IQR rule:

    Lower fence = Q1 - 1.5 × IQR
    Upper fence = Q3 + 1.5 × IQR

Observations outside these fences are flagged as potential outliers.

This rule is a screening convention, not a universal definition of an invalid observation.

## Robust statistics

The median and IQR are more robust to extreme observations than the mean and standard deviation.

This makes them useful when distributions are:

- highly skewed
- contaminated by extreme observations
- heavy-tailed
- unsuitable for simple mean-based summaries

A robust analysis may report both:

    Mean + standard deviation

and:

    Median + IQR

when the distribution warrants both perspectives.

## Discrete versus continuous distributions

Discrete distributions assign probability to individual possible values.

For example:

    P(X = 4)

can be positive for a discrete random variable.

Continuous distributions generally assign zero probability to any exact individual point:

    P(X = x) = 0

while interval probabilities can be positive:

    P(a < X < b) > 0

This difference is essential when interpreting PMFs and PDFs.

## Expected value

For a finite discrete distribution:

    E[X] = Σ x p(x)

The expected value is the probability-weighted average of possible outcomes.

For example, if:

    X = 0, 1, 2

and:

    P(X) = 0.2, 0.3, 0.5

then:

    E[X]
    =
    0(0.2) + 1(0.3) + 2(0.5)
    =
    1.3

The expected value is a theoretical quantity. It does not necessarily correspond to an outcome that can actually occur.

## Variance of a discrete distribution

The variance of a discrete random variable can be written as:

    Var(X) = E[X²] - E[X]²

The script calculates both expected value and variance from finite probability distributions.

Variance quantifies dispersion around the expected value.

## Law of Large Numbers

The Law of Large Numbers describes the tendency of sample averages to approach the population expectation as sample size increases, under appropriate assumptions.

The script demonstrates this using repeated random observations.

For a random variable with expected value μ:

    sample mean → μ

as sample size becomes sufficiently large under the relevant conditions.

The Law of Large Numbers does not mean every finite sample will be close to the population mean. It describes asymptotic behavior.

## Central Limit Theorem

The Central Limit Theorem is one of the most important connections between data distributions and sampling distributions.

Under common conditions, the distribution of standardized sample means approaches a normal distribution as sample size increases.

This is important because the original population does not necessarily need to be normally distributed.

The script demonstrates this by:

- generating strongly right-skewed population data
- repeatedly sampling from that population
- calculating sample means
- comparing the resulting sampling distributions

As sample size increases, the distribution of sample means becomes increasingly regular and approximately normal under the applicable conditions.

This does not mean that every sample becomes normally distributed. The theorem concerns the distribution of a statistic across repeated samples.

## Standard error

The standard error of the sample mean is commonly represented as:

    SE(x̄) = s / sqrt(n)

where:

- s is the sample standard deviation
- n is the sample size

The standard error measures variability in the estimated mean across repeated samples.

The inverse square-root relationship is important:

    SE ∝ 1 / sqrt(n)

Therefore, multiplying the sample size by four approximately halves the standard error, assuming the underlying variability remains comparable.

## Kernel density estimation

Kernel density estimation, or KDE, creates a smooth empirical estimate of a continuous density.

The script uses a Gaussian kernel:

    K(u) =
        1 / sqrt(2π) × exp(-u² / 2)

The KDE is:

    f̂(x)
    =
    1 / (n h)
    ×
    Σ K((x - x_i) / h)

where:

- n is the number of observations
- h is the bandwidth
- x_i is an observation

The bandwidth controls smoothness.

A small bandwidth can produce a highly variable estimate.

A large bandwidth can oversmooth genuine structure.

The script uses a version of Silverman's rule of thumb to select a bandwidth automatically.

KDE is particularly useful for exploring distribution shape when histograms are too dependent on arbitrary bin boundaries.

## Distribution shape versus normality

A distribution being symmetric does not mean it is normal.

A symmetric distribution can be:

- uniform
- bimodal
- heavy-tailed
- bounded
- otherwise non-normal

Similarly, skewness close to zero does not prove normality.

Normality is a specific mathematical distributional assumption.

A serious normality assessment may require multiple forms of evidence, such as:

- domain knowledge
- histogram
- Q-Q plot
- ECDF comparison
- numerical diagnostics
- formal tests where appropriate

No single diagnostic should automatically determine the conclusion.

## Sampling bias

A sample can be large but still be biased.

Suppose a population contains a mixture of urban and rural observations, but the sample is collected only from an urban source.

The sample distribution may differ systematically from the population distribution.

Increasing the sample size does not automatically eliminate systematic sampling bias.

This is an important distinction:

- sampling variability is random variation between samples
- sampling bias is systematic distortion in how the sample represents the population

A huge biased sample can produce a very precise estimate of the wrong quantity.

## Categorical imbalance

Categorical imbalance occurs when one or more categories dominate the dataset.

For example:

    Normal = 950
    Fraud = 50

A classifier that always predicts "Normal" would achieve 95% accuracy.

That accuracy may appear high while the model completely fails to identify fraud.

This demonstrates why distribution analysis matters in classification.

Depending on the problem, useful measures can include:

- precision
- recall
- F1 score
- specificity
- balanced accuracy
- class-specific error rates

The appropriate metric depends on the costs of different errors.

## Mean versus median in skewed data

Consider a strongly right-skewed variable such as customer spending.

The mean answers:

    What is the arithmetic average transaction value?

The median answers:

    What is the middle transaction after ordering the observations?

These are different questions.

The median can represent a typical customer more effectively when a small number of customers spend exceptionally large amounts.

The mean may be more relevant for aggregate financial calculations.

There is therefore no universal rule that the median is "better" than the mean. The correct statistic depends on the analytical objective.

## Coefficient of variation

The coefficient of variation is:

    CV = standard deviation / |mean|

It expresses variability relative to the magnitude of the mean.

It can be useful when comparing relative variability across compatible ratio-scale variables.

It should not be used indiscriminately.

It becomes problematic when the mean is zero or very close to zero. It also has limited meaning for variables where zero does not represent a meaningful absence of the measured quantity.

## Standardization

Standardization converts numerical observations into z-score-like values:

    z_i = (x_i - x̄) / s

The transformed variable has:

    mean approximately 0
    standard deviation approximately 1

when the sample mean and sample standard deviation are used.

Standardization preserves ordering but changes the original scale.

It is commonly useful when variables have very different numerical scales, especially in algorithms where feature scale influences optimization or distance calculations.

Standardization does not make a skewed variable normal.

## Monte Carlo simulation

Monte Carlo methods approximate probabilities through repeated random simulation.

For example, to estimate:

    P(80 <= X <= 120)

one can repeatedly sample X and calculate the proportion of simulated observations falling in the interval.

As the number of simulations increases, the estimate generally becomes more stable under appropriate assumptions.

Simulation introduces sampling error. It is therefore an approximation rather than an exact replacement for an analytical solution when an exact solution is available.

## Histogram bin selection

Histogram appearance depends strongly on bin width.

With too few bins:

- important clusters can disappear
- tails can be hidden
- multimodality can be obscured

With too many bins:

- random noise can appear meaningful
- the distribution may look unnecessarily fragmented

Histogram design is therefore part of statistical communication.

The underlying observations do not change when bin width changes. Only the visual grouping changes.

## Empirical distributions versus theoretical distributions

An empirical distribution comes directly from observed data.

A theoretical distribution is a mathematical model.

Examples of theoretical distributions include:

- normal
- Bernoulli
- binomial
- multinomial
- exponential

A theoretical model can simplify analysis and support probability calculations, but it introduces assumptions.

A model should therefore be evaluated against the observed data and the context in which the model is being used.

## Real-world applications

### Finance

Financial variables can exhibit asymmetric or heavy-tailed behavior.

Examples include:

- transaction sizes
- losses
- claims
- asset returns
- customer balances

Assuming normality without checking the distribution can underestimate unusual events when the actual data has heavier tails or substantial asymmetry.

### Business analytics

Business datasets frequently contain skewed numerical variables.

Customer spending, order values, revenue per customer, and transaction sizes often have long right tails.

Categorical distributions are also central to:

- customer segments
- product choices
- acquisition channels
- payment methods
- churn outcomes

### Healthcare

Healthcare data may contain skewed waiting times, costs, laboratory measurements, and event frequencies.

Categorical variables can describe:

- treatment groups
- disease status
- demographic classifications
- outcome categories

The appropriate distributional model depends on the measurement process and domain.

### Machine learning

Distribution analysis helps with:

- feature preprocessing
- scaling
- class imbalance
- anomaly detection
- probability estimation
- model assumptions
- monitoring distribution shifts

Distribution analysis is especially important when training and production data may have different distributions.

### Quality control

Manufacturing and service operations often monitor distributions of:

- defect measurements
- processing times
- dimensional measurements
- error rates
- throughput

Changes in distribution shape can indicate changes in the underlying process.

## Common mistakes

### Treating a histogram as proof of normality

A histogram is a descriptive visualization. It does not prove that a dataset follows a normal distribution.

### Confusing a PDF with probability

A PDF represents density. The probability over an interval is obtained from the area under the density.

### Assuming mean equals median

This relationship is characteristic of certain symmetric distributions. It is not a general rule.

### Ignoring skewness

Strong skew can make mean and standard deviation less representative of a typical observation.

### Automatically deleting outliers

An extreme observation may be a valid and important observation.

### Treating category codes as measurements

Encoding categories as 1, 2, and 3 does not automatically make them numerical quantities.

### Assuming the Central Limit Theorem makes all data normal

The Central Limit Theorem primarily concerns the behavior of sampling distributions under appropriate conditions. It does not state that the original population becomes normal.

### Assuming large samples eliminate bias

Large sample size reduces sampling variability under suitable conditions, but it does not automatically eliminate systematic sampling bias.

### Using one statistic to identify distribution shape

Mean, median, skewness, kurtosis, and standard deviation each capture different properties. Distribution shape should be evaluated using multiple forms of evidence.

## Missing values

Missing values require explicit treatment.

A missing value is not automatically equivalent to zero.

Possible approaches include:

- removing observations under appropriate conditions
- imputation
- model-based handling
- separate missingness indicators
- specialized missing-data methods

The correct method depends on why the values are missing and what the analysis is intended to estimate.

The script demonstrates safe removal of NaN values for a simple example but does not imply that deletion is universally appropriate.

## Data validation

Distribution calculations should operate on valid inputs.

The script validates:

- numerical types
- finite values
- empty datasets
- boolean values accidentally supplied as numbers
- invalid probabilities
- invalid standard deviations
- invalid bandwidths
- incompatible input lengths

This is particularly important in production systems because silent data corruption can produce statistically valid-looking but substantively incorrect results.

## Reproducibility

Random simulations can produce different results each time unless a random seed is fixed.

The script demonstrates deterministic random-number generation with explicit seeds.

Reproducibility is useful for:

- debugging
- testing
- educational demonstrations
- simulation studies
- controlled comparisons

A fixed seed is not a substitute for cryptographically secure randomness where security is required.

## Performance considerations

Several basic operations have different computational costs.

Frequency counting with a hash table is generally O(n) on average.

Sorting is generally O(n log n).

A simple mean calculation is O(n).

A simple variance calculation is O(n).

A percentile calculation that first sorts the data is generally O(n log n).

A naive ECDF query can take O(n), although sorting the data and using binary search can reduce repeated query cost.

Naive KDE evaluation at one point requires O(n) work.

Evaluating KDE over m points can require O(nm).

Monte Carlo simulation is approximately O(number of trials).

Large-scale production analysis often benefits from optimized numerical libraries, vectorized computation, efficient memory layouts, streaming statistics, approximate quantiles, and specialized algorithms.

## Security and data integrity

Statistical analysis can involve sensitive information.

Important practices include:

- restricting access to sensitive datasets
- avoiding unnecessary exposure of individual records
- validating incoming data
- retaining raw data for auditability where appropriate
- documenting transformations
- checking category-label integrity
- separating data ingestion from analytical processing
- recording assumptions
- ensuring reproducibility for controlled analyses

For sensitive categorical distributions, aggregate reporting may be preferable to exposing individual records.

Distribution analysis itself does not guarantee privacy. Appropriate data-governance controls are still required.

## Important distinctions

| Concept | Meaning |
|---|---|
| Population distribution | Distribution of the complete population |
| Sample distribution | Distribution observed in a sample |
| Sampling distribution | Distribution of a statistic across repeated samples |
| Frequency | Number of observations in a value or category |
| Relative frequency | Frequency divided by total observations |
| PMF | Probability assigned to discrete outcomes |
| PDF | Density function for continuous distributions |
| CDF | Probability that a random variable is at or below a value |
| Mean | Arithmetic average |
| Median | Middle location of ordered observations |
| Mode | Most frequently occurring value or category |
| Variance | Squared dispersion around the mean |
| Standard deviation | Square root of variance |
| IQR | Q3 minus Q1 |
| Skewness | Measure of distributional asymmetry |
| Kurtosis | Measure related to tail and fourth-moment behavior |
| Normal distribution | Symmetric bell-shaped theoretical distribution |
| Categorical distribution | Probability distribution over discrete categories |
| ECDF | Cumulative distribution constructed from observed data |
| KDE | Smooth estimated density based on observed data |

## Normal, skewed, and categorical distributions compared

| Characteristic | Normal | Right-skewed | Left-skewed | Categorical |
|---|---|---|---|---|
| Data type | Continuous | Usually numerical | Usually numerical | Categories |
| Symmetry | Symmetric | Asymmetric | Asymmetric | Not described by numerical symmetry |
| Tail | Balanced | Longer right tail | Longer left tail | Category frequencies |
| Common center | Mean | Median often useful | Median often useful | Mode |
| Mean sensitivity | Moderate to outliers | High | High | Usually not applicable |
| IQR | Useful | Often useful | Often useful | Not normally applicable |
| Histogram | Appropriate | Appropriate | Appropriate | Usually use bar chart |
| PMF | No | No | No | Yes for discrete categories |
| PDF | Yes | Depends on model | Depends on model | No |
| CDF | Yes | Yes for continuous model | Yes for continuous model | Yes for discrete distribution |

## Practical interpretation of the case study

The integrated case study models customer order values using an exponential distribution to create a right-skewed business-like variable.

The analysis examines:

- mean
- median
- standard deviation
- quartiles
- IQR
- skewness
- histogram
- potential outliers
- log transformation

The important analytical lesson is that distribution shape determines how numerical summaries should be interpreted.

For strongly right-skewed order values, the mean can be substantially larger than the median.

That does not make the mean incorrect.

It means that the mean and median answer different questions.

The median describes the central position of the ordered observations.

The mean represents the arithmetic average and is directly connected to total value calculations.

A business analyst may therefore need both.

## Edge cases

Distribution analysis should account for special cases such as:

- empty datasets
- a single observation
- constant data
- NaN values
- infinite values
- invalid probability values
- zero standard deviation
- negative values under logarithmic transformations
- extreme outliers
- very small samples
- highly imbalanced categories
- rare categories
- inconsistent category labels

For example, standardization is undefined for constant data because the standard deviation is zero.

Similarly, the coefficient of variation is undefined when the mean is zero.

A logarithmic transformation requires special handling for zero and negative values. The script uses log(1+x) for non-negative observations so that zero can be transformed.

## Limitations of distribution analysis

A distribution describes observed or modeled statistical behavior, but it does not automatically explain causation.

Two variables can have similar distributions while being generated by completely different processes.

Similarly, a visually attractive distribution does not guarantee:

- unbiased sampling
- valid measurement
- absence of data corruption
- independence
- causal interpretation
- appropriate model specification

Distributional analysis should therefore be combined with knowledge of the data-generation process.

## Best practices

Use the distribution that corresponds to the measurement type.

Inspect data before selecting statistical summaries.

Use both numerical and visual diagnostics.

Compare mean and median when skewness may be present.

Use median and IQR when robust summaries are appropriate.

Inspect potential outliers before removing them.

Distinguish discrete probabilities from continuous densities.

Do not interpret categorical codes as numerical measurements without justification.

Do not assume normality merely because a variable is numerical.

Do not apply the 68-95-99.7 rule to arbitrary datasets.

Document transformations.

Document missing-value treatment.

Document sampling assumptions.

Use reproducible random seeds for simulations and tests.

Check category imbalance before interpreting classification accuracy.

Use the Central Limit Theorem correctly as a statement about sampling distributions rather than as a claim that raw data become normal.

Consider computational complexity when distribution calculations must operate over very large datasets.

## Script structure

The Python script is organized as a progressive study file.

It begins with foundational distribution concepts and frequency tables, then moves through descriptive statistics and histograms.

The normal-distribution section implements the PDF, CDF, z-scores, probability calculations, and simulated normal samples.

The skewness section generates right- and left-skewed data and demonstrates how transformations can alter distribution shape.

The categorical section implements empirical category probabilities, Bernoulli probabilities, binomial probabilities, multinomial probabilities, joint frequencies, and conditional probabilities.

The later sections address outliers, robust statistics, ECDFs, the Law of Large Numbers, the Central Limit Theorem, standard error, KDE, standardization, Monte Carlo simulation, computational complexity, data integrity, and reproducibility.

The final integrated case study combines these ideas in a synthetic customer-order analysis.

The script also includes built-in assertions so fundamental calculations can be checked directly when the program is executed.

## Core analytical perspective

Distribution analysis is not simply the process of calculating an average or drawing a histogram.

A complete distributional analysis asks:

- What type of variable is being measured?
- Is the variable discrete or continuous?
- Is the distribution empirical or theoretical?
- Where is the center?
- How dispersed are the observations?
- Is the distribution symmetric?
- Are the tails unusually long?
- Are there potential outliers?
- Are there multiple modes or clusters?
- Are categories balanced?
- How representative is the sample?
- Are missing values affecting the distribution?
- Does a theoretical model such as the normal distribution make sense?
- Is the statistic being used appropriate for the distribution shape?
- What assumptions are required for the intended inference?
- Does the sampling distribution differ from the population distribution?
- Is the computational method appropriate for the data volume?

These questions connect descriptive statistics, probability theory, statistical inference, data quality, and practical decision-making.

## Included computational components

The script contains complete implementations for:

- frequency distributions
- relative frequencies
- histograms
- population variance
- population standard deviation
- percentiles
- quartiles
- IQR
- sample skewness
- excess kurtosis
- normal PDF
- normal CDF
- z-scores
- normal probability calculations
- normal random sampling
- right-skewed data generation
- left-skewed data generation
- logarithmic transformation
- categorical probabilities
- Bernoulli PMF
- binomial PMF
- multinomial probability
- joint categorical frequencies
- conditional probability
- IQR-based outlier detection
- robust statistics
- empirical CDF
- sampling distributions
- standard error
- Gaussian KDE
- Silverman bandwidth estimation
- standardization
- Monte Carlo probability estimation
- distribution profiling
- input validation
- missing-value handling
- reproducibility
- automated assertions

All examples are implemented as executable Python functions rather than placeholders, allowing the script to serve as both an instructional reference and an executable statistical study file.
