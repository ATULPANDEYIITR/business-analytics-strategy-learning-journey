# NumPy Numerical Computing and Array Operations

## Scope

This learning artifact treats NumPy as a numerical array-processing system rather than as a collection of isolated functions. The implementations model a small sensor-analysis workflow in which measurements are stored as dense numerical matrices, transformed with vectorized operations, normalized, statistically evaluated, and checked for anomalies.

The five source files use different engineering perspectives:

| File | Primary perspective | Main implementation |
|---|---|---|
| Python | Direct NumPy numerical computing | Dense arrays, masking, broadcasting, statistics, linear algebra |
| JavaScript | Typed-array numerical processing | `Float64Array`, matrix abstraction, events, asynchronous statistics |
| C++17 | Performance-oriented numerical engine | Contiguous matrix storage, STL algorithms, validation |
| Java 17 | Enterprise domain model | Records, interfaces, policy objects, streams, explicit validation |
| PostgreSQL | Relational numerical workflow | Measurements, normalization profiles, statistical SQL, functions, triggers |

The central data model is a matrix in which rows represent observations and columns represent numerical variables:

```text
                 temperature   humidity   pressure   vibration
sample 0             22.4        45.0      1012.3       0.12
sample 1             23.1        46.5      1011.8       0.15
sample 2             24.8        49.2      1010.4       0.18
...
```

The same conceptual structure is represented differently in each implementation because numerical arrays, typed memory, object-oriented domain models, and relational tables have different strengths.

## Core Numerical Model

NumPy arrays are homogeneous, multidimensional numerical structures. Unlike a normal Python list, a NumPy array has a defined shape and data type, allowing numerical operations to be performed over complete arrays.

The Python implementation creates a `float64` matrix with eight observations and four variables. The shape is therefore `(8, 4)`.

Important properties used in the implementation are:

- `shape` identifies the size of each dimension.
- `ndim` identifies the number of dimensions.
- `dtype` identifies the numerical storage type.
- Integer indexing selects individual elements.
- Slicing selects ranges of rows or columns.
- Boolean masks select records satisfying conditions.
- Vectorized expressions operate on arrays without explicit Python loops.
- `axis` controls the dimension along which reductions such as `mean` and `std` operate.

For example, a column operation over `axis=0` calculates one result for each feature, while a row operation can produce one result per observation.

## Array Creation and Data Types

The Python implementation uses `np.array` with `dtype=np.float64`. Explicitly choosing the numerical type makes the representation predictable and avoids accidental mixing of integer and floating-point calculations.

The implementation also demonstrates deterministic random data using `np.random.default_rng`. A fixed seed makes numerical experiments reproducible.

The random generator is preferable to relying on implicit global random state because the generator can be passed explicitly to functions and isolated from unrelated random operations.

## Indexing and Slicing

The numerical workflow uses several forms of array selection.

A row can be selected with an expression such as `values[0]`. A complete column can be selected with `values[:, 0]`. A range of rows can be selected using a slice such as `values[:3]`.

These operations are important because numerical processing often separates observations from features without copying or manually constructing new lists.

The Python edge-case section also demonstrates that array slicing can produce a view rather than an independent copy. Mutating the selected view can therefore affect the original array.

That distinction matters when working with large arrays because views can avoid memory allocation, while unintended mutation can introduce difficult debugging problems.

## Boolean Masking

Boolean masking is used to identify high-temperature observations.

The expression conceptually represented by `values[values[:, 0] >= 27.0]` creates a Boolean condition for each row and uses that condition to select matching records.

This is a central NumPy technique because filtering can be expressed directly as an array operation rather than as an explicit record-by-record loop.

The same idea can be extended to compound conditions using Boolean operators and parentheses.

## Vectorization

Vectorization is one of the most important distinctions between ordinary Python numerical processing and NumPy-based processing.

The Python implementation converts Celsius values to Fahrenheit using:

`temperature_c * 9.0 / 5.0 + 32.0`

The expression operates on the entire array. There is no explicit Python loop around each temperature.

The performance section compares a Python list comprehension against an equivalent NumPy expression for one million values. The exact timing depends on hardware, Python version, memory conditions, and runtime state, so the measurement is illustrative rather than a fixed benchmark.

Vectorization can reduce Python interpreter overhead and allows NumPy to use optimized numerical loops over contiguous numerical memory.

## Broadcasting

Broadcasting allows arrays with compatible shapes to participate in arithmetic without explicitly constructing repeated copies.

The Python implementation adds a four-element offset vector to an eight-by-four matrix:

`values + offsets`

The four offsets correspond to the four columns. NumPy logically applies each offset to every row.

Broadcasting is useful for:

- feature-specific calibration
- centering data
- adding offsets
- subtracting column means
- scaling features
- applying per-feature thresholds

Broadcasting rules depend on compatible dimensions. It is therefore important to understand array shapes before applying arithmetic to avoid either unexpected results or shape errors.

## Aggregation and Statistics

The implementation calculates:

- minimum values
- maximum values
- arithmetic means
- medians
- standard deviations
- correlations
- weighted normalized scores

Column-wise statistics use `axis=0`, which produces one result for each sensor variable.

The statistical model is descriptive rather than inferential. Standard deviation describes dispersion in the supplied dataset; it does not establish that a distribution follows a particular statistical model.

The JavaScript, C++, and Java implementations reproduce the core descriptive calculations explicitly so their numerical behavior can be compared with the NumPy implementation.

## Missing Values

NumPy represents missing floating-point values with `NaN`.

The Python implementation uses `np.isnan` to locate missing values and `np.nanmean` to calculate means while ignoring `NaN` values.

This is different from replacing missing values with zero. A zero can be a valid measurement, while `NaN` represents unavailable or undefined numerical information.

The example also uses `np.nan_to_num` to demonstrate explicit replacement. In production numerical analysis, the replacement value should be chosen according to the meaning of the measurement rather than automatically assuming zero is appropriate.

## Normalization

The workflow performs per-column min-max normalization.

For a value `x`, minimum `min`, and maximum `max`, the normalized value is:

`(x - min) / (max - min)`

The result normally lies between zero and one when the value is within the observed range.

A zero-range feature requires special handling. If `max` equals `min`, direct division would be invalid. The implementations therefore map a constant feature to zero.

Normalization allows measurements with very different units and scales to participate in a weighted scoring model.

For example:

| Feature | Typical scale |
|---|---|
| Temperature | Tens of degrees |
| Humidity | Tens of percentage points |
| Pressure | Around one thousand hPa |
| Vibration | Fractions of a g |

Without normalization, pressure would numerically dominate a simple weighted sum.

## Weighted Numerical Scoring

After normalization, the Python workflow calculates a weighted score using a vector-matrix multiplication:

`normalized @ weights`

The four weights are:

| Feature | Weight |
|---|---|
| Temperature | 0.35 |
| Humidity | 0.20 |
| Pressure | 0.25 |
| Vibration | 0.20 |

The weights express the numerical model used by the example. They are not universal scientific thresholds.

A weighted score is useful for demonstrating matrix multiplication because each row becomes a single scalar produced from all normalized features.

## Anomaly Detection

The Python implementation calculates column-wise z-scores:

`(x - mean) / standard_deviation`

The absolute z-score is then compared against a configurable threshold.

The example uses a threshold of `2.0`.

A zero standard deviation is handled explicitly. If every value in a feature is identical, its standard deviation is zero and direct division would be invalid. The implementation substitutes one for the divisor, which results in zero z-scores for the constant feature.

This is a defensive numerical decision. A production anomaly detector would also need domain-specific rules for distribution assumptions, sample size, seasonality, measurement errors, and robust statistics.

## Linear Algebra

The Python implementation includes:

- matrix-vector multiplication
- determinant calculation
- matrix inversion
- solution of a linear system

The linear system is solved with `np.linalg.solve` rather than calculating an inverse and multiplying by the vector.

That distinction matters numerically. Solving a linear system directly is generally preferable to explicitly forming an inverse when the goal is to solve `Ax = b`.

The assertion verifies that the calculated solution satisfies the original system within numerical tolerance.

## Numerical Precision

The examples use double-precision floating-point values.

Floating-point arithmetic is approximate. Values that appear mathematically identical may differ slightly after repeated calculations. The Python implementation therefore uses `np.allclose` for numerical comparisons where exact equality is inappropriate.

The same principle applies to C++ and Java calculations using `double`.

Numerical software should avoid assumptions such as `a + b == c` when floating-point rounding can affect the result.

## JavaScript Implementation

The JavaScript file does not mechanically reproduce NumPy syntax because standard JavaScript has no native NumPy-equivalent multidimensional array system.

It instead defines a `Matrix` class backed by `Float64Array`.

`Float64Array` provides:

- fixed-width floating-point storage
- contiguous typed numerical memory
- predictable element representation
- lower overhead than arrays containing arbitrary JavaScript values

The `Matrix` abstraction supplies operations such as:

- row access
- column extraction
- element access
- broadcasting
- column statistics
- normalization
- weighted row scoring

The file also uses Node.js `EventEmitter` to model an event-driven numerical monitoring workflow. Each evaluated record produces a result event, followed by a completion event.

An asynchronous statistics function uses `setImmediate` to demonstrate how numerical processing can be integrated into an event-driven Node.js application without introducing third-party dependencies.

## C++17 Implementation

The C++ implementation treats numerical processing as a compact matrix engine.

The `Matrix` class stores values in a single `std::vector<double>`. An element at row `r` and column `c` is stored at the linear position:

`r * columns + c`

This row-major representation provides contiguous storage and predictable indexing.

The implementation uses STL facilities such as:

- `std::vector`
- `std::generate`
- `std::max_element`
- `std::distance`
- `std::normal_distribution`
- `std::mt19937`

The `NumericalAnalyticsEngine` separates matrix storage from analytical operations. It performs normalization, weighted scoring, and anomaly detection without requiring an external numerical library.

The C++ implementation also validates matrix dimensions and index ranges through exceptions.

This design is intentionally different from Python's high-level vectorized execution. The C++ version exposes more of the memory and iteration structure directly, making it useful for understanding how numerical array operations can be implemented underneath a higher-level API.

## Java 17 Implementation

The Java implementation models measurements using the `SensorReading` record.

Records provide compact immutable domain objects for measurements while retaining validation in the compact constructor.

The `NumericalPolicy` interface separates scoring decisions from numerical storage. `WeightedRiskPolicy` maps a numerical score to either `NORMAL` or `ALERT`.

This demonstrates an enterprise-oriented separation:

```yaml
SensorReading
     |
     v
Matrix
     |
     v
Normalization
     |
     v
Weighted Score
     |
     v
NumericalPolicy
     |
     v
RiskResult
```

Java streams are used for descriptive statistics and filtering. Arrays remain explicit numerical storage because primitive `double` arrays avoid the boxing overhead associated with collections of `Double`.

The design uses `IllegalArgumentException` for invalid numerical configuration and `IndexOutOfBoundsException` for invalid matrix access.

## PostgreSQL Numerical Model

The PostgreSQL implementation represents numerical data relationally.

The principal relationship is:

```yaml
sensor_batches
       |
       v
measurements -----> sensors
       |
       v
normalization_profiles
       |
       v
statistical functions
       |
       v
anomaly_evaluations
```

A single `measurements` table stores one numerical value per sensor, sample, and batch.

This is different from the dense matrix representation used by Python. Relational storage separates values into rows so that constraints, foreign keys, indexing, transactions, and database-level validation can be applied.

The `measurement_matrix` view reconstructs the wide analytical representation using filtered aggregation.

## Database Constraints

The PostgreSQL schema uses:

- primary keys for row identity
- foreign keys for relationships
- unique constraints for sample uniqueness
- check constraints for valid ranges
- enum values for measurement status
- partial indexing for problematic states

The `validate_measurement` trigger checks each inserted or updated value against the configured sensor range.

Invalid values are marked `INVALID`, while valid values initially receive `NORMAL` status.

A later transactional update demonstrates that analytical policy can change a valid measurement to `WARNING` based on a temperature threshold.

## PostgreSQL Statistical Functions

`calculate_column_statistics` calculates per-sensor:

- minimum
- maximum
- mean
- population standard deviation
- measurement count

`calculate_normalized_scores` reconstructs normalized values using the configured minimum, maximum, and weight for each sensor.

`calculate_z_scores` uses PostgreSQL window functions to calculate per-sensor means and standard deviations and then evaluates the maximum absolute z-score for each sample.

This shows that numerical analysis is not restricted to application memory. Relational databases can perform substantial numerical aggregation close to the stored data.

## Performance Considerations

The Python implementation benefits from vectorized operations and NumPy's optimized numerical routines.

The JavaScript implementation uses `Float64Array` to avoid arbitrary JavaScript object storage for the numerical matrix.

The C++ implementation uses contiguous `std::vector<double>` storage and avoids unnecessary object allocation inside the core loops.

The Java implementation uses primitive `double[]` arrays for numerical operations instead of boxing each value into a collection object.

The PostgreSQL implementation adds indexes only for access patterns used by the workflow. The `(batch_id, sample_index)` index supports reconstruction and batch-oriented access, while the sensor index supports joins and sensor-specific analysis.

Performance should still be measured against realistic data sizes. An implementation that is efficient for eight rows may require different memory and execution strategies for millions or billions of observations.

## Memory and Copying

Array operations can create either views or new arrays depending on the operation.

This matters because large numerical datasets can consume substantial memory.

The Python example explicitly demonstrates view behavior for slicing. The JavaScript implementation copies row and column results to maintain clear ownership. The C++ matrix stores one contiguous vector and constructs separate vectors for extracted rows and columns. Java similarly returns copies of rows.

The PostgreSQL model avoids loading the entire dataset into application memory for aggregate queries.

These choices illustrate a central numerical-computing trade-off:

```lua
Less copying
    |
    +-- lower memory use
    |
    +-- faster large-data processing
    |
    +-- greater mutation/aliasing risk

More copying
    |
    +-- simpler ownership
    |
    +-- safer isolation
    |
    +-- higher memory and allocation cost
```

## Validation and Failure Handling

The implementations reject invalid numerical structures rather than silently continuing.

Examples include:

- empty or invalid matrix dimensions
- mismatched row lengths
- invalid indices
- incompatible broadcast dimensions
- invalid weight vectors
- non-finite numerical values
- non-positive anomaly thresholds
- zero-range normalization
- zero-variance anomaly features

The PostgreSQL layer also enforces relational integrity through database constraints and triggers.

Validation at multiple layers is useful because numerical errors can otherwise propagate through many calculations before becoming visible.

## Security Considerations

The numerical examples do not require network access, credentials, shell commands, or dynamic code execution.

The PostgreSQL implementation relies on database constraints rather than trusting client-side validation alone.

The source files do not interpolate untrusted strings into SQL statements because the SQL script is static.

In a production numerical service, input validation should occur at the ingestion boundary, database constraints should protect persistent data integrity, and resource limits should prevent unexpectedly large arrays from causing memory exhaustion.

Random seeds should also be handled deliberately. Reproducible seeds are useful for testing and debugging, while security-sensitive randomness requires a cryptographically secure random source rather than a conventional numerical pseudo-random generator.

## Distinct Implementation Roles

The five implementations are deliberately not identical.

| Implementation | Distinct engineering role |
|---|---|
| Python | High-level numerical analysis with NumPy's array semantics |
| JavaScript | Event-driven typed-array numerical processing |
| C++17 | Explicit memory-oriented numerical engine |
| Java 17 | Domain-oriented numerical service and policy model |
| PostgreSQL | Persistent relational numerical analysis |

The common scenario makes their behavior comparable while their implementation mechanisms remain distinct.

## Practical Numerical Workflow

The complete workflow can be viewed as:

```typescript
Raw measurements
      |
      v
Shape and type validation
      |
      v
Array / matrix representation
      |
      +--------------------+
      |                    |
      v                    v
Descriptive statistics   Missing/invalid data checks
      |                    |
      +---------+----------+
                |
                v
        Feature normalization
                |
                v
        Weighted numerical score
                |
                +------------------+
                |                  |
                v                  v
        Threshold decision    Z-score analysis
                |                  |
                +--------+---------+
                         |
                         v
                 Analytical result
```

This structure separates data representation, transformation, statistical evaluation, and decision logic.

## Limitations

The example data is deliberately small and deterministic. It demonstrates numerical mechanisms rather than providing a production sensor-calibration model.

The anomaly threshold of `2.0` is an example policy and should not be interpreted as a universal criterion.

Min-max normalization is sensitive to extreme values because the minimum and maximum determine the scale. For data with strong outliers, robust scaling or domain-specific transformations may be more appropriate.

Z-scores are most informative when the statistical assumptions behind them are reasonable. Non-Gaussian, seasonal, multimodal, or strongly dependent data may require other anomaly-detection methods.

The weighted risk score is also an engineered numerical model. Its weights need domain justification before being used for operational decisions.

## Key Distinctions

Array operations and numerical algorithms should not be confused with business decisions.

An array represents structured numerical data.

A transformation changes that data according to a mathematical rule.

A statistic summarizes numerical behavior.

A normalization changes scale.

An anomaly detector identifies observations meeting a numerical criterion.

A policy converts an analytical result into an operational state.

The implementations preserve these distinctions so that numerical computation remains testable and its assumptions remain visible.
