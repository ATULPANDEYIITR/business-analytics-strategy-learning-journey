# Exploratory Data Analysis: Finding Patterns, Trends and Anomalies

## Analytical scope

Exploratory Data Analysis, or EDA, is the process of examining data before formal modeling so that its structure, distribution, relationships, trends, and unusual observations become visible. The central purpose is not simply to calculate averages. EDA combines descriptive statistics, grouping, temporal aggregation, trend estimation, anomaly detection, and validation to determine what the data is actually doing.

This project uses a realistic operational measurement dataset containing dates, numeric measurements, regions, and business categories. The same analytical problem is approached differently in Python, JavaScript, C++, Java, and PostgreSQL.

The four central analytical questions are distinct:

- **Distribution:** What is typical, how dispersed are the observations, and how asymmetric or extreme is the data?
- **Patterns:** How do observations differ across dimensions such as region and category?
- **Trends:** Does the measured quantity systematically increase, decrease, or change over time?
- **Anomalies:** Which observations are unusual relative to the complete dataset or to their local temporal neighborhood?

A strong EDA workflow keeps these questions separate. A high value is not automatically an anomaly, and a statistically unusual observation is not automatically an error.

## Data model

The analytical records contain four important attributes:

| Field | Analytical role |
|---|---|
| `timestamp` or `observed_at` | Establishes temporal order and enables time-series analysis |
| `value` or `metric_value` | Numeric measurement being explored |
| `region` | Categorical dimension for comparing populations |
| `category` | Second categorical dimension for segmentation |

The generated data contains a gradual change over time and intentionally includes unusual observations. These features make it possible to demonstrate the difference between an underlying trend and isolated deviations.

The database representation also records `metric_name` and `source_system`. These fields allow multiple measurements and data sources to coexist without assuming that every numeric value belongs to the same analytical population.

## Descriptive statistics

The Python, Java, and SQL implementations calculate the mean, median, minimum, maximum, quartiles, interquartile range, and standard deviation.

The mean is sensitive to extreme values. If one observation is exceptionally large, it can pull the mean upward. The median is based on ordering and is therefore more resistant to isolated extremes.

The first quartile, `Q1`, describes the lower portion of the distribution and the third quartile, `Q3`, describes the upper portion. Their difference is the interquartile range:

`IQR = Q3 - Q1`

The IQR describes the spread of the middle half of the observations. It is particularly useful for robust anomaly detection because it does not depend directly on the most extreme values.

The standard deviation measures dispersion around the mean. It is useful when the distribution and measurement process make a deviation-based interpretation appropriate, but it should not automatically be treated as a universal anomaly rule.

## Finding patterns through segmentation

A dataset can hide important structure when all observations are summarized together.

The Python implementation groups measurements by category and region. The JavaScript implementation uses `Map` objects and a reusable aggregation function. The Java implementation uses `Collectors.groupingBy` and `averagingDouble`, which expresses the aggregation directly as a domain operation. The C++ implementation stores grouped values in ordered maps and computes group-specific means.

These calculations answer questions such as whether one region has consistently higher measurements or whether a category has a different baseline from another category.

A group comparison should be interpreted together with sample size and dispersion. A higher mean alone does not establish that one population is inherently better or worse. The difference may reflect composition, seasonality, measurement practices, or another variable.

## Time-series trends

Temporal order matters because observations that occur close together can have relationships that disappear when the records are shuffled.

The implementations calculate a linear trend using the least-squares slope. A positive slope indicates that the fitted line increases as the observation index advances. A negative slope indicates a decreasing fitted line.

The slope is a compact description of direction, not proof of causation. A positive trend does not explain why the metric increased.

The Python and JavaScript implementations also calculate moving averages. A seven-observation moving average reduces short-term variation and makes a broader direction easier to inspect:

`moving_average(t) = mean(value[t-6], ..., value[t])`

The moving average is a smoothing operation. It does not create additional information and can hide short-lived events when the window is too large.

## Change detection

A useful EDA technique is to compare consecutive observations rather than only looking at absolute values.

The SQL implementation uses `LAG` to obtain the previous observation and calculates both absolute and percentage changes. This can reveal abrupt movements even when the absolute scale of the metric changes over time.

Percentage change needs special treatment when the previous value is zero or close to zero. Dividing by zero is invalid, while division by a very small baseline can produce a very large percentage that may not represent a meaningful operational change.

## Global anomaly detection

The IQR method defines lower and upper analytical fences:

`lower = Q1 - 1.5 × IQR`

`upper = Q3 + 1.5 × IQR`

An observation outside those boundaries is classified as an IQR outlier.

This method is useful because it is based on the distribution rather than assuming that the data is normally distributed.

The SQL implementation calculates quartiles with PostgreSQL's `percentile_cont`, creates the corresponding limits, and joins the limits back to the observations. The Python, C++, and Java implementations perform the same analytical idea in application code.

An IQR outlier is a candidate for investigation. It should not automatically be deleted. A genuine business event, system migration, unusual demand period, sensor failure, or data-entry error can all produce extreme values.

## Local anomaly detection

A global rule can miss an important class of anomaly.

Suppose a metric normally increases from 100 to 200 over several months. A value of 190 might not be globally unusual, but if the surrounding observations are approximately 150, that value can still represent a sudden local event.

The implementations therefore include local anomaly detection. For each observation, a neighborhood is constructed around its position. The observation is compared with the mean and standard deviation of nearby observations.

The local score is:

`local_z = |value - local_mean| / local_standard_deviation`

A threshold such as `2.5` identifies unusually large local deviations.

The local method and IQR method answer different questions. IQR asks whether a value is unusual relative to the overall distribution. Local scoring asks whether it is unusual relative to nearby observations.

## Python implementation

The Python program provides the most complete exploratory workflow.

`Observation` is an immutable dataclass representing an analytical record. Validation occurs when CSV records are converted into observations, preventing non-finite values and missing analytical dimensions from silently entering the analysis.

The script implements:

- Robust mean and median calculations that reject empty analytical populations.
- Percentile and quartile calculation.
- Sample standard deviation.
- IQR-based outlier detection.
- Standardized scores.
- Local neighborhood anomaly detection.
- Linear trend estimation.
- Moving averages.
- Grouped analysis by region and category.
- Period-to-period comparison.
- Correlation between aligned analytical series.
- CSV loading and validation.
- CSV output of the generated observations.

The generated dataset contains seasonal variation, gradual growth, random variation, and deliberately unusual regional-category observations. This allows global and local anomaly detection to be observed under different conditions.

The correlation calculation is intentionally applied to aligned daily series rather than arbitrary lists. Correlation requires paired observations with a meaningful correspondence between positions.

## JavaScript implementation

The JavaScript program treats EDA as an event-oriented analytical workflow.

`validateObservation` converts external record values into validated analytical objects. This is important in JavaScript because external data commonly arrives as strings, objects, or other dynamically typed values.

`Map` is used for grouping because it provides an explicit key-to-collection structure suitable for analytical dimensions such as region, category, and date.

The `AnomalyMonitor` class extends Node.js `EventEmitter`. Instead of only returning a list of anomalies, it emits an `anomaly` event whenever a local analytical threshold is crossed. This models a practical monitoring architecture in which anomaly detection can feed logging, alerting, dashboards, or downstream processing.

The JavaScript implementation also demonstrates asynchronous file output using `fs/promises`. The generated analytical dataset is written to CSV without requiring a third-party package.

The JavaScript implementation deliberately differs from the Python design. Its important focus is event-driven processing, dynamic input validation, `Map`-based aggregation, asynchronous output, and event emission.

## C++ case study

The C++ program treats EDA as a performance-oriented analytical service.

`GovernanceAnalytics` owns the observation collection and exposes analytical operations through methods. The implementation uses `std::vector` for ordered numerical data and `std::map` for grouped dimensions.

The percentile calculation sorts a copy of the numerical values, which keeps the original observation order intact. This matters because temporal order can be analytically meaningful even when a distribution statistic requires sorted values.

The program calculates distribution statistics, regional and category means, IQR outliers, linear trend slope, and local anomalies.

The case study demonstrates an important systems-level distinction between global and local anomaly detection. A value may be extreme compared with the complete population while another value may be normal globally but unusual relative to its immediate neighbors.

The C++ implementation validates finite numeric values and required dimensions before analysis. Exceptions are caught at the application boundary so invalid analytical data produces an explicit failure rather than undefined behavior.

For the main operations, grouping is approximately linear in the number of observations aside from the cost of sorting when percentile-based analysis is performed. IQR detection depends on percentile computation, while local anomaly detection is proportional to the number of observations multiplied by the neighborhood size in the straightforward implementation.

## Java implementation

The Java implementation models EDA as an enterprise-oriented analytical service.

`Observation` is a Java record, making the domain data immutable and explicit. Its compact constructor validates required fields and rejects non-finite numeric measurements.

`Dimension` identifies the supported analytical grouping dimensions. This is preferable to passing arbitrary strings throughout a domain service because invalid dimensions can be constrained at the type level.

`AnomalyMethod` distinguishes IQR detection from local z-score detection. The `Anomaly` record retains both the source observation and the method that produced the analytical finding.

`AnalysisService` owns the analytical workflow. Java Streams are used where grouping and aggregation naturally correspond to collection operations, while explicit loops are retained for local anomaly detection and trend calculations where they make the algorithm easier to inspect.

The service provides:

- Distribution statistics.
- Regional means.
- Category means.
- IQR anomaly detection.
- Local z-score anomaly detection.
- Daily aggregation.
- Trend slope estimation.
- Identification of the category with the highest mean.

The type structure prevents different analytical concepts from being collapsed into one generic status value.

## PostgreSQL data model

The SQL implementation represents the analytical dataset relationally.

The `observations` table uses `observation_id` as the primary key and requires a date, metric name, finite numeric measurement, region, category, and source system.

Database constraints reject invalid empty dimensions and non-finite numeric values. This demonstrates an important EDA principle: data quality controls should not exist exclusively in application code when the database can enforce the same invariant consistently for every client.

The indexes support common analytical access paths:

- `(metric_name, observed_at)` supports metric-specific time-series queries.
- `(region, category)` supports dimensional segmentation.
- `(observed_at, metric_value)` supports temporal and value-oriented access.

The `descriptive_statistics` view calculates distribution metrics. `daily_statistics` provides time-based aggregation. `regional_patterns` exposes dimensional comparisons.

The `iqr_anomalies` view calculates quartiles and derives analytical fences directly in PostgreSQL. This makes the anomaly rule reproducible and queryable without exporting the data to an application first.

## Window functions and temporal analysis

The SQL workflow uses `LAG` to compare an observation with its previous observation. This is particularly appropriate for time-series EDA because the database can preserve ordering and calculate changes without procedural application code.

The moving-average query uses a window frame:

`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`

This creates a seven-observation rolling calculation. Window functions are useful in EDA because they preserve individual rows while adding contextual calculations.

The trend query uses PostgreSQL regression functions. `regr_slope` estimates the slope of the relationship between the measurement and elapsed time. Converting the slope to an estimated daily change makes the result easier to interpret.

## Relationships among patterns, trends, and anomalies

These analytical categories should not be treated as interchangeable.

A **pattern** describes structured differences between groups or dimensions. For example, one region may have a consistently higher mean.

A **trend** describes directional movement through time. A metric can have a positive trend even when individual observations fluctuate substantially.

An **anomaly** identifies an observation that deviates from a chosen reference distribution or local context.

These can interact. A regional pattern can create apparent global anomalies if groups have substantially different baselines. A trend can cause early and late observations to have different distributions. Seasonality can make a recurring high value appear anomalous under a simplistic global rule.

Good EDA therefore asks whether the reference population and analytical context are appropriate before labeling an observation as abnormal.

## Common analytical failure modes

### Treating missing values as zero

A missing measurement means the value was not observed or was unavailable. Replacing it with zero changes the distribution and can create an artificial downward pattern.

### Treating every outlier as bad data

An outlier is an observation that deserves investigation. It may represent a valid rare event rather than an error.

### Using only the mean

The mean can hide skewness and extreme observations. Median, quartiles, range, and standard deviation provide complementary information.

### Ignoring temporal order

A dataset can have the same distribution after shuffling but lose the information required to identify trends, changes, and local anomalies.

### Confusing correlation with causation

A strong correlation indicates that two variables move together in the observed data. It does not establish that one variable causes the other.

### Using an inappropriate anomaly threshold

A threshold should reflect the measurement process and the analytical question. A fixed z-score or IQR rule should not be treated as universally correct.

### Aggregating too early

Averaging data across all dimensions can erase subgroup behavior. Analysis should preserve dimensions that are important to the underlying question.

## Practical interpretation

EDA should produce questions and evidence, not merely tables of numbers.

If a regional mean differs substantially, the next analytical question is why the populations differ. If a trend changes direction, the temporal location of the change should be examined. If an anomaly appears, its source record and neighboring observations should be inspected before any correction is made.

The implementations deliberately retain the original observations while producing derived analytical views. This preserves traceability between a statistical finding and the underlying record.

## Performance considerations

Sorting is the major cost of straightforward percentile and IQR calculations. For `n` observations, sorting requires approximately `O(n log n)` time.

Mean, standard deviation, grouping, and simple scans are generally `O(n)` for one pass through the dataset.

A moving average can be calculated in `O(n)` time using a rolling sum. The educational implementations use direct window aggregation because the mechanism is clearer, while production-scale implementations can use incremental rolling state.

Local anomaly detection with a window of width `w` is approximately `O(nw)` in the straightforward implementation. When `w` is small and fixed, this behaves close to linear time. Large windows require more careful implementation.

Database indexes can substantially improve filtering and ordering operations, but indexes also increase storage and write cost. Index selection should therefore follow actual query patterns rather than creating an index for every column.

## Data quality and validation

EDA results are only as reliable as the analytical population.

The implementations reject non-finite numeric values and require meaningful categorical dimensions. PostgreSQL enforces corresponding constraints at the database layer.

Additional production validation would normally examine duplicate records, impossible dates, inconsistent units, missing periods, unexpected category values, source-system changes, and changes in measurement methodology.

A particularly important issue is data drift. A distribution can change because the real process changed or because the way the data is collected changed. EDA should distinguish those possibilities before interpreting the change as a business trend.

## Production considerations

For large analytical datasets, the same concepts can be implemented with partitioned tables, columnar storage, incremental aggregates, materialized views, distributed processing, or streaming anomaly detection.

The core analytical definitions should remain explicit even when the implementation becomes more sophisticated. A production system should be able to explain how a trend, pattern, or anomaly was calculated, which records were included, which exclusions were applied, and which threshold produced the result.

Reproducibility is especially important for anomaly detection. A finding should retain its analytical method, threshold, reference population, timestamp, and source record so that investigators can reproduce the decision later.
