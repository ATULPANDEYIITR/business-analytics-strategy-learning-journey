# Exploratory Data Analysis

## 1. Introduction

Exploratory Data Analysis (EDA) is the systematic examination of a dataset before statistical modelling, hypothesis testing, or operational decision-making.

EDA identifies structural characteristics, data-quality problems, distributions, unusual observations, relationships between variables, and patterns that require further investigation.

The implementations in this project use an employee workforce dataset containing:

| Attribute | Description | Data type |
|---|---|---|
| employee_id | Employee identifier | Categorical |
| department | Organizational department | Categorical |
| salary | Annual salary | Numeric |
| experience | Years of professional experience | Numeric |
| rating | Employee performance rating | Numeric |

The dataset contains missing observations and a repeated record. These conditions make it suitable for demonstrating practical data profiling and quality assessment.

## 2. EDA workflow

The implementations follow this analytical workflow:

    Dataset acquisition
           |
           v
    Structural validation
           |
           v
    Schema and type inference
           |
           v
    Missing-value analysis
           |
           v
    Duplicate detection
           |
           v
    Descriptive statistics
           |
           v
    Distribution and outlier analysis
           |
           v
    Correlation analysis
           |
           v
    Grouped aggregation
           |
           v
    Data-quality assessment
           |
           v
    Analytical reporting

Each stage produces information that informs subsequent analysis.

## 3. Dataset acquisition and validation

Dataset acquisition establishes the source and structure of the observations.

The Python implementation supports CSV ingestion through `csv.DictReader`. It validates headers, rejects duplicate column names, checks row consistency, and handles file-access errors.

The JavaScript implementation uses asynchronous file access through Node.js `fs/promises`. Its CSV parser supports quoted fields, escaped quotation marks, commas inside quoted values, and multiline quoted records.

The C++ implementation uses an explicitly defined `Record` structure and a controlled sample dataset. This demonstrates a statically defined analytical schema.

The Java implementation uses an immutable `Employee` record to represent individual observations.

The PostgreSQL implementation separates dataset registration, column metadata, and observation storage into relational tables.

### Validation rules

- Column names must be non-empty and unique.
- Every observation must follow the dataset schema.
- Numeric values must be finite.
- Negative salary values are rejected by the database.
- Experience must be within the defined business range.
- Performance ratings must be between zero and five.
- Missing values must not be interpreted as numeric zero.

Structural validation and statistical quality assessment are different operations. A structurally valid dataset can still contain missing values, duplicated observations, or statistically unusual measurements.

## 4. Data types and schema inference

Type inference determines the most appropriate analytical treatment for each column.

| Data type | Characteristics | Analytical operations |
|---|---|---|
| Numeric | Quantitative values | Mean, median, variance, correlation |
| Categorical | Labels or groups | Frequency, mode, grouping |
| Boolean | Two logical states | Proportion and frequency |
| Date | Calendar observations | Minimum, maximum, temporal analysis |
| Empty | No usable observations | Missingness assessment |

The Python implementation supports numeric, categorical, boolean, date, and empty classifications.

The JavaScript implementation uses numeric, categorical, date, and empty classifications.

The C++ and Java implementations concentrate on the declared workforce schema and numeric extraction.

The PostgreSQL implementation stores declared column types separately from inferred analytical results.

Type inference should not replace domain validation. An employee identifier containing only digits, for example, may still be a categorical identifier rather than a quantitative measurement.

## 5. Missing-value analysis

Missingness occurs when an observation has no usable value for a particular variable.

The implementations recognize common representations:

- Empty strings
- `NA`
- `N/A`
- `NULL`
- `None`
- `NaN`
- `missing`

Missing-value counts and percentages are calculated independently for each column.

The missing percentage is:

\[
Missing\ Percentage =
\frac{Missing\ Observations}{Total\ Observations}
\times 100
\]

Missingness can affect analytical validity.

Three commonly used missing-data mechanisms are:

| Mechanism | Meaning |
|---|---|
| MCAR | Missing Completely At Random |
| MAR | Missing At Random conditional on observed variables |
| MNAR | Missingness depends on unobserved values or the missing value itself |

The implementations identify missing observations but do not automatically classify their underlying mechanism.

Potential treatments include deletion, statistical imputation, domain-specific replacement, and explicit missing-value indicators. The appropriate choice depends on the data-generating process and the analytical objective.

## 6. Duplicate detection

Duplicate observations can distort descriptive statistics, frequency distributions, and model training.

The implementations compare complete records and count repeated observations beyond their first occurrence.

The Python implementation uses tuples and a set.

The JavaScript implementation uses serialized records as keys in a `Set`.

The C++ implementation uses a set of serialized field combinations.

The Java implementation uses immutable record equality and a `HashSet`.

The PostgreSQL implementation groups observations using their complete analytical attributes and identifies groups containing multiple records.

Duplicate detection does not automatically justify deleting records. Repeated observations may represent legitimate repeated measurements, transactions, or events.

A production system should distinguish exact duplicates from business-key duplicates.

## 7. Descriptive statistics

Descriptive statistics summarize the central tendency and dispersion of numerical variables.

### 7.1 Mean

The arithmetic mean is:

\[
\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i
\]

It is sensitive to extreme observations.

### 7.2 Median

The median is the middle observation after sorting the data.

For an even number of observations, it is the average of the two middle values.

It is more resistant to extreme values than the mean.

### 7.3 Minimum and maximum

These identify the smallest and largest observed values.

Their difference is the range:

\[
Range = Maximum-Minimum
\]

### 7.4 Variance

Sample variance measures dispersion around the sample mean:

\[
s^2 =
\frac{\sum_{i=1}^{n}(x_i-\bar{x})^2}{n-1}
\]

### 7.5 Standard deviation

Sample standard deviation is:

\[
s=\sqrt{s^2}
\]

It expresses dispersion in the original measurement units.

### 7.6 Quartiles

Quartiles divide sorted observations into four approximately equal groups.

- Q1 represents the 25th percentile.
- Q2 represents the median.
- Q3 represents the 75th percentile.

The implementations use linear interpolation based on the position:

\[
Position=(n-1)p
\]

where \(p\) is the requested percentile expressed as a fraction.

Different statistical packages may use different quantile conventions. Results should therefore be interpreted with the selected convention in mind.

## 8. Distribution analysis and outliers

Distribution analysis examines how numerical observations are spread across their possible values.

The implementations calculate quartiles and the interquartile range.

\[
IQR=Q3-Q1
\]

The conventional IQR outlier boundaries are:

\[
Lower\ Bound=Q1-1.5(IQR)
\]

\[
Upper\ Bound=Q3+1.5(IQR)
\]

Observations outside these boundaries are flagged as potential outliers.

An outlier is not necessarily an erroneous observation.

For example, an unusually high salary could represent a legitimate executive compensation record. Outlier investigation should consider business context, measurement errors, population structure, and data provenance.

The IQR method is a screening mechanism rather than a definitive test of data validity.

## 9. Categorical frequency analysis

Categorical analysis examines the occurrence of distinct labels.

For the department variable, the implementations calculate:

- Distinct category counts
- Category frequencies
- Most frequent categories
- Department-level observation counts

Category frequency is:

\[
Frequency(c)=
\sum_{i=1}^{n}I(x_i=c)
\]

where \(I\) is an indicator function.

Category percentages can be calculated as:

\[
Category\ Percentage=
\frac{Category\ Frequency}{Total\ Valid\ Observations}
\times 100
\]

The PostgreSQL implementation provides a department distribution view with category counts and percentages.

## 10. Correlation analysis

Correlation measures the strength and direction of association between numerical variables.

The implementations calculate Pearson's correlation coefficient.

\[
r =
\frac{
\sum_{i=1}^{n}(x_i-\bar{x})(y_i-\bar{y})
}{
\sqrt{
\sum_{i=1}^{n}(x_i-\bar{x})^2
\sum_{i=1}^{n}(y_i-\bar{y})^2
}
}
\]

The coefficient ranges from -1 to +1.

| Coefficient | Interpretation |
|---|---|
| +1 | Perfect positive linear association |
| Between 0 and +1 | Positive linear association |
| 0 | No linear association |
| Between -1 and 0 | Negative linear association |
| -1 | Perfect negative linear association |

The workforce example evaluates the relationship between salary and experience.

Pairwise deletion is used when either variable is missing. This preserves the alignment of valid observations.

Correlation has important limitations:

- Correlation does not establish causation.
- Pearson correlation measures linear association.
- Extreme observations can influence the coefficient.
- Constant variables produce undefined correlation.
- Small sample sizes can produce unstable estimates.
- Confounding variables can create misleading relationships.

## 11. Grouped analysis

Grouped analysis evaluates a numerical variable across categories.

The implementations calculate salary statistics by department.

The principal measures are:

- Observation count
- Mean salary
- Median salary
- Minimum salary
- Maximum salary

This approach makes it possible to compare departments without treating the entire workforce as a homogeneous population.

Grouped analysis can be extended to multiple dimensions, such as department, employment type, location, and observation period.

Care must be taken to ensure that groups contain sufficient observations for meaningful comparisons.

## 12. Data-quality assessment

EDA should identify problems that can affect downstream analysis.

The implementations evaluate:

| Quality dimension | Detection mechanism |
|---|---|
| Completeness | Missing-value counts |
| Uniqueness | Duplicate detection |
| Consistency | Schema and type validation |
| Validity | Domain constraints |
| Distribution | Quartiles and outlier boundaries |
| Relationships | Correlation analysis |

The Java implementation models findings using `QualityIssue` and `QualitySeverity`.

The PostgreSQL implementation persists findings with severity classifications:

- `info`
- `warning`
- `critical`

These classifications distinguish informational observations from conditions requiring investigation.

A dataset can pass structural validation while still receiving multiple quality warnings.

## 13. Implementation architecture

### Python

The Python implementation uses:

- `Dataset` for data acquisition and validation.
- `ColumnProfile` for column-level results.
- `AnalysisReport` for structured output.
- `ExploratoryDataAnalyzer` for statistical operations.
- `argparse` for command-line configuration.
- `csv`, `statistics`, `json`, and `pathlib` for standard-library processing.

The report is written as JSON, making it suitable for subsequent automated processing.

### JavaScript

The JavaScript implementation emphasizes asynchronous execution and event-driven analysis.

Its principal components are:

- `CsvParser` for CSV parsing.
- `Dataset` for structured records.
- `Statistics` for statistical calculations.
- `EDAEngine` for analytical processing.
- `EventEmitter` for analysis lifecycle events.

The report-writing mechanism uses a temporary file followed by a rename operation to reduce the risk of exposing an incomplete report.

### C++17

The C++ implementation uses explicit domain structures and STL algorithms.

Its principal components are:

- `Record` for workforce observations.
- `Dataset` for dataset ownership.
- `Statistics` for numerical calculations.
- `NumericSummary` for statistical results.
- `EDAEngine` for analytical operations.

The implementation uses `vector` for sequential observations, `map` for ordered grouped results, and `set` for duplicate detection.

### Java 17

The Java implementation uses an enterprise-oriented service architecture.

Its principal components are:

- `Employee` record for immutable observations.
- `Dataset` for validated data ownership.
- `StatisticsService` for mathematical calculations.
- `EDAService` for profiling and analytical orchestration.
- `AnalysisResult` for immutable output.
- `QualityIssue` for structured data-quality findings.

The design separates statistical operations from dataset management and reporting.

### PostgreSQL

The database implementation models a persistent EDA workflow.

Its principal entities are:

| Table | Purpose |
|---|---|
| `datasets` | Dataset registration |
| `dataset_columns` | Dataset schema metadata |
| `employee_observations` | Analytical observations |
| `analysis_runs` | Analysis execution history |
| `column_profiles` | Persisted statistical profiles |
| `quality_issues` | Persisted quality findings |

Views provide reusable analytical queries.

The stored procedure `run_eda` performs profiling and records quality findings.

A trigger prevents modification of finalized analysis runs.

## 14. Database analytical mechanisms

### 14.1 Common Table Expressions

The salary outlier view uses CTEs to separate quartile calculation from boundary calculation.

This improves the readability of multi-stage analytical SQL.

### 14.2 Window functions

The department distribution view uses a window function to calculate category percentages within each dataset.

### 14.3 Ordered-set aggregates

`PERCENTILE_CONT` calculates continuous percentiles directly in PostgreSQL.

### 14.4 Statistical aggregates

PostgreSQL provides:

- `AVG`
- `MIN`
- `MAX`
- `STDDEV_SAMP`
- `VAR_SAMP`
- `CORR`
- `COUNT`

These functions support efficient database-side analysis without transferring all observations to an application.

### 14.5 Indexing

The implementation includes indexes for dataset identifiers, department grouping, non-null salary values, and source-record identifiers.

Indexes improve selective retrieval but consume storage and increase the cost of inserts and updates.

Index design should reflect actual query patterns and dataset size.

## 15. Missing values and statistical reliability

Missing-value treatment can change analytical conclusions.

For example, calculating average salary only from available salary observations estimates the average of the observed records, not necessarily the entire workforce population.

Pairwise correlation can also use a different number of observations for different variable pairs.

Consequently, statistical reports should retain valid observation counts alongside their estimates.

The implementations report valid numeric counts and missing-value totals to make this distinction visible.

## 16. Performance considerations

Let:

- \(n\) represent the number of observations.
- \(m\) represent the number of columns.
- \(k\) represent the number of numerical columns.

| Operation | Typical complexity |
|---|---|
| Dataset traversal | \(O(nm)\) |
| Missing-value counts | \(O(nm)\) |
| Duplicate detection | Expected \(O(nm)\) |
| Sorting for quartiles | \(O(n\log n)\) per column |
| Mean and variance | \(O(n)\) |
| Pearson correlation | \(O(n)\) per variable pair |
| Full correlation matrix | \(O(k^2n)\) |
| Grouped aggregation | Expected \(O(n)\) with hash-based grouping |

Sorting is required for exact quantile and median calculations in these implementations.

For large datasets, additional techniques may be appropriate:

- Chunk-based CSV processing.
- Streaming aggregates.
- Approximate quantile algorithms.
- Database-side aggregation.
- Partitioned datasets.
- Incremental profiling.
- Parallel processing where computationally justified.

The in-memory implementations are intended for educational and moderate-sized analytical workloads rather than unlimited datasets.

## 17. Security and operational considerations

EDA pipelines frequently process sensitive organizational, financial, and operational records.

Production deployments should apply:

- Access controls for source datasets.
- Least-privilege database permissions.
- Parameterized SQL for application-provided filters.
- Input validation before statistical processing.
- Restricted output-directory permissions.
- Protection of sensitive analytical reports.
- Audit logging for analysis executions.
- Retention policies for source and derived data.
- Appropriate masking or pseudonymization of identifiers.

The sample implementations use synthetic workforce observations. Real employee datasets require appropriate privacy and access controls.

CSV files should also be treated as untrusted input. File-size limits, encoding validation, parser limits, and resource controls are important for externally supplied datasets.

## 18. Edge cases and limitations

The implementations account for several common analytical edge cases:

- Empty or missing values.
- Datasets without valid numeric observations.
- Duplicate records.
- Constant numerical columns.
- Undefined correlation.
- Single-observation standard deviation.
- Invalid numerical values.
- Inconsistent CSV field counts.
- Empty categories.
- Unusual numerical observations.

The implementations do not perform automatic imputation, hypothesis testing, causal inference, feature engineering, or predictive modelling.

They also do not automatically identify whether a distribution is normal, skewed, multimodal, or subject to temporal drift.

These analyses require additional statistical procedures and domain-specific interpretation.

The type-inference and CSV implementations have different supported formats. The JavaScript parser is a focused CSV implementation, not a complete implementation of every CSV dialect. The C++ and Java implementations use a predefined workforce schema rather than general-purpose CSV ingestion.

The PostgreSQL procedure persists salary profiling and selected quality findings, while the application implementations calculate a broader set of in-memory statistics.

## 19. Execution

### Python

Run the built-in sample analysis with:

`python exploratory_data_analysis.py`

Analyze an external CSV file with:

`python exploratory_data_analysis.py --input employees.csv`

Save a report to a specified location:

`python exploratory_data_analysis.py --input employees.csv --output reports/eda.json`

Run grouped analysis:

`python exploratory_data_analysis.py --group department --measure salary`

Run statistical checks:

`python exploratory_data_analysis.py --test`

### JavaScript

Run the sample analysis:

`node exploratory_data_analysis.js`

Analyze a CSV file:

`node exploratory_data_analysis.js --input employees.csv`

Specify an output report:

`node exploratory_data_analysis.js --input employees.csv --output reports/eda.json`

Run grouped analysis:

`node exploratory_data_analysis.js --group department --measure salary`

Run correctness tests:

`node exploratory_data_analysis.js --test`

### C++17

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic exploratory_data_analysis.cpp -o eda`

Execute:

`./eda`

On Windows:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic exploratory_data_analysis.cpp -o eda.exe`

`eda.exe`

### Java 17

Compile:

`javac ExploratoryDataAnalysis.java`

Execute:

`java ExploratoryDataAnalysis`

Run statistical tests:

`java ExploratoryDataAnalysis --test`

### PostgreSQL

Execute the SQL script using a PostgreSQL client connected to a database in which the executing role has permission to create schemas, tables, views, functions, procedures, and triggers.

The script creates the `eda` schema, inserts the sample workforce dataset, executes the analysis procedure, and runs retrieval and reporting queries.

## 20. Practical interpretation

EDA provides evidence about dataset structure and statistical behavior before more advanced analytical procedures are applied.

For the workforce dataset, the analytical workflow can establish:

- Whether records contain missing measurements.
- Whether complete observations are repeated.
- How salary varies across departments.
- Whether salary observations contain potential outliers.
- How salary and experience are linearly associated.
- Whether numerical variables have sufficient valid observations.
- Which quality issues should be investigated before downstream analysis.

These findings support data validation, analytical planning, and informed decisions about subsequent statistical or machine-learning workflows.
