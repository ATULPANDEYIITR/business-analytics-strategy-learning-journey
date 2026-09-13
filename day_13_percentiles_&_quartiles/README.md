# Percentiles & Quartiles: Distribution Analysis and Business Interpretation

## Topic introduction

Percentiles and quartiles are descriptive-statistical tools used to understand the position and spread of observations within a dataset. They are particularly useful when the distribution is skewed, contains extreme values, or cannot be described adequately by a single average.

A percentile identifies a value below which a specified percentage of observations fall. For example, the 90th percentile is a value at or below which approximately 90% of observations lie.

Quartiles divide an ordered dataset into four parts:

- Q1 is the 25th percentile.
- Q2 is the 50th percentile, which is the median.
- Q3 is the 75th percentile.

The Python script develops these ideas from basic descriptive statistics through interpolated percentile calculations, five-number summaries, interquartile range analysis, outlier detection, distribution shape, weighted percentiles, empirical cumulative distributions, robust statistics, group comparisons, and business applications.

## Why distribution position matters

An average can conceal important differences between observations.

Consider two datasets with similar means. One may have observations concentrated tightly around the mean, while the other may contain a large number of ordinary observations and a small number of extreme values.

Percentiles reveal where observations are located throughout the distribution.

For business analysis, this is important because decision makers often need answers such as:

- What value represents the typical customer?
- What value separates the top 10% from the rest?
- How large is the middle 50% of the population?
- How long do the slowest 5% of transactions take?
- Which customers belong to the highest-value segment?
- How widely dispersed are employee salaries?
- What response time is experienced by 95% of requests?
- Are unusually large observations distorting the average?

## Fundamental terminology

### Observation

An observation is one measured value in a dataset.

For example:

12, 15, 18, 20, 25

contains five observations.

### Ordered dataset

Percentile calculations require observations to be considered in ascending order.

An original dataset might be:

50, 10, 40, 20, 30

After ordering:

10, 20, 30, 40, 50

The script sorts numerical observations before calculating percentiles.

### Rank

Rank represents the position of an observation within an ordered dataset.

Percentile methods use rank or position calculations to determine the requested distribution point.

### Percentile

The pth percentile represents a distribution location associated with p percent of observations.

Common percentiles include:

- P10: 10th percentile
- P25: 25th percentile
- P50: 50th percentile
- P75: 75th percentile
- P90: 90th percentile
- P95: 95th percentile
- P99: 99th percentile

The interpretation must always consider the direction of the metric.

For a salary dataset, being above P90 means a relatively high salary.

For delivery time, being above P90 means a relatively slow delivery.

### Quartile

Quartiles divide the distribution into four percentile regions.

Q1 is the 25th percentile.

Q2 is the 50th percentile.

Q3 is the 75th percentile.

The four regions are approximately:

- 0th to 25th percentile
- 25th to 50th percentile
- 50th to 75th percentile
- 75th to 100th percentile

The regions contain approximately equal numbers of observations, although repeated values and percentile conventions can affect exact boundaries.

## Percentile calculation

The script implements more than one percentile definition because percentile calculations are not universally defined by a single mathematical convention.

### Nearest-rank method

The nearest-rank method uses a rank based on:

rank = ceiling(p / 100 × n)

where p is the requested percentile and n is the number of observations.

For the 25th percentile, the method identifies an observation at the corresponding rank rather than interpolating between observations.

This method is simple and intuitive, particularly when percentile reporting is defined as a rank-based rule.

### Linear interpolation

The main percentile implementation uses the position:

h = (n - 1) × p

where p is the percentile expressed as a fraction between 0 and 1.

If the position falls between two observations, the result is obtained through linear interpolation.

For example, with:

10, 20

the 25th percentile has position:

(2 - 1) × 0.25 = 0.25

The result is between 10 and 20:

10 + 0.25 × (20 - 10) = 12.5

Therefore, the interpolated 25th percentile is 12.5.

An important consequence is that an interpolated percentile does not necessarily have to be an observed value.

### Hazen method

The script also demonstrates the Hazen plotting-position convention.

Its position is:

h = (n + 1) × p

Different statistical systems can use different quantile conventions. Consequently, two tools may return slightly different percentile values for the same small dataset even when both implementations are mathematically valid.

For reproducible analysis, the percentile method should be documented.

## Boundary values

The 0th percentile corresponds to the minimum under the implementation used in the script.

The 100th percentile corresponds to the maximum.

For a dataset containing one observation, every percentile is that observation.

For example, if the only observation is 42:

P10 = P25 = P50 = P75 = P90 = 42

This is mathematically consistent because there is no distributional variation in a one-observation dataset.

## Quartiles

The script defines:

Q1 = P25

Q2 = P50

Q3 = P75

The median is therefore the second quartile.

For an ordered dataset such as:

10, 20, 30, 40, 50

the median is 30.

With interpolation, quartiles can also lie between observations.

Quartiles are especially useful because they provide distribution information without depending strongly on extreme observations.

## Five-number summary

The five-number summary contains:

1. Minimum
2. Q1
3. Median
4. Q3
5. Maximum

It provides a compact description of the distribution.

For example:

Minimum = 10  
Q1 = 20  
Median = 30  
Q3 = 40  
Maximum = 90

This indicates that the central 50% of observations lies between 20 and 40, while the full observed range extends from 10 to 90.

The five-number summary is the conceptual foundation of a box plot.

## Interquartile range

The interquartile range, or IQR, measures the spread of the middle 50% of observations.

The formula is:

IQR = Q3 - Q1

If:

Q1 = 20

and:

Q3 = 40

then:

IQR = 40 - 20 = 20

Unlike the full range, the IQR is relatively resistant to extreme observations.

This makes it useful for comparing distributions where unusually large or small values exist.

## IQR-based outlier detection

The script implements Tukey-style fences.

The lower fence is:

Q1 - 1.5 × IQR

The upper fence is:

Q3 + 1.5 × IQR

Observations outside these boundaries are classified as potential outliers.

The word "potential" is important. An IQR outlier is not automatically a data error.

A very large customer order may be legitimate.

A very long delivery may represent a real operational event.

An unusually high salary may be valid for a senior executive.

An observation should be investigated using domain knowledge before being removed.

## Percentile rank

Percentile rank reverses the usual percentile question.

Instead of asking:

"What value is the 90th percentile?"

we can ask:

"Approximately what percentage of observations are at or below this value?"

The script calculates empirical percentile rank using:

number of observations less than or equal to the value

divided by:

total number of observations

and multiplied by 100.

For example, if a salary is at or below approximately 85% of observed salaries, its empirical percentile rank is approximately 85.

Percentile rank is useful for benchmarking individuals, customers, transactions, stores, or other units.

## Percentile bands

Percentiles can be used to create analytical segments.

A simple segmentation scheme is:

- 0th to 25th percentile
- 25th to 50th percentile
- 50th to 75th percentile
- 75th to 90th percentile
- 90th to 95th percentile
- Above the 95th percentile

These bands can support customer segmentation, operational monitoring, compensation analysis, risk classification, and performance reporting.

The interpretation depends on the metric.

For customer revenue, the highest percentile band may contain the most valuable customers.

For customer complaints, the highest percentile band may represent customers with the greatest number of complaints.

For response time, the highest percentile band represents the slowest requests.

## Distribution shape

Percentiles are useful for studying the shape of a distribution.

A symmetric distribution tends to have approximately balanced relationships around the median.

A positively skewed distribution has a longer right tail. High values extend substantially farther above the center than low values extend below it.

A negatively skewed distribution has a longer left tail.

The script calculates two descriptive skewness measures.

### Pearson's second coefficient of skewness

The formula used is:

3 × (mean - median) / standard deviation

A positive value suggests right skewness.

A negative value suggests left skewness.

A value near zero suggests approximate symmetry under the selected descriptive measure.

### Bowley skewness

Bowley's quartile skewness is:

(Q3 + Q1 - 2 × Q2) / (Q3 - Q1)

Because it is based on quartiles and the median, it is less sensitive to extreme observations than many statistics based on higher-order moments.

This makes it useful when distributional analysis is intentionally focused on robust positional measures.

## Mean versus median

The mean uses every observation and can be strongly affected by extreme values.

The median is a positional measure and is much less affected by a small number of extreme observations.

Suppose annual customer spending contains many customers spending several hundred currency units and a few customers spending thousands.

The mean may become substantially larger than the spending level of a typical customer.

The median can provide a more representative description of the central customer.

This does not mean the median is always better.

The appropriate statistic depends on the business question.

The mean is useful when total magnitude and additive properties matter.

The median is useful when the typical observation is the primary question.

Percentiles are useful when the location of different parts of the distribution matters.

## Business interpretation of delivery times

The script includes a delivery-time case study.

For operational metrics such as delivery time, lower values are generally preferable.

The median describes the typical observed delivery.

P90 describes a slower part of the customer experience.

P95 gives an even more conservative view.

P99 highlights the extreme upper tail.

This distinction is important because an average delivery time might look acceptable while a significant minority of customers experience very long delays.

A business dashboard that reports only the mean can therefore miss tail-performance problems.

## Business interpretation of customer spending

Customer spending is frequently right-skewed.

A small group of high-value customers can contribute a large amount of revenue.

For this type of distribution, analysts should examine:

- Mean
- Median
- Q1
- Q3
- IQR
- P90
- P95
- P99

A large difference between the mean and median can indicate that high-value observations strongly influence the average.

The appropriate interpretation depends on the business objective.

If management wants to understand the typical customer, the median may be more informative.

If management wants to understand total revenue contribution, the mean and aggregate revenue remain important.

## Business interpretation of salaries

Percentiles can be used to understand relative salary position within an observed workforce.

For example, an employee salary near the 90th percentile is higher than approximately 90% of the salaries in that particular dataset.

This does not establish whether the employee is fairly compensated.

A meaningful compensation analysis may require factors such as:

- Role
- Experience
- Location
- Seniority
- Skill level
- Business unit
- Performance
- External market benchmarks

Percentile rank is therefore a relative statistical description, not a complete compensation decision rule.

## Business interpretation of response times

Software performance often requires tail analysis.

Suppose an application has:

P50 = 100 ms

P90 = 140 ms

P95 = 180 ms

P99 = 300 ms

The median indicates that typical performance is fast, but the P99 indicates that a small fraction of requests are much slower.

Tail percentiles can expose problems caused by:

- Database contention
- Network latency
- Resource exhaustion
- Garbage collection
- External services
- Lock contention
- Large requests
- Uneven workload distribution

For service-level objectives, the exact percentile and threshold should be explicitly defined rather than assumed.

## Weighted percentiles

Not every observation necessarily represents the same amount of population or exposure.

For example, five transactions might have different customer counts associated with them.

A weighted percentile assigns greater influence to observations with larger weights.

The script accepts:

- Observed values
- Non-negative weights
- Requested percentile

The values are sorted, and cumulative weights determine the percentile location.

Weighted percentiles can be useful for:

- Population analysis
- Survey data
- Transaction volumes
- Exposure-weighted risk
- Revenue-weighted analysis
- Customer counts
- Operational workloads

Weights must be defined carefully because changing the weighting scheme changes the meaning of the result.

## Empirical cumulative distribution function

The empirical cumulative distribution function, or ECDF, estimates:

F(x) = P(X <= x)

from observed data.

The script calculates the proportion of observations less than or equal to a selected value.

For example, if 80 out of 100 observations are at or below 500, then the empirical CDF at 500 is 0.80.

This is closely related to percentile interpretation.

Percentiles ask for the value associated with a cumulative probability.

The ECDF asks for the cumulative probability associated with a value.

## Robust statistics

Robust statistics are designed to reduce sensitivity to unusual observations.

The script includes the median, IQR, trimmed mean, and winsorization.

### Trimmed mean

A trimmed mean removes a specified proportion from both tails before calculating the mean.

A 10% trimmed mean removes approximately 10% from each side.

This can reduce the influence of extreme observations.

The trade-off is that observations are deliberately excluded from the calculation.

### Winsorization

Winsorization retains the observations but replaces extreme values with selected percentile boundaries.

For example, values below P5 can be replaced with P5, and values above P95 can be replaced with P95.

The trade-off is that the original extreme values are transformed rather than removed.

Both methods should be documented because they alter the analytical representation of the data.

## Sensitivity analysis

The script demonstrates the effect of adding an extreme observation.

Suppose a dataset contains ordinary values and one extremely large value is added.

The mean can move substantially because the mean uses every numerical magnitude.

The median may move much less.

Q1 and Q3 may also remain relatively stable depending on sample size and location of the extreme value.

This illustrates why distribution analysis should not rely on a single statistic.

Sensitivity analysis is especially important when business conclusions could change because of a small number of extreme observations.

## Group comparison

Percentiles can compare distributions across departments, regions, customer groups, products, or time periods.

The script constructs a distribution profile for each group containing:

- Count
- Minimum
- Q1
- Median
- Q3
- Maximum
- IQR
- P90
- P95
- P99

This allows analysts to distinguish between several types of differences.

Two groups may have similar medians but different IQRs.

That means their typical values are similar while their central spread differs.

Two groups may have similar medians but very different P95 values.

That indicates their upper tails behave differently.

Two groups may have similar P95 values but different medians.

That indicates the typical experience differs even if their slower-tail performance is similar.

## Important distinctions

### Percentile versus percentage

A percentage describes a proportion.

A percentile describes a position within an ordered distribution.

"90%" and "90th percentile" do not mean the same thing.

### Percentile versus percentile rank

A percentile asks:

"What value corresponds to this percentage position?"

A percentile rank asks:

"What percentage of observations are at or below this value?"

### Quartile versus percentile

Quartiles are specific percentiles.

Q1 = P25

Q2 = P50

Q3 = P75

The term percentile is more general.

### IQR versus range

Range is:

maximum - minimum

IQR is:

Q3 - Q1

Range considers the two extreme observations.

IQR focuses on the central 50%.

### Median versus mean

The median is positional.

The mean is arithmetic.

The median is generally less sensitive to extreme values.

The mean has useful mathematical properties for additive and many statistical calculations.

Neither statistic is universally superior.

## Edge cases

The script explicitly handles several edge cases.

### Empty dataset

An empty dataset cannot produce a meaningful percentile and is rejected.

### One observation

All percentile positions map to the same observation.

### Two observations

Interpolation can produce values between the two observed values.

### Identical values

If every observation is identical, all percentiles are identical and the IQR is zero.

### Negative values

Percentiles work normally with negative numerical values.

### Unsorted values

The implementation sorts the data internally.

### NaN

NaN values are rejected because they can make comparisons and statistical calculations unreliable.

### Infinite values

Positive and negative infinity are rejected.

### Non-numeric values

Non-numeric observations are rejected rather than silently interpreted.

## Common mistakes

### Treating P95 as meaning that 95% of values equal the percentile

P95 is a distribution position, not a statement that 95% of observations have the same value.

### Assuming the percentile must be an observed value

Interpolation-based methods can produce values between observations.

### Treating outliers as errors

An outlier is an unusual observation under a statistical rule. It is not automatically an invalid observation.

### Removing outliers without investigation

Removing observations can materially change business conclusions.

The reason for removal should be documented.

### Reporting only the mean

The mean can hide skewness and tail behavior.

A distribution-sensitive report should often include median and selected percentiles.

### Comparing percentiles without considering sample size

Small datasets can produce unstable percentile estimates.

A percentile from a very small sample should not automatically be treated as a highly precise population estimate.

### Ignoring the definition of percentile

Different quantile algorithms can return different values, especially in small datasets.

The method should be documented when reproducibility matters.

### Confusing relative position with quality

Being at the 90th percentile does not automatically mean good performance.

For a revenue metric, high may be favorable.

For a response-time metric, high may be unfavorable.

The metric's business meaning determines interpretation.

## Limitations

Percentiles describe observed distributional position. They do not automatically explain why the distribution has that shape.

Percentiles also do not establish causality.

A high P95 response time indicates that slow observations exist, but it does not identify the technical cause.

Similarly, a salary at the 90th percentile does not establish whether compensation is fair.

Percentiles can also be unstable with very small samples.

For streaming or extremely large datasets, exact sorting may require substantial computational resources.

Approximate quantile algorithms may be more appropriate when exact calculations are impractical and small estimation errors are acceptable.

## Performance considerations

The educational implementation sorts the dataset before calculating a percentile.

Sorting generally requires O(n log n) time.

Once sorted, accessing a known percentile position is approximately O(1).

The current functions validate and sort their input independently, which is clear and safe for educational use but inefficient when many percentiles are requested from a very large dataset.

For repeated analysis, an optimized implementation can sort the dataset once and reuse the ordered representation.

For very large datasets, specialized quantile algorithms can reduce memory requirements or support approximate percentile estimation.

The appropriate implementation depends on:

- Dataset size
- Number of percentile queries
- Accuracy requirements
- Memory constraints
- Batch versus streaming processing
- Latency requirements

## Data quality and security considerations

Percentile analysis depends heavily on input quality.

Important controls include:

- Validate numerical observations.
- Define how missing values are handled.
- Detect impossible values.
- Monitor sudden changes in distribution.
- Preserve filtering rules.
- Preserve the percentile methodology.
- Restrict access to sensitive business data.
- Protect employee, customer, financial, and operational records.
- Keep analytical transformations reproducible.

Security problems are not usually caused by the percentile formula itself. They more commonly arise from poor handling of the underlying data.

A distribution report can also expose sensitive information when groups are very small. Aggregation and access controls should therefore be considered when percentile results are based on confidential populations.

## Production implementation considerations

A production percentile pipeline should define the complete analytical specification.

This should include:

- Dataset population
- Inclusion and exclusion rules
- Missing-value treatment
- Duplicate handling
- Weighting methodology
- Percentile definition
- Time period
- Sampling method
- Unit of measurement
- Outlier policy
- Rounding policy
- Refresh frequency

Without these definitions, two analysts can use the same raw data and produce different results while both appearing technically correct.

Production dashboards should also distinguish between exact and approximate percentile calculations.

## Testing and validation

The script contains tests for:

- P0
- P50
- P100
- Q1
- Q3
- IQR
- One-observation datasets
- Two-observation interpolation
- Empty datasets
- Invalid percentile values

Testing is important because statistical functions often appear simple while containing subtle boundary behavior.

A production implementation should also test:

- Missing values
- Duplicate values
- Large datasets
- Negative values
- Extreme values
- Different percentile methods
- Weighted observations
- Regression against a trusted statistical implementation

## Practical analytical workflow

A disciplined distribution-analysis workflow can be structured as follows:

1. Validate the dataset.
2. Define the business metric precisely.
3. Check the number of observations.
4. Order the observations or use an appropriate quantile implementation.
5. Calculate the median and quartiles.
6. Calculate the IQR.
7. Examine P90, P95, and P99 when tail behavior matters.
8. Compare mean and median.
9. Investigate skewness.
10. Identify potential outliers.
11. Investigate unusual observations rather than automatically deleting them.
12. Compare relevant business groups.
13. Document the percentile method.
14. Interpret the statistics according to the business meaning of the metric.
15. Monitor the distribution over time.

## Real-world applications

Percentiles and quartiles are widely applicable to business and technical analysis.

### Customer analytics

Percentiles can segment customers according to:

- Spending
- Orders
- Lifetime value
- Engagement
- Complaint frequency
- Purchase frequency

### Operations

They can describe:

- Delivery times
- Processing times
- Queue times
- Production duration
- Defect rates

### Technology

They can measure:

- API response time
- Page load time
- Query duration
- Error rates
- Resource utilization

### Finance

They can help analyze:

- Portfolio returns
- Loss distributions
- Transaction sizes
- Customer balances
- Risk exposures

Percentiles alone are not a substitute for formal risk models, but they provide useful descriptive information about observed distributions.

### Human resources

Percentiles can support:

- Salary benchmarking
- Performance distributions
- Tenure analysis
- Recruitment metrics
- Absence analysis

### Marketing

Percentiles can describe:

- Customer acquisition cost
- Campaign response
- Conversion values
- Revenue per customer
- Engagement levels

## Interpreting percentiles responsibly

A percentile is always relative to a defined population.

If a customer's annual spending is at the 90th percentile of one dataset, that statement is meaningful only in relation to that population.

Changing the population can change the percentile rank.

For example, an employee can be at the 80th percentile within one department but at the 60th percentile across the entire company.

The reference population must therefore be clearly defined.

## Relationship between quartiles and business decisions

Quartiles are especially useful when businesses need simple distribution segmentation.

The bottom quartile can represent lower observed values.

The second quartile represents values between Q1 and the median.

The third quartile represents values between the median and Q3.

The top quartile represents the highest observed quarter.

This can create understandable management segments without assuming that the underlying variable follows a normal distribution.

## Distribution analysis without assuming normality

One of the strengths of percentiles and quartiles is that they do not require the dataset to be normally distributed.

A business dataset may be:

- Right-skewed
- Left-skewed
- Heavy-tailed
- Multimodal
- Discrete
- Highly concentrated
- A mixture of several populations

Percentile-based analysis remains useful in these situations because it describes observed positional structure rather than forcing the data into a particular theoretical distribution.

## Interpretation of tail percentiles

Tail percentiles deserve special attention in operational analysis.

P90 focuses on the upper 10% of observations.

P95 focuses on the upper 5%.

P99 focuses on the upper 1%.

For metrics where lower is better, such as latency or processing time, these upper-tail percentiles often represent undesirable performance.

For metrics where higher is better, such as revenue or customer value, the same percentiles may represent desirable high-performing segments.

Therefore, the numerical percentile must always be interpreted together with the direction and purpose of the metric.
