# Descriptive statistics

## Introduction

Descriptive statistics is the branch of statistics concerned with organizing, summarizing, describing, and interpreting observed data.

This study script develops the main descriptive measures used to understand numerical datasets:

- Mean
- Median
- Mode
- Range
- Quartiles
- Interquartile range
- Variance
- Standard deviation
- Percentiles
- Mean absolute deviation concepts
- Median absolute deviation
- Z-scores
- Coefficient of variation
- Population and sample measures
- Frequency and grouped data
- Weighted statistics
- Robust statistics
- Streaming statistics

The Python implementation uses only the standard library. It includes manual implementations, validation, edge-case handling, numerical-stability considerations, comparisons with Python's `statistics` module, and assertion-based tests.

## What descriptive statistics does

Descriptive statistics converts a collection of observations into information that is easier to understand.

Consider:

`[10, 20, 20, 30, 40]`

Looking at the individual observations gives some information, but descriptive measures provide a structured description:

- The mean identifies the arithmetic center.
- The median identifies the middle ordered observation.
- The mode identifies the most frequent observation.
- The range measures the distance between the smallest and largest observations.
- Variance measures squared deviation from the mean.
- Standard deviation expresses typical spread in the original units.
- Quartiles divide ordered data into sections.
- The interquartile range measures the spread of the middle 50%.

Descriptive statistics does not automatically establish causation, explain why observations occurred, or prove that a sample represents an entire population.

## Population and sample

A **population** is the complete set of observations relevant to a particular question.

A **sample** is a subset of a population.

For example, if the objective is to describe the exam scores of every student in a class, the entire class can be treated as the population.

If the objective is to estimate the performance of all students in a university by examining only some students, the observed students form a sample.

This distinction is especially important for variance and standard deviation.

### Population notation

A population commonly uses:

- `N` for population size
- `μ` for population mean
- `σ²` for population variance
- `σ` for population standard deviation

### Sample notation

A sample commonly uses:

- `n` for sample size
- `x̄` for sample mean
- `s²` for sample variance
- `s` for sample standard deviation

## Numerical and categorical data

Descriptive measures depend on the type of data.

### Numerical data

Numerical data represents measurable quantities.

Examples:

- Age
- Income
- Temperature
- Revenue
- Exam scores
- Response time
- Distance

Mean, median, variance, and standard deviation are commonly used with numerical data.

### Categorical data

Categorical data represents groups or labels.

Examples:

- Red, blue, green
- Product category
- Department
- Payment method
- Region

Mode is particularly useful for categorical data because frequency can be calculated even when arithmetic operations have no meaningful interpretation.

## Mean

The arithmetic mean is calculated as:

`mean = sum of observations / number of observations`

For observations `x₁, x₂, ..., xₙ`:

`x̄ = Σxᵢ / n`

For a population:

`μ = Σxᵢ / N`

### Example

For:

`[10, 20, 30, 40, 50]`

the sum is `150` and there are `5` observations.

Therefore:

`mean = 150 / 5 = 30`

The script demonstrates this both with a simple `sum()` implementation and with `math.fsum()`.

### Why mean is useful

The mean uses every observation. This makes it mathematically convenient and useful in many applications.

It is widely used in:

- Business reporting
- Scientific measurements
- Academic performance analysis
- Financial analysis
- Machine learning
- Quality control
- Operations analysis

### Sensitivity to extreme values

The mean is sensitive to outliers.

Consider:

`[20, 21, 22, 23, 24, 25, 26]`

Adding `200` substantially increases the mean.

This is an important reason to compare the mean with the median when data may be skewed or contain extreme observations.

## Weighted mean

Not every observation must contribute equally to an average.

A weighted mean is:

`weighted mean = Σ(wᵢxᵢ) / Σwᵢ`

where:

- `xᵢ` is an observation
- `wᵢ` is its weight

For example, suppose three assessments have scores:

`80, 90, 70`

with weights:

`0.2, 0.5, 0.3`

The weighted mean is:

`(80 × 0.2 + 90 × 0.5 + 70 × 0.3) / 1`

which equals `83`.

Weights can represent:

- Importance
- Frequency
- Probability
- Portfolio allocation
- Credit
- Sampling weights

The meaning of the weights must be understood before interpreting the result.

## Median

The median is the central value after observations are sorted.

For an odd number of observations, the median is the single middle observation.

For an even number of observations, the median is usually calculated as the average of the two middle observations.

### Odd example

Data:

`[7, 2, 9, 4, 5]`

Sorted:

`[2, 4, 5, 7, 9]`

The median is:

`5`

### Even example

Data:

`[7, 2, 9, 4, 5, 10]`

Sorted:

`[2, 4, 5, 7, 9, 10]`

The two middle observations are `5` and `7`.

Therefore:

`median = (5 + 7) / 2 = 6`

### Why median is useful

The median is much less affected by extreme values than the mean.

For income, property prices, waiting times, and other skewed measurements, the median can provide a more representative measure of the typical observation.

## Mean versus median

Mean and median answer related but different questions.

| Measure | Interpretation | Outlier sensitivity |
|---|---|---|
| Mean | Arithmetic average | High |
| Median | Central ordered position | Low |

For approximately symmetric data without severe outliers, the mean can be highly informative.

For strongly skewed data, the median often provides a more stable description of the center.

## Mode

The mode is the most frequently occurring observation.

For:

`[1, 2, 2, 3, 4]`

the mode is:

`2`

A dataset can have:

- One mode
- Two modes
- Several modes
- No unique mode because all observations have equal frequency

### Unimodal data

A distribution with one dominant mode is called unimodal.

### Bimodal data

A distribution with two equally dominant modes is bimodal.

### Multimodal data

A distribution with several dominant modes is multimodal.

The script implements mode detection using `collections.Counter`.

It also demonstrates Python's `statistics.multimode()`.

### Mode for categorical data

Mode is particularly useful for categorical data.

For:

`["red", "blue", "blue", "green"]`

the mode is:

`"blue"`

Mean and standard deviation would not normally be meaningful for these labels.

## Range

The range is:

`range = maximum - minimum`

For:

`[4, 8, 15, 16, 23, 42]`

the minimum is `4` and the maximum is `42`.

Therefore:

`range = 42 - 4 = 38`

Range is easy to calculate but uses only two observations.

A single extreme value can therefore dramatically change the range.

## Quartiles

Quartiles divide ordered numerical data into portions.

The most commonly discussed quartiles are:

- Q1: first quartile
- Q2: second quartile
- Q3: third quartile

Q2 corresponds to the median under the percentile convention used in the script.

Conceptually:

- Approximately 25% of observations are at or below Q1.
- Approximately 50% are at or below Q2.
- Approximately 75% are at or below Q3.

Exact percentile values can differ between statistical software because multiple percentile definitions exist.

The script explicitly implements a linear-interpolation percentile method so that the calculation rule is visible rather than hidden.

## Interquartile range

The interquartile range is:

`IQR = Q3 - Q1`

The IQR describes the spread of the middle 50% of observations.

Unlike the range, it ignores the extreme lower and upper portions of the ordered dataset.

This makes the IQR more resistant to outliers.

## IQR-based outlier rule

A common descriptive rule defines:

`lower fence = Q1 - 1.5 × IQR`

`upper fence = Q3 + 1.5 × IQR`

Observations outside these fences are often called potential outliers.

The term **potential** is important.

An observation outside the fence is not automatically wrong.

It may represent:

- A legitimate rare event
- A genuine customer
- A major transaction
- A system incident
- A measurement error
- A data-entry error
- A different underlying population

Statistical rules identify observations for investigation. They do not establish the cause.

## Variance

Variance measures the average squared deviation from the mean.

For a population:

`σ² = Σ(xᵢ - μ)² / N`

For a sample:

`s² = Σ(xᵢ - x̄)² / (n - 1)`

The process is:

1. Calculate the mean.
2. Subtract the mean from every observation.
3. Square each deviation.
4. Add the squared deviations.
5. Divide by the appropriate denominator.

### Why square deviations?

Simply adding deviations from the mean would produce zero because positive and negative deviations cancel.

Squaring makes all deviations non-negative.

For example:

`+5` becomes `25`

and:

`-5` also becomes `25`

This allows the magnitude of deviations to be accumulated.

## Population variance versus sample variance

The denominators are different.

Population variance:

`N`

Sample variance:

`n - 1`

The sample calculation uses `n - 1`, commonly called **Bessel's correction**.

Under the usual independent random-sampling assumptions, dividing by `n - 1` makes sample variance an unbiased estimator of the population variance.

This does not mean that sample variance is always numerically larger for every possible dataset in every comparison, but with the same observations the denominator is smaller, so the computed sample variance is larger whenever the numerator is positive.

## Why variance is in squared units

Suppose the original variable is measured in meters.

The deviations are measured in meters.

After squaring them, variance is measured in:

`meters²`

This can make variance less intuitive to communicate.

For that reason, standard deviation is often easier to interpret.

## Standard deviation

Standard deviation is the square root of variance.

Population standard deviation:

`σ = √σ²`

Sample standard deviation:

`s = √s²`

Standard deviation has the same units as the original variable.

If response time is measured in milliseconds, standard deviation is also measured in milliseconds.

If sales are measured in rupees, standard deviation is measured in rupees.

## Interpreting standard deviation

Standard deviation describes the overall spread of observations around the mean.

It does not mean that every observation is exactly one standard deviation away from the mean.

Nor does standard deviation alone tell us the complete shape of a distribution.

For approximately normal data, standard-deviation-based intervals have familiar interpretations, but those interpretations depend on distributional assumptions.

For arbitrary skewed or heavy-tailed data, those normal-distribution rules should not be applied automatically.

## Comparing datasets

Two datasets can have the same mean but very different variability.

For example:

`[50, 50, 50, 50, 50]`

has zero variability.

A dataset such as:

`[30, 40, 50, 60, 70]`

has the same mean of `50` but considerably greater spread.

This demonstrates why a center measure alone is insufficient.

A useful descriptive report often combines:

- Center
- Spread
- Position
- Frequency
- Outlier information

## Outliers

An outlier is an observation that is unusually distant from the rest of the data.

Outliers can strongly affect:

- Mean
- Variance
- Standard deviation
- Range

Median and IQR are generally more resistant.

This distinction is important in practical analysis.

An outlier should not simply be deleted because it makes the statistics look inconvenient.

The analyst should determine whether the observation is:

- Valid
- Invalid
- Misrecorded
- From another population
- A rare but genuine event

## Skewness and mean-median relationships

Skewness describes asymmetry in a distribution.

A right-skewed distribution often has a longer upper tail.

A left-skewed distribution often has a longer lower tail.

A common descriptive pattern is:

- Right skew: mean tends to exceed median.
- Left skew: mean tends to be below median.
- Symmetric data: mean and median may be close.

These are useful descriptive relationships rather than universal mathematical rules.

The script includes Pearson's second coefficient of skewness:

`3(mean - median) / standard deviation`

This is only one descriptive skewness measure. It should not be confused with every formal definition of skewness.

## Frequency data

Frequency data stores distinct values together with the number of times each value occurs.

For example:

Values:

`[10, 20, 30, 40]`

Frequencies:

`[2, 3, 4, 1]`

This represents:

`10, 10, 20, 20, 20, 30, 30, 30, 30, 40`

The frequency-weighted mean is:

`Σ(xᵢfᵢ) / Σfᵢ`

Frequency representations are useful when raw observations are unavailable or when data naturally arrives as counts.

## Grouped data

Grouped data represents observations through intervals.

For example:

- 0–10
- 10–20
- 20–30
- 30–40

If only the intervals and frequencies are known, individual observations are unavailable.

A common approximation uses class midpoints.

For an interval from 10 to 20:

`midpoint = (10 + 20) / 2 = 15`

The estimated mean then uses the midpoints as representative values.

This is an approximation because all observations inside a class are treated as if they were represented by the midpoint.

## Weighted statistics versus frequency statistics

Weights and frequencies are related but should not automatically be treated as identical concepts.

A frequency normally represents how many times an observation occurs.

A statistical weight can represent:

- Sampling importance
- Reliability
- Probability
- Portfolio allocation
- Survey adjustment

The mathematical calculation may look similar, but the interpretation is different.

## Robust statistics

A statistic is called robust when it is relatively resistant to certain unusual observations or deviations from assumptions.

Common robust descriptive measures include:

- Median
- IQR
- MAD

The median is robust to extreme values because its position depends primarily on ordering.

The IQR focuses on the middle half of the observations.

## Median absolute deviation

The median absolute deviation, or MAD, is:

`MAD = median(|xᵢ - median(x)|)`

The process is:

1. Calculate the median.
2. Calculate the absolute deviation of every observation from that median.
3. Take the median of those absolute deviations.

MAD is useful when a dataset contains outliers or is strongly non-normal.

## Percentiles

A percentile indicates a location within an ordered dataset.

Examples:

- 25th percentile
- 50th percentile
- 75th percentile
- 90th percentile
- 95th percentile
- 99th percentile

The 50th percentile corresponds to the median under the percentile method implemented in the script.

Percentiles are particularly useful for:

- Service-level reporting
- Response-time analysis
- Income analysis
- Exam performance
- Risk analysis
- Performance monitoring

A 99th percentile response time, for example, describes the threshold below which approximately 99% of observations fall under the chosen percentile definition.

## Percentile definitions

Percentiles are not defined by one universally implemented algorithm.

Different statistical packages may use different conventions for:

- Position calculation
- Interpolation
- Small datasets
- Boundary values

Therefore, when exact reproducibility matters, the percentile definition should be documented.

The script uses:

`position = (n - 1) × p`

with linear interpolation.

## Coefficient of variation

The coefficient of variation is:

`CV = standard deviation / mean`

It is dimensionless.

It can be useful when comparing relative variability across measurements with different scales.

For example, two business processes may have different average values but similar relative variability.

CV requires care when the mean is:

- Zero
- Very close to zero
- Negative
- Not meaningful as a reference point

For these situations, CV may be misleading or undefined.

## Z-scores

A z-score standardizes an observation relative to a dataset's mean and standard deviation.

The basic formula is:

`z = (x - mean) / standard deviation`

Interpretation:

- `z = 0`: observation equals the mean.
- Positive z-score: observation is above the mean.
- Negative z-score: observation is below the mean.

The magnitude indicates how far the observation is from the mean in standard-deviation units.

Z-scores are commonly used for:

- Standardization
- Anomaly screening
- Comparison across scales
- Statistical modeling

The meaning of a z-score depends on the standardization convention and the distribution being analyzed.

## Streaming statistics

Traditional calculations may require storing all observations.

This can be impractical for:

- Sensor streams
- Server logs
- Financial tick data
- Large event streams
- Continuous monitoring systems

The script implements `RunningStatistics`, which maintains:

- Observation count
- Running mean
- Running second-moment accumulator

The implementation uses **Welford's algorithm**.

Each observation updates the state without requiring the entire dataset to remain in memory.

## Welford's algorithm

Welford's algorithm is numerically stable for online variance calculation.

The important state variables are:

- `count`
- `mean`
- `m2`

For a new value:

`delta = x - mean`

The mean is updated using:

`mean = mean + delta / count`

A second deviation is then calculated and used to update `m2`.

Population variance is:

`m2 / count`

Sample variance is:

`m2 / (count - 1)`

This approach is preferable to repeatedly recalculating all deviations when data arrives incrementally.

## Numerical stability

Mathematically, population variance can be written as:

`E[X²] - E[X]²`

This is mathematically equivalent to the deviation-based formula.

In floating-point arithmetic, the two terms can be extremely large and nearly equal.

Subtracting them can cause loss of significant precision. This phenomenon is known as **catastrophic cancellation**.

The script compares a naive implementation with a deviation-based implementation and demonstrates why numerically stable algorithms matter.

## Floating-point arithmetic

Computers generally represent ordinary Python floating-point values using binary floating-point representation.

Some decimal values cannot be represented exactly in binary floating point.

For example, the mathematical decimal relationship:

`0.1 + 0.2 = 0.3`

does not necessarily produce exact equality using binary floating-point arithmetic.

This matters when statistics involve:

- Financial values
- Repeated calculations
- Very large values
- Very small differences
- Large datasets

The script demonstrates Python's `decimal.Decimal` for cases where decimal arithmetic is appropriate.

## Descriptive statistics profile

The script provides a `DescriptiveStatistics` data class containing:

- Count
- Minimum
- Maximum
- Range
- Mean
- Median
- Modes
- Population variance
- Population standard deviation
- Sample variance
- Sample standard deviation
- Q1
- Q3
- IQR
- MAD

The `describe()` function produces this profile from a validated numerical dataset.

This approach illustrates how several individual statistical calculations can be organized into a reusable analytical component.

## Edge cases

Statistical implementations need explicit handling for unusual inputs.

### Empty dataset

There is no arithmetic mean for an empty dataset.

The script raises `ValueError`.

### Single observation

For:

`[42]`

the population variance is:

`0`

because there is no variation within the complete population represented by that single observation.

Sample variance is undefined because `n - 1 = 0`.

### Constant dataset

For:

`[10, 10, 10, 10]`

the mean is `10`.

The median is `10`.

The variance is `0`.

The standard deviation is `0`.

### Negative values

Negative observations are valid for many variables.

For example:

- Profit/loss
- Temperature in some scales
- Returns
- Deviations
- Coordinates

Statistical calculations do not inherently require observations to be positive.

### Zero mean

The coefficient of variation is undefined when the mean is zero.

### Non-finite values

The implementation rejects:

- `NaN`
- Positive infinity
- Negative infinity

unless a different missing-data policy is explicitly designed.

## Missing values

Real datasets often contain missing observations.

A statistical system should explicitly define how missing values are treated.

Possible approaches include:

- Remove missing observations
- Impute missing observations
- Treat missingness as a category where appropriate
- Report the number of missing observations
- Use domain-specific missing-data methods

Silently converting missing values into zero is generally incorrect unless zero has a specific meaning in the dataset.

## Common mistakes

### Confusing variance and standard deviation

Variance is measured in squared units.

Standard deviation is measured in the original units.

### Using the wrong denominator

Population variance uses:

`N`

Sample variance uses:

`n - 1`

### Assuming mean always represents a typical observation

In skewed datasets, the mean may be strongly affected by extreme values.

### Removing outliers automatically

An outlier is not automatically a data error.

### Ignoring units

A standard deviation of `10` has very different meanings depending on whether the measurement is:

- 10 rupees
- 10 milliseconds
- 10 kilograms
- 10 kilometers

### Treating categorical labels as numerical measurements

Assigning numbers to categories does not automatically make arithmetic operations meaningful.

### Ignoring data collection

A perfectly calculated mean from biased or nonrepresentative data can still produce a misleading result.

## Mean, median, mode and spread comparison

| Measure | Primary purpose | Outlier sensitivity | Typical use |
|---|---|---|---|
| Mean | Arithmetic center | High | Numerical averages |
| Median | Central ordered position | Low | Skewed data |
| Mode | Most frequent value | Frequency-dependent | Categorical or repeated values |
| Range | Total span | Very high | Simple spread |
| Variance | Squared spread | High | Statistical calculations |
| Standard deviation | Spread in original units | High | General variability |
| IQR | Middle 50% spread | Low | Robust analysis |
| MAD | Robust deviation from median | Low | Robust analysis |

## Choosing the appropriate measure

There is no single descriptive statistic that is best for every dataset.

### Approximately symmetric numerical data

Mean and standard deviation are often useful.

### Strongly skewed numerical data

Median and IQR can provide a more representative description.

### Data containing significant outliers

Compare:

- Mean
- Median
- Standard deviation
- IQR
- MAD

The differences themselves can reveal how strongly the outliers influence the data.

### Categorical data

Mode and frequency counts are generally more appropriate than mean or variance.

### Service-time data

Percentiles such as the 50th, 90th, 95th and 99th percentiles can be more informative than an average alone.

## Real-world application: student scores

The script analyzes student scores using:

- Mean
- Median
- Mode
- Range
- Standard deviation
- Quartiles
- IQR

A score distribution can contain repeated values, high performers, low performers, and potentially unusual observations.

Reporting only the average may hide important differences in performance.

## Real-world application: business sales

Monthly sales often contain unusual periods caused by:

- Seasonal demand
- Promotions
- Major contracts
- Holidays
- Supply constraints
- One-time transactions

A single unusually high month can raise the mean substantially.

Comparing the mean and median can reveal this effect.

Standard deviation can then describe the overall variability.

## Real-world application: investment returns

Investment returns can be summarized using mean return and standard deviation.

Standard deviation is frequently used as a descriptive measure of return variability.

The script also demonstrates why standard deviation does not describe every aspect of investment risk.

It does not by itself capture:

- Direction of deviations
- Tail behavior
- Maximum loss
- Drawdown
- Asymmetry
- Dependence between assets

Therefore, standard deviation is one descriptive measure rather than a complete risk model.

## Real-world application: delivery times

Operational data such as delivery times is often skewed.

A small number of very slow deliveries can significantly increase the mean.

Median and percentiles can therefore be valuable.

For customer-facing services, a percentile can answer questions such as how slow the service becomes for the worst-performing portion of observations.

## Real-world application: system response times

The integrated case study uses response times containing a large delay.

The outlier increases:

- Mean
- Range
- Variance
- Standard deviation

Robust measures such as median, IQR and MAD are less affected.

This illustrates why production monitoring commonly examines distributions rather than relying on averages alone.

## Data validation

The script validates numerical input before calculating statistics.

Validation checks include:

- Empty datasets
- Numeric conversion
- Boolean rejection
- Non-finite values
- Matching lengths for values and weights
- Valid weights
- Valid frequencies
- Adequate sample size

Validation is part of statistical implementation rather than an optional programming detail.

## Data quality

Statistical calculations cannot compensate for incorrect data.

Before interpreting results, analysts should consider:

- Measurement accuracy
- Missing observations
- Duplicate observations
- Invalid values
- Unit consistency
- Sampling method
- Time period
- Population definition
- Data collection process
- Selection bias

A mathematically correct statistic can still be substantively misleading if the underlying data is poor.

## Security considerations

Statistical systems can process sensitive information.

Security considerations include:

- Restricting access to sensitive datasets
- Protecting stored data
- Validating externally supplied input
- Avoiding execution of untrusted expressions
- Limiting resource usage for extremely large inputs
- Avoiding unnecessary exposure of individual-level observations

Aggregated statistics can also disclose sensitive information in some contexts, particularly when groups are very small or when multiple statistics can be combined to infer individual values.

## Performance considerations

For a dataset containing `n` observations:

- Mean can generally be calculated in `O(n)` time.
- Variance can generally be calculated in `O(n)` time.
- Standard deviation is `O(n)` when variance is calculated directly.
- Mode using a frequency dictionary is typically `O(n)` expected time.
- A full sort for median is `O(n log n)` time.
- Welford's online algorithm processes observations in `O(n)` total time with `O(1)` additional state.

Median can theoretically be computed using selection algorithms in expected or worst-case linear time depending on the algorithm, but a full sort is often simpler and practical.

## Memory considerations

Storing every observation requires memory proportional to `n`.

Welford's algorithm only needs a fixed amount of state for mean and variance.

This makes it useful for:

- Streaming data
- Large logs
- Sensor systems
- Real-time monitoring
- Incremental analytics

Percentiles and exact medians are more difficult to compute in a strict streaming environment because their calculation depends on the distribution of observations.

Large-scale systems may therefore use approximate quantile algorithms.

## Computational accuracy

There is a distinction between:

- Mathematical correctness
- Numerical stability
- Data correctness

A formula can be mathematically correct while a particular floating-point implementation is numerically unstable.

A numerically stable implementation can still produce misleading results if the data is incorrect.

A perfectly accurate dataset can still be inappropriate if the statistical measure does not match the analytical question.

Good statistical computing considers all three.

## Python implementation choices

The script deliberately includes both simple and more robust implementations.

For example, the arithmetic mean can be represented conceptually as:

`sum(values) / len(values)`

but the implementation also uses `math.fsum()` to reduce floating-point summation error.

The script also compares its results with Python's standard `statistics` module:

- `statistics.mean`
- `statistics.median`
- `statistics.multimode`
- `statistics.pvariance`
- `statistics.variance`
- `statistics.pstdev`
- `statistics.stdev`

This provides an independent implementation for verification.

## Testing

The script contains assertion-based tests covering:

- Mean
- Median
- Population variance
- Sample variance
- Standard deviation
- Mode
- Weighted mean
- Range
- Quartiles
- IQR
- Welford's algorithm
- Empty input
- Insufficient sample size
- Non-finite input

Testing is important because statistical code can produce plausible-looking numbers even when the implementation is incorrect.

## Important distinctions

### Mean versus median

Mean uses the magnitude of every observation.

Median primarily uses the ordered position of observations.

### Variance versus standard deviation

Variance uses squared units.

Standard deviation returns to the original units.

### Population versus sample

Population measures describe the complete population being considered.

Sample measures are used when observations are treated as a sample from a larger population.

### Range versus IQR

Range uses the minimum and maximum.

IQR uses Q1 and Q3.

IQR is therefore more resistant to extreme values.

### Standard deviation versus MAD

Standard deviation is mean-based and sensitive to extreme observations.

MAD is median-based and more robust.

## Limitations

Descriptive statistics has important limitations.

A mean does not describe the complete distribution.

A median does not describe variability.

A standard deviation does not describe skewness by itself.

Variance does not identify the reason for variability.

Mode does not necessarily exist uniquely.

Range is extremely sensitive to extreme observations.

IQR ignores information outside the middle 50%.

MAD is robust but can be less familiar to audiences accustomed to standard deviation.

No single statistic can fully describe a complex dataset.

For meaningful analysis, multiple measures should often be considered together.

## Practical reporting

A useful descriptive report might include:

- Number of observations
- Missing observations
- Mean
- Median
- Standard deviation
- Minimum
- Maximum
- Quartiles
- IQR
- Relevant percentiles
- Outlier information
- Units
- Population/sample definition

The correct combination depends on the data and analytical objective.

For skewed operational data, percentiles may be particularly important.

For approximately symmetric scientific measurements, mean and standard deviation may be appropriate.

For heavily contaminated or outlier-prone data, median, IQR and MAD may provide a more robust description.

## Script structure

The Python file progresses from fundamental calculations to more advanced implementations.

The main components include:

- Basic data validation
- Arithmetic mean
- Weighted mean
- Median
- Mode
- Range
- Percentiles
- Quartiles
- IQR
- Population variance
- Sample variance
- Population standard deviation
- Sample standard deviation
- Frequency statistics
- Grouped-data approximation
- Robust statistics
- Coefficient of variation
- Z-scores
- Welford's algorithm
- Numerical-stability comparison
- Decimal arithmetic
- A reusable descriptive-statistics data class
- Outlier detection
- Real-world examples
- Edge-case demonstrations
- Verification against Python's statistics library
- Assertion-based testing

## Key formulas

### Arithmetic mean

`x̄ = Σxᵢ / n`

### Weighted mean

`weighted mean = Σ(wᵢxᵢ) / Σwᵢ`

### Population variance

`σ² = Σ(xᵢ - μ)² / N`

### Sample variance

`s² = Σ(xᵢ - x̄)² / (n - 1)`

### Population standard deviation

`σ = √σ²`

### Sample standard deviation

`s = √s²`

### Range

`range = maximum - minimum`

### Interquartile range

`IQR = Q3 - Q1`

### Z-score

`z = (x - mean) / standard deviation`

### Coefficient of variation

`CV = standard deviation / mean`

### Median absolute deviation

`MAD = median(|xᵢ - median(x)|)`

## Conceptual hierarchy

Descriptive statistics can be viewed as several related questions.

**What is the center?**

- Mean
- Median
- Mode

**How widely are the observations spread?**

- Range
- Variance
- Standard deviation
- IQR
- MAD

**Where does an observation lie within the distribution?**

- Percentiles
- Quartiles
- Z-scores

**How frequently do values occur?**

- Frequency
- Mode

**How can unusual observations be identified?**

- IQR fences
- Z-scores
- Robust measures

The most useful analysis often combines several of these perspectives rather than relying on one number.
