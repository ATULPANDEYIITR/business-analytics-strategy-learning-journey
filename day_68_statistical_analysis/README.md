# Statistical Analysis Using Python

## Project Description

This project implements statistical calculations across Python, JavaScript, C++17, Java 17, and PostgreSQL.

The implementations use examination scores and study-performance observations to demonstrate how numerical datasets can be validated, summarized, compared, modeled, and evaluated.

The project covers descriptive statistics, measures of dispersion, frequency distributions, correlation, regression, confidence intervals, bootstrap estimation, and outlier detection.

Each implementation is independently executable and uses its language's standard capabilities.

## Learning Objectives

- Calculate descriptive statistical measures.
- Distinguish sample statistics from population statistics.
- Understand the behavior of numerical distributions.
- Measure variability and dispersion.
- Calculate quartiles and percentiles.
- Construct frequency distributions.
- Identify potential outliers.
- Evaluate relationships between numerical variables.
- Fit simple linear regression models.
- Estimate confidence intervals.
- Apply bootstrap resampling.
- Validate numerical observations.
- Store and retrieve statistical results using PostgreSQL.

## Statistical Foundations

### Population and Sample

A population represents the complete collection of observations under investigation.

A sample represents a subset of that population.

For example:

- Population: All students enrolled in an institution.
- Sample: Students selected from different departments for an examination-performance study.

The distinction matters because population calculations and sample estimates use different denominators.

| Characteristic | Population | Sample |
|---|---|---|
| Mean | Population mean | Sample mean |
| Variance denominator | N | n - 1 |
| Standard deviation | Population standard deviation | Sample standard deviation |
| Purpose | Describe complete population | Estimate population characteristics |

### Mean

The arithmetic mean represents the average value.

\[
\bar{x}=\frac{\sum_{i=1}^{n}x_i}{n}
\]

Where:

- \(x_i\) represents an observation.
- \(n\) represents the number of observations.
- \(\bar{x}\) represents the arithmetic mean.

The mean is sensitive to unusually large or small observations.

### Median

The median is the middle observation after sorting the dataset.

For an odd number of observations:

\[
Median=x_{\frac{n+1}{2}}
\]

For an even number of observations:

\[
Median=
\frac{x_{\frac{n}{2}}+x_{\frac{n}{2}+1}}{2}
\]

The median is less sensitive to extreme observations than the mean.

### Mode

The mode represents the most frequently occurring observation.

A dataset can have:

- One mode.
- Multiple modes.
- No uniquely occurring mode.

The implementations preserve multiple values when frequencies are tied.

### Range

The range measures the difference between the maximum and minimum observations.

\[
Range=X_{\max}-X_{\min}
\]

It provides a simple measure of dispersion but is highly sensitive to extreme values.

## Measures of Dispersion

### Population Variance

Population variance measures the average squared deviation from the population mean.

\[
\sigma^2=
\frac{\sum_{i=1}^{N}(x_i-\mu)^2}{N}
\]

### Sample Variance

Sample variance estimates population variability using the sample observations.

\[
s^2=
\frac{\sum_{i=1}^{n}(x_i-\bar{x})^2}{n-1}
\]

The denominator \(n-1\) is the degrees-of-freedom adjustment used for the unbiased sample variance estimator under independent sampling with finite variance.

### Standard Deviation

Standard deviation is the square root of variance.

Population standard deviation:

\[
\sigma=\sqrt{\sigma^2}
\]

Sample standard deviation:

\[
s=\sqrt{s^2}
\]

Standard deviation is expressed in the same measurement units as the original observations.

A smaller standard deviation indicates that observations are more concentrated around their mean.

## Quartiles and Percentiles

Quartiles divide an ordered dataset into four sections.

| Measure | Meaning |
|---|---|
| Q1 | 25th percentile |
| Q2 | 50th percentile |
| Q3 | 75th percentile |
| IQR | Q3 minus Q1 |

The interquartile range is:

\[
IQR=Q3-Q1
\]

Percentiles describe the position of observations within a distribution.

For example, the 90th percentile represents a value at or below which approximately 90% of observations fall.

The Python, JavaScript, C++, and Java implementations use linear interpolation between neighboring ordered observations.

The PostgreSQL implementation uses `percentile_cont`, which calculates continuous percentiles through interpolation.

## Frequency Distribution

A frequency distribution records how often each distinct observation occurs.

Example:

| Examination score | Frequency |
|---:|---:|
| 60 | 1 |
| 70 | 1 |
| 72 | 2 |
| 80 | 1 |
| 90 | 1 |

Relative frequency expresses the frequency as a proportion of the total observations.

\[
Relative\ Frequency=
\frac{Frequency}{Total\ Observations}
\]

Percentage frequency is:

\[
Percentage=Relative\ Frequency\times100
\]

Frequency distributions help identify repeated values and the concentration of observations.

## Outlier Detection

An outlier is an observation that differs substantially from the general pattern of a dataset.

This project uses the interquartile range method.

Lower boundary:

\[
L=Q1-1.5(IQR)
\]

Upper boundary:

\[
U=Q3+1.5(IQR)
\]

An observation is flagged when:

\[
x<L \quad \text{or} \quad x>U
\]

The method identifies potential outliers, not necessarily incorrect measurements.

An extreme examination score may be legitimate. Outlier classification should therefore be separated from automatic deletion.

The PostgreSQL implementation preserves observations and supports quality classifications:

- `valid`
- `suspected_outlier`
- `excluded`

Only observations classified as `valid` participate in the implemented database calculations.

## Covariance and Correlation

### Covariance

Covariance measures how two numerical variables change together.

Sample covariance:

\[
Cov(X,Y)=
\frac{
\sum_{i=1}^{n}(x_i-\bar{x})(y_i-\bar{y})
}{n-1}
\]

Interpretation:

- Positive covariance: Variables tend to move in the same direction.
- Negative covariance: Variables tend to move in opposite directions.
- Near-zero covariance: No strong linear co-movement is indicated.

Covariance depends on measurement units and is difficult to compare across differently scaled datasets.

### Pearson Correlation

Pearson correlation standardizes covariance.

\[
r=
\frac{Cov(X,Y)}{s_Xs_Y}
\]

Its value ranges from -1 to +1.

| Correlation | Interpretation |
|---|---|
| +1 | Perfect positive linear relationship |
| 0 | No linear correlation |
| -1 | Perfect negative linear relationship |

A positive correlation between study hours and examination performance indicates that higher study hours tend to accompany higher examination scores.

Correlation does not establish causation.

The implementations reject correlation calculations when either dataset has zero variance.

## Simple Linear Regression

Linear regression models the relationship between an independent variable and a dependent variable.

The simple linear regression equation is:

\[
Y=\beta_0+\beta_1X+\epsilon
\]

Where:

- \(Y\) is the dependent variable.
- \(X\) is the independent variable.
- \(\beta_0\) is the intercept.
- \(\beta_1\) is the slope.
- \(\epsilon\) represents the residual error.

The estimated slope is:

\[
\beta_1=
\frac{
\sum(x_i-\bar{x})(y_i-\bar{y})
}{
\sum(x_i-\bar{x})^2
}
\]

The intercept is:

\[
\beta_0=\bar{y}-\beta_1\bar{x}
\]

### Coefficient of Determination

The coefficient of determination is:

\[
R^2=1-\frac{SS_{res}}{SS_{tot}}
\]

Where:

- \(SS_{res}\) is the residual sum of squares.
- \(SS_{tot}\) is the total sum of squares.

R-squared measures the proportion of observed variation explained by the fitted linear model.

A higher R-squared does not automatically establish that a model is appropriate or that its predictions are reliable.

## Confidence Intervals

A confidence interval provides a range of plausible values for an unknown population parameter under a specified statistical procedure.

The implementations provide a 95% normal-approximation interval for the population mean:

\[
CI=\bar{x}\pm1.96\frac{s}{\sqrt{n}}
\]

Where:

- \(\bar{x}\) is the sample mean.
- \(s\) is the sample standard deviation.
- \(n\) is the sample size.

The multiplier 1.96 corresponds approximately to a two-sided 95% standard normal interval.

This is an approximation. For small samples with unknown population variance, a Student's t critical value is generally more appropriate.

The confidence interval describes the uncertainty of the estimated mean, not the range containing 95% of individual observations.

## Bootstrap Resampling

Bootstrap resampling estimates sampling uncertainty by repeatedly drawing observations with replacement from the original sample.

The implemented procedure:

1. Accepts a validated numerical dataset.
2. Creates a resampled dataset of the original sample size.
3. Samples observations with replacement.
4. Calculates the mean of each resampled dataset.
5. Repeats the procedure for the specified number of iterations.
6. Sorts the resulting estimates.
7. Calculates the 2.5th and 97.5th percentiles.

The percentile bootstrap interval is:

\[
CI_{bootstrap}=
[P_{2.5},P_{97.5}]
\]

Bootstrap estimates are useful when analytical sampling distributions are difficult to derive.

They do not correct biased or unrepresentative original samples. Their reliability depends on the sampling design and the information contained in the observed data.

## Dataset Used in the Implementations

### Examination Performance

The examination dataset contains 24 numerical observations.

It includes:

- Repeated scores.
- Low and high observations.
- A deliberately extreme value.
- Sufficient observations for descriptive calculations.
- Values suitable for quartile and outlier analysis.

The value 150 is retained as an observation so that the IQR method can identify whether it is unusually distant from the central distribution.

### Study Hours and Performance

A second dataset contains paired observations of study hours and examination performance.

The paired observations support:

- Covariance.
- Pearson correlation.
- Regression slope.
- Regression intercept.
- R-squared.

Paired records must maintain their original ordering because each study-hours observation corresponds to a particular performance observation.

## Python Implementation

The Python implementation is structured around two principal classes.

### StatisticalMeasure

Provides individual statistical operations:

- `mean()`
- `median()`
- `mode()`
- `variance()`
- `standard_deviation()`
- `percentile()`
- `quartiles()`
- `frequency()`
- `covariance()`
- `correlation()`
- `regression()`
- `outliers()`
- `mean_confidence_interval()`

Python's `statistics` module provides established implementations for fundamental calculations.

### StatisticalAnalyzer

Combines the individual calculations into an `AnalysisReport` dataclass.

The report stores:

- Observation count.
- Central tendency measures.
- Minimum and maximum.
- Variance and standard deviation.
- Quartiles.
- Frequency distribution.
- Outliers.
- Mean confidence interval.

### CSVHandler

Supports importing numerical columns from CSV files and exporting analysis results to JSON.

It validates column names, numeric conversions, and finite values.

### Bootstrap Function

The standalone `bootstrap_mean()` function performs reproducible bootstrap estimation using a seeded random number generator.

### Validation and Error Handling

Custom exceptions distinguish insufficient observations from invalid numerical input.

NaN, infinity, Boolean values, and non-numeric observations are rejected.

## JavaScript Implementation

The JavaScript implementation uses Node.js capabilities to organize statistical processing around services and asynchronous workflows.

### DataValidator

Validates numerical arrays and paired datasets.

It prevents invalid observations from reaching calculation methods.

### Statistics

Implements calculations using:

- Array operations.
- `Map` for frequency distributions.
- Numerical interpolation.
- Reduction operations.
- Explicit regression calculations.

### BootstrapAnalyzer

Implements seeded resampling with a deterministic pseudo-random number generator.

The same seed and input produce reproducible bootstrap results.

### AnalysisService

Extends `EventEmitter` and provides event-driven analysis.

It emits:

- `analysisStarted`
- `analysisCompleted`
- `analysisFailed`

Completed reports are stored in a `Map`, allowing retrieval by dataset name.

### CSVReader and Report Export

`CSVReader` demonstrates asynchronous file reading through Node.js filesystem promises.

Report export uses asynchronous JSON writing.

The CSV parser is intentionally limited to simple comma-separated numerical files without quoted fields containing commas. Production CSV ingestion should use a fully compliant parser.

## C++17 Implementation

The C++17 program uses explicit numerical operations and STL containers.

### StatisticalEngine

The main calculation class implements:

- Mean.
- Median.
- Percentiles.
- Sample and population variance.
- Standard deviation.
- Frequency distribution.
- Mode.
- Quartiles.
- IQR outlier detection.
- Covariance.
- Pearson correlation.
- Linear regression.
- Confidence intervals.

### StatisticalReport

A structure groups calculated measures into a single report.

### BootstrapAnalyzer

Uses `std::mt19937` and a uniform integer distribution for reproducible resampling.

The vector of bootstrap estimates is sorted to calculate percentile boundaries.

### Error Handling

`StatisticalException` represents invalid statistical operations.

The program validates sample sizes, finite observations, paired dataset lengths, and zero-variance conditions.

## Java 17 Implementation

The Java implementation uses an enterprise-oriented service architecture.

### Domain Types

The application defines:

- `Dataset`
- `StatisticalReport`
- `RegressionResult`
- `ConfidenceInterval`
- `AnalysisStatus`

Records provide structured immutable data objects.

### StatisticalPolicy

The policy interface separates dataset validation from calculation logic.

`DefaultStatisticalPolicy` checks:

- Dataset name.
- Measurement unit.
- Observation count.
- Numerical validity.
- Maximum configured dataset size.

### StatisticalService

Centralizes calculation methods and report management.

The service maintains explicit analysis states:

`CREATED → VALIDATING → PROCESSING → COMPLETED`

A processing error changes the state to `FAILED`.

Completed reports are indexed by dataset name.

### BootstrapService

Provides a separate service for bootstrap estimation.

This separation allows descriptive analysis and resampling to be tested independently.

## PostgreSQL Implementation

The PostgreSQL implementation models statistical processing as a relational workflow.

### Database Schema

The `statistical_analysis` schema contains five principal tables.

| Table | Responsibility |
|---|---|
| `datasets` | Dataset metadata and processing status |
| `observations` | Individual numerical observations |
| `analysis_runs` | Analysis execution history |
| `statistical_results` | Stored statistical results |
| `observation_frequency` | Frequency distribution view |

The `statistical_outliers` view identifies observations outside the IQR boundaries.

### Relational Structure

`datasets`

→ `observations`

→ `analysis_runs`

→ `statistical_results`

Each observation belongs to a dataset.

Each analysis run belongs to a dataset.

Each stored statistical result belongs to an analysis run.

### Database Constraints

The schema enforces:

- Primary key uniqueness.
- Foreign key relationships.
- Non-empty dataset names.
- Non-empty measurement units.
- Valid numerical ranges.
- Unique subject references within datasets.
- Valid sample sizes.
- Valid outlier counts.
- Valid analysis timestamps.

### PostgreSQL Statistical Functions

The database uses built-in aggregate and ordered-set functions.

| Function | Purpose |
|---|---|
| `AVG()` | Arithmetic mean |
| `MIN()` | Minimum observation |
| `MAX()` | Maximum observation |
| `VAR_SAMP()` | Sample variance |
| `VAR_POP()` | Population variance |
| `STDDEV_SAMP()` | Sample standard deviation |
| `STDDEV_POP()` | Population standard deviation |
| `CORR()` | Pearson correlation |
| `REGR_SLOPE()` | Regression slope |
| `REGR_INTERCEPT()` | Regression intercept |
| `PERCENTILE_CONT()` | Continuous percentile |
| `COUNT()` | Observation count |

### Stored Functions

The SQL script defines functions for:

- Descriptive statistics.
- Correlation.
- Regression.
- Mean confidence intervals.

These functions centralize statistical calculations within the database.

### Stored Procedure

`process_dataset()` performs an analysis workflow.

Its operations include:

1. Validating dataset existence.
2. Creating an analysis-run record.
3. Updating processing status.
4. Calculating descriptive statistics.
5. Detecting outliers.
6. Persisting results.
7. Updating completion status.

An exception records the failure state and re-raises the error.

Because the procedure executes within its caller's transaction, an unhandled error still causes the enclosing transaction to fail. The caller must roll back appropriately when necessary.

### Database Indexing

The schema includes indexes on:

- Dataset identifiers.
- Dataset and observation values.
- Observation timestamps.
- Analysis history.
- Stored analysis results.

These indexes support common filtering and reporting operations.

## Execution Instructions

### Python

Save the first implementation as `statistical_analysis.py`.

Run:

`python statistical_analysis.py`

The script uses the Python standard library and creates `statistical_report.json`.

### JavaScript

Save the second implementation as `statistical_analysis.js`.

Run:

`node statistical_analysis.js`

Node.js standard-library modules are sufficient.

### C++17

Save the third implementation as `statistical_analysis.cpp`.

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic statistical_analysis.cpp -o statistical_analysis`

Run:

`./statistical_analysis`

On Windows:

`statistical_analysis.exe`

### Java 17

Save the fourth implementation as `StatisticalAnalysis.java`.

Compile:

`javac StatisticalAnalysis.java`

Run:

`java StatisticalAnalysis`

### PostgreSQL

Save the fifth implementation as `statistical_analysis.sql`.

Execute:

`psql -U postgres -d your_database -f statistical_analysis.sql`

The database must exist before execution.

The script creates its own schema and objects. It is designed for a fresh installation of the project schema and does not drop existing objects.

## Validation and Edge Cases

The implementations explicitly address the following situations:

| Condition | Expected behavior |
|---|---|
| Empty dataset | Reject calculation |
| Insufficient sample size | Raise an error |
| NaN observation | Reject input |
| Infinite observation | Reject input |
| Non-numeric observation | Reject input |
| Unequal paired datasets | Reject calculation |
| Constant independent variable | Reject regression |
| Constant correlation variable | Reject correlation |
| Invalid percentile | Reject calculation |
| Invalid bootstrap iteration count | Reject estimation |
| Repeated observations | Preserve frequency information |
| Multiple modes | Return all highest-frequency values |
| Extreme observations | Flag using IQR boundaries |

## Statistical and Computational Limitations

### Numerical Precision

Floating-point calculations may introduce small rounding differences across programming languages.

PostgreSQL uses `NUMERIC` for stored observations and results, while the application implementations use floating-point arithmetic.

Small differences in the last decimal places are expected.

### Percentile Conventions

Different statistical packages may use different percentile definitions.

The implementations use continuous linear interpolation, while Python's quartile calculation uses its documented inclusive method.

Results should therefore be compared using the same percentile convention.

### Confidence Interval Approximation

The 1.96 multiplier assumes a normal approximation.

For small samples, a t-distribution-based interval should generally be preferred.

### Bootstrap Limitations

Bootstrap resampling depends on the quality of the original sample.

A biased sample or a sample that does not represent the target population can produce misleading intervals.

### Regression Limitations

Simple linear regression models one independent variable.

The implementation does not automatically test:

- Residual normality.
- Homoscedasticity.
- Independence of errors.
- Influential observations.
- Multicollinearity.
- Nonlinear relationships.

These assumptions must be considered before interpreting regression results.

### Scalability

For a dataset containing \(n\) observations:

| Operation | Typical time complexity |
|---|---|
| Mean | O(n) |
| Variance | O(n) |
| Standard deviation | O(n) |
| Median | O(n log n) |
| Percentile | O(n log n) |
| Frequency distribution | O(n log k) with ordered maps |
| Covariance | O(n) |
| Correlation | O(n) |
| Linear regression | O(n) |
| Outlier detection | O(n log n) |
| Bootstrap | O(B × n) |

Here:

- \(n\) is the number of observations.
- \(k\) is the number of distinct values.
- \(B\) is the number of bootstrap iterations.

Sorting-based methods can be optimized using selection algorithms when only one order statistic is required.

## Security and Data Integrity

Statistical processing should preserve the integrity and confidentiality of source observations.

The implementations apply the following controls:

- Validate numerical input before calculation.
- Reject non-finite values.
- Avoid dynamically constructed SQL statements.
- Use database constraints for data integrity.
- Preserve original observations during outlier classification.
- Use deterministic seeds for reproducible simulations.
- Limit configured bootstrap iterations.
- Avoid logging sensitive individual-level observations unnecessarily.

Production deployments should also implement appropriate database permissions, encryption, access auditing, backup policies, and data-retention controls.

## Practical Applications

The implemented calculations support several analytical activities.

| Application | Statistical techniques |
|---|---|
| Examination performance | Mean, median, mode, variance |
| Student performance analysis | Correlation and regression |
| Quality monitoring | Standard deviation and outliers |
| Business performance | Percentiles and frequency |
| Operational monitoring | Confidence intervals |
| Research sampling | Bootstrap estimation |
| Database reporting | Aggregation and statistical functions |

The implementations demonstrate how the same statistical concepts can be represented through Python's statistical library, JavaScript's event-driven architecture, C++ numerical processing, Java enterprise services, and PostgreSQL analytical functions.
