# Sampling: population, samples and sampling techniques

## Topic introduction

Sampling is the process of selecting observations from a larger population so that information about the population can be studied without necessarily observing every member.

A **population** is the complete set of units relevant to a study. A **sample** is a subset of those units that is actually observed. The purpose of sampling is usually to obtain information about population characteristics while reducing the cost, time, or operational burden of a complete census.

Examples of populations include:

- All households in a city
- All registered voters in a jurisdiction
- All transactions made by a company during a financial year
- All students enrolled at a university
- All manufactured components produced by a factory
- All patients eligible for a clinical study

The quality of statistical inference depends strongly on how the sample is selected. A large sample is not automatically a representative sample. A small probability sample can provide a stronger basis for inference than a much larger sample selected through a systematically biased process.

The implementations in this repository use a synthetic population and demonstrate several probability and non-probability sampling designs.

## Fundamental concepts

### Population

The population is the complete group about which a researcher wants to make statements.

In the Python implementation, the population is represented by a collection of `Person` objects. Each object contains characteristics such as age, region, employment status, income, satisfaction, and cluster.

In the C++ case study, the equivalent unit is a `Household`.

The population size is commonly represented by `N`.

### Sample

A sample is the subset of the population selected for observation.

The sample size is commonly represented by `n`.

When sampling without replacement, a unit selected once cannot be selected again. This is the approach used by the simple random sampling implementations.

### Parameter

A **parameter** is a numerical characteristic of the population.

Examples include:

- Population mean
- Population proportion
- Population variance
- Population total

If the entire population has monthly incomes `x_1, x_2, ..., x_N`, the population mean is:

`μ = (1/N) Σx_i`

The Python program calculates the population mean directly because the synthetic population is available to the simulation.

In an actual survey, the true population parameter is generally unknown.

### Statistic

A **statistic** is calculated from a sample.

The sample mean is:

`x̄ = (1/n) Σx_i`

The sample mean can be used as an estimator of the population mean.

The distinction is important:

- Parameter: describes the population.
- Statistic: describes the observed sample.
- Estimator: a rule used to estimate a population parameter.
- Estimate: the numerical result obtained after applying the estimator to a particular sample.

### Sampling unit

A sampling unit is the basic unit eligible for selection.

Examples include:

- Individual
- Household
- Company
- School
- Hospital
- Geographic area
- Transaction

The sampling unit depends on the research design.

### Sampling frame

A sampling frame is the operational representation from which the sample is selected.

For example, a survey of university students might use an enrollment database as its sampling frame.

A sampling frame can differ from the target population. If eligible people are missing from the frame, the resulting problem is called **coverage error**.

## Probability sampling

Probability sampling uses a randomization mechanism in which eligible units have known, non-zero selection probabilities.

Important probability designs include:

- Simple random sampling
- Systematic sampling
- Stratified sampling
- Cluster sampling
- Multistage sampling

Probability sampling provides a formal basis for calculating selection probabilities and sampling uncertainty.

It does not guarantee that every sample will look perfectly representative. Random samples can differ from the population by chance.

## Simple random sampling

Simple random sampling selects units so that every possible sample of a specified size has the same probability of being selected.

The Python implementation uses `random.sample`, while the JavaScript and C++ implementations use explicitly seeded random generators for reproducible demonstrations.

The conceptual procedure is:

1. Define the population.
2. Establish a sampling frame.
3. Determine the sample size.
4. Randomly select the required number of units.
5. Measure the selected units.
6. Calculate statistics.
7. Use the statistics to estimate population quantities.

Simple random sampling is mathematically convenient, but it can be operationally expensive when population units are geographically dispersed.

## Systematic sampling

Systematic sampling selects units according to an interval.

If the population contains `N` units and the desired sample contains `n` units, the approximate interval is:

`k = N/n`

A random starting point is selected and subsequent units are selected at approximately every `k` positions.

The Python implementation demonstrates this process.

Systematic sampling can be efficient, but the ordering of the sampling frame matters. If the frame contains a periodic pattern that coincides with the sampling interval, the sample can become problematic.

For example, suppose a production database repeats a particular quality pattern every ten records and the sampling interval is also ten. The sample could repeatedly select similar positions in that cycle.

## Stratified sampling

Stratified sampling divides the population into **strata** and samples from each stratum.

A stratum is a subgroup defined before sampling.

Possible stratification variables include:

- Region
- Age group
- Employment status
- Organization size
- Education level

The Python, JavaScript, and C++ implementations use geographic region as an example.

### Proportionate allocation

In proportionate stratified sampling, the sample size allocated to stratum `h` is approximately:

`n_h = (N_h/N)n`

where:

- `N_h` is the size of stratum `h`
- `N` is the total population size
- `n_h` is the sample size assigned to the stratum
- `n` is the total sample size

Stratification is particularly useful when important subgroups must be represented in the sample.

It can also improve precision when units within strata are relatively homogeneous while the strata differ meaningfully from one another.

## Cluster sampling

Cluster sampling divides the population into naturally occurring groups called clusters.

Examples include:

- Schools
- Villages
- Wards
- Hospitals
- Branch offices
- Production facilities

Instead of directly selecting individuals, the researcher selects clusters.

In the C++ case study, geographic wards represent clusters.

Cluster sampling can substantially reduce fieldwork costs because selected observations may be geographically concentrated.

Its statistical trade-off is that observations inside a cluster may be correlated. If households in the same ward have similar economic characteristics, observing many households from a few wards may provide less independent information than observing the same number of households distributed across many wards.

## Multistage sampling

Multistage sampling uses multiple sampling stages.

A common design is:

`Population → clusters → individual units`

For example:

1. Randomly select districts.
2. Randomly select households within the selected districts.
3. Interview the selected households.

The C++ implementation uses this approach by first selecting wards and then selecting households within those wards.

Multistage sampling is common in large operational surveys because the complete list of every individual may be unavailable or expensive to construct.

Its variance estimation is more complicated than that of a simple random sample because selection occurs at multiple stages.

## Non-probability sampling

Non-probability sampling does not require known random selection probabilities.

Examples include:

- Convenience sampling
- Quota sampling
- Purposive sampling
- Snowball sampling

These designs can be useful in exploratory research, qualitative research, hard-to-reach populations, or situations where a probability sampling frame is unavailable.

Their inferential limitations must be recognized. A large non-probability sample does not automatically provide the same statistical guarantees as a probability sample.

## Convenience sampling

Convenience sampling selects units that are easily accessible.

For example, a researcher might survey the first 100 people encountered at a location.

The Python and JavaScript implementations intentionally use simple accessibility-based selection to demonstrate the mechanism.

Convenience samples can be inexpensive, but accessibility may be related to the variable being studied. That can create systematic differences between the sample and the target population.

## Quota sampling

Quota sampling defines target counts for categories.

For example, a study might specify:

- 35 participants from the North region
- 25 from the South
- 20 from the East
- 20 from the West

The JavaScript implementation demonstrates quota selection.

Quota sampling should not automatically be described as equivalent to stratified random sampling. Both can control subgroup counts, but stratified probability sampling also uses random selection within the strata.

## Purposive sampling

Purposive sampling selects units because they meet a research-defined criterion.

Examples include selecting:

- Experts with specialized knowledge
- Organizations meeting a particular operational condition
- Cases representing unusual events
- Participants with direct experience of a phenomenon

The researcher deliberately defines the selection rule.

This can be appropriate for qualitative or specialized research, but the resulting sample should not automatically be treated as a probability sample.

## Snowball sampling

Snowball sampling uses existing participants to identify or recruit additional participants.

It can be useful when members of a population are difficult to identify through conventional sampling frames.

The network structure of recruitment can influence which individuals are reached, creating potential selection effects.

## Sampling error

Sampling error is the difference between a sample-based estimate and the corresponding population parameter caused by observing a sample rather than the entire population.

For a mean:

`sampling error = sample mean - population mean`

The Python, JavaScript, and C++ programs calculate this quantity because the synthetic population is known.

In a real survey, the true population mean is usually unavailable, so sampling error cannot normally be calculated directly from the observed sample alone.

Sampling error should be distinguished from other forms of survey error.

## Nonsampling errors

Sampling is only one part of total survey quality.

### Coverage error

Coverage error occurs when the sampling frame does not properly represent the target population.

Examples include:

- Missing eligible people
- Duplicate units
- Ineligible units included in the frame

### Nonresponse error

Nonresponse occurs when selected eligible units fail to provide the required information.

Nonresponse can become a source of bias when respondents and nonrespondents systematically differ.

### Measurement error

Measurement error occurs when the recorded value differs from the intended quantity.

Possible causes include:

- Poor questionnaire wording
- Recall problems
- Incorrect instruments
- Data-entry mistakes
- Misunderstood questions

### Processing error

Processing errors can occur during:

- Data entry
- Coding
- Transformation
- Deduplication
- Data integration
- Statistical computation

A well-designed sampling procedure cannot compensate for every type of nonsampling error.

## Sampling distribution

A sampling distribution is the distribution of a statistic across repeated samples drawn according to the same sampling design.

The Python and JavaScript programs repeatedly draw samples and calculate their means.

If many samples of the same size are drawn, their sample means form an empirical sampling distribution.

The standard deviation of this distribution is related to the **standard error** of the estimator.

For a simple random sample, the standard error of the sample mean is approximately:

`SE(x̄) = s/√n`

where `s` is the sample standard deviation.

For a finite population sampled without replacement, a finite population correction can also be relevant:

`FPC = √((N-n)/(N-1))`

The complete variance calculation depends on the sampling design.

## Confidence intervals

A confidence interval provides a range constructed by a specified statistical procedure.

For an approximate normal-theory interval:

`estimate ± critical value × standard error`

The implementations use `1.96` as an approximate 95% normal critical value.

The Python and JavaScript programs calculate the interval for the sample mean, and the C++ case study performs the same calculation.

For small samples or situations where normal approximations are inappropriate, a Student's t distribution or another suitable inferential method may be required.

A confidence interval is not a statement that a particular fixed parameter has a literal probability of being inside the already calculated interval. The frequentist interpretation concerns the long-run behavior of the procedure used to construct intervals.

## Sample-size determination

Sample-size planning depends on the research objective and assumptions.

For estimating a population proportion, the basic Cochran expression is:

`n_0 = z²p(1-p)/e²`

where:

- `z` is the critical value
- `p` is the anticipated proportion
- `e` is the desired margin of error

When the population is finite, a finite-population correction can be applied:

`n = n_0 / (1 + (n_0 - 1)/N)`

When there is little prior information about the proportion, `p = 0.5` is conservative because it maximizes `p(1-p)`.

Sample-size planning should also consider:

- Expected nonresponse
- Design effect
- Subgroup requirements
- Cost
- Precision targets
- Population structure
- Analysis requirements

## Weighting

Not every observation necessarily represents the same number of population units.

If an observation has weight `w_i`, a weighted mean is:

`x̄_w = Σ(w_i x_i) / Σw_i`

Weights can arise from:

- Unequal selection probabilities
- Nonresponse adjustments
- Post-stratification
- Calibration procedures

The Python and JavaScript implementations include weighted-mean demonstrations.

Weighting must be applied carefully. Poorly constructed weights can increase variance or introduce other problems.

## Design effect

The nominal sample size does not always describe the amount of independent statistical information available.

Cluster sampling often produces correlated observations.

A simplified conceptual relationship is:

`DEFF ≈ 1 + (m-1)ρ`

where:

- `m` is average cluster size
- `ρ` is the intracluster correlation coefficient

As within-cluster similarity increases, the design effect can increase.

The effective sample size can be approximated conceptually by:

`n_eff ≈ n/DEFF`

Actual survey variance estimation should follow the complete sampling design rather than relying blindly on a simplified formula.

## Python implementation

The Python program is designed as the most comprehensive educational implementation.

### Population model

`Person` is a dataclass representing a sampling unit.

Each unit contains:

- `person_id`
- `age`
- `region`
- `employment`
- `monthly_income`
- `satisfaction`
- `cluster`

`build_population()` creates a reproducible synthetic finite population.

### Simple random sampling

`simple_random_sample()` uses Python's standard-library `Random.sample()` to select units without replacement.

This demonstrates the central randomization mechanism of simple random sampling.

### Systematic sampling

`systematic_sample()` calculates an approximate interval and selects units from a randomized starting position.

The implementation also validates the sample size and verifies that sampled identifiers are unique.

### Stratified sampling

`stratified_sample()` groups people by a supplied stratum function.

The function supports general grouping logic rather than hard-coding a single attribute.

For example, region can be supplied as the stratum variable.

The implementation performs proportionate allocation and corrects rounding so that the final sample size matches the requested size.

### Cluster and multistage sampling

`cluster_sample()` selects complete clusters.

`multistage_sample()` first selects clusters and then samples individual units inside each selected cluster.

The two functions demonstrate the difference between selecting entire groups and selecting individuals within selected groups.

### Statistical estimation

The Python program calculates:

- Population parameters
- Sample statistics
- Sample means
- Standard deviations
- Sampling errors
- Confidence intervals
- Weighted means

### Repeated-sampling simulation

`simulation_of_sampling_distribution()` repeatedly draws samples and calculates sample means.

This makes the idea of a sampling distribution observable rather than purely symbolic.

### Validation

The Python implementation explicitly tests invalid situations, including:

- Zero sample size
- Sample larger than the population
- Invalid proportions
- Invalid weights
- Empty observations

These checks are important in production statistical software because invalid inputs should fail explicitly rather than produce plausible-looking but incorrect results.

## JavaScript implementation

The JavaScript implementation complements the Python implementation with an application-oriented approach.

### Seeded randomness

JavaScript's standard `Math.random()` is not directly seedable.

The `SeededRandom` class provides a small deterministic pseudorandom generator for reproducible educational demonstrations.

It implements:

- Random numbers
- Integer selection
- Random choice
- Shuffling
- Sampling without replacement

This is useful for testing because the same seed produces the same demonstration sequence.

### Data structures

The JavaScript program uses:

- Arrays
- Objects
- Maps
- Classes
- Higher-order functions

`groupBy()` demonstrates how a general grouping abstraction can support stratified and cluster sampling.

### Stratified sampling

`stratifiedSample()` accepts an attribute function.

This allows the same implementation to stratify by different variables without rewriting the sampling algorithm.

### Quota sampling

`quotaSample()` demonstrates how category targets can be filled without requiring random selection inside each category.

This provides a direct implementation-level distinction between quota sampling and probability-based stratified sampling.

### Statistical functions

The JavaScript file implements:

- Mean
- Median
- Sample standard deviation
- Weighted mean
- Standard error
- Confidence intervals
- Sample-size calculation

No external npm package is required.

## C++ case study

The C++ program models a realistic municipal survey.

The problem is to estimate average household monthly income without conducting a complete census.

### System architecture

The conceptual workflow is:

`Population → sampling design → selected households → measurements → estimator → uncertainty`

The population contains households distributed among geographic wards.

The sampling engine provides reproducible random selection.

### `Household`

`Household` is a C++ structure representing a sampling unit.

It stores:

- Household identifier
- Age
- Region
- Employment category
- Monthly income
- Geographic cluster

### `SamplingEngine`

`SamplingEngine` encapsulates pseudorandom generation and sampling operations.

The use of `std::mt19937` provides a standard-library pseudorandom generator with deterministic behavior when initialized with a fixed seed.

`randomSample()` performs sampling without replacement by shuffling a copy and retaining the requested number of units.

### Simple random design

`simpleRandomSample()` validates the requested sample size and delegates random selection to `SamplingEngine`.

The resulting estimate is compared with the known population parameter because the simulation has access to the complete synthetic population.

### Stratified design

`stratifiedSample()` groups households by region.

The allocation follows the principle:

`n_h = (N_h/N)n`

The implementation performs integer allocation and distributes remaining observations while respecting stratum capacity.

### Multistage design

`multistageSample()` implements:

`Population → selected wards → selected households`

This resembles operational survey designs where geographic grouping reduces fieldwork requirements.

### Confidence interval

`confidenceInterval()` computes an approximate normal-theory interval:

`x̄ ± 1.96 × SE`

The implementation exposes the estimate, standard error, lower bound, and upper bound as a dedicated `ConfidenceInterval` structure.

### Sample-size planning

`cochranSampleSize()` implements a finite-population-adjusted Cochran-style calculation.

The C++ implementation validates all major numerical assumptions before calculating the result.

### Repeated sampling

`repeatedSampling()` draws hundreds of samples and stores their mean estimates.

The resulting estimates can be used to observe the empirical sampling distribution.

## Important distinctions

| Concept | Meaning |
|---|---|
| Population | Complete target group |
| Sample | Selected subset of the population |
| Parameter | Numerical property of the population |
| Statistic | Numerical property calculated from a sample |
| Census | Observation of every population unit |
| Sampling frame | Operational representation used for selection |
| Sampling unit | Basic unit eligible for selection |
| Stratum | Subgroup sampled separately |
| Cluster | Group selected as part of the sampling design |
| Probability sample | Sample with known non-zero selection probabilities |
| Non-probability sample | Selection probabilities are not established in the same probability framework |
| Sampling error | Random difference between sample estimate and population parameter |
| Nonresponse error | Error associated with failure of selected units to respond |
| Coverage error | Error caused by mismatch between target population and sampling frame |
| Measurement error | Error in observed measurements |
| Weight | Adjustment representing differing population contributions |

## Stratified versus cluster sampling

These methods are frequently confused because both divide a population into groups.

### Stratified sampling

The researcher divides the population into strata and usually samples units from every important stratum.

The purpose is often to ensure representation and potentially improve precision.

Conceptually:

`Population → strata → sample from each stratum`

### Cluster sampling

The researcher divides the population into clusters and selects some clusters.

The purpose is often operational efficiency.

Conceptually:

`Population → clusters → select clusters`

The statistical properties are different.

Strata are often designed to be internally homogeneous and distinct from one another.

Clusters may contain internally similar units, which can reduce the amount of independent information obtained from a given nominal sample size.

## Probability versus non-probability sampling

Probability sampling provides a formal framework for selection probabilities and design-based inference.

Non-probability sampling can be useful when:

- A sampling frame is unavailable
- The study is exploratory
- The target population is difficult to identify
- Qualitative selection is intentional
- Operational constraints prevent probability selection

The appropriate choice depends on the research question and study design.

## Common mistakes

### Confusing a large sample with a representative sample

Increasing sample size reduces random sampling variability under suitable conditions, but it does not automatically correct systematic selection bias.

A very large sample obtained from an unsuitable frame can still be systematically unrepresentative.

### Treating convenience sampling as random sampling

Selecting whoever is easiest to reach is not equivalent to random selection.

### Confusing stratification with clustering

Stratified designs normally sample within strata.

Cluster designs select groups and may then observe all or some units within selected groups.

### Ignoring the sampling frame

A theoretically correct random selection process cannot solve a fundamentally incomplete or inaccurate sampling frame.

### Ignoring nonresponse

If selected respondents differ systematically from those who do not respond, the final respondent set can differ from the intended sample.

### Ignoring weighting

When selection probabilities differ, an unweighted estimate can fail to represent the intended population quantity.

### Treating every confidence interval as a simple random-sample interval

Complex designs can require specialized variance estimation.

Using a simple random-sample formula for a clustered or multistage design can understate or otherwise misrepresent uncertainty.

### Using an inappropriate sample-size formula

Sample-size calculations depend on:

- Estimand
- Confidence level
- Desired precision
- Expected variability
- Population size
- Sampling design
- Subgroup requirements
- Nonresponse

A single universal sample-size number does not exist.

## Edge cases

### Sample size of one

A single observation cannot provide a conventional estimate of sample standard deviation.

The implementations explicitly handle or reject situations requiring at least two observations.

### Sample size equal to population size

If `n = N`, the sample is effectively a census.

Sampling error from selecting a subset disappears because every unit is observed, although nonsampling errors can still exist.

### Sample larger than population

Sampling without replacement cannot select more unique units than exist in the population.

The Python, JavaScript, and C++ implementations reject this condition.

### Empty population

Statistical functions such as the mean require at least one observation.

### Zero total weight

A weighted mean is undefined when all weights sum to zero.

The implementations reject this condition.

### Invalid probability

A proportion used in the sample-size equation must lie strictly between zero and one.

## Performance considerations

### Python

Random sampling using the standard library is suitable for moderate educational datasets.

For very large populations, memory and data-transfer costs can become important. Streaming or reservoir-sampling techniques may be preferable when the entire population cannot fit into memory.

### JavaScript

Arrays and `Map` provide convenient in-memory structures.

For browser applications, large survey datasets may require pagination, indexed storage, workers, or server-side processing.

The JavaScript implementation intentionally remains dependency-free.

### C++

C++ provides explicit control over memory and data structures.

The case study uses `std::vector` and `std::map`, which are sufficient for the simulated dataset.

For large-scale production systems, selection and aggregation may need to operate directly against databases or distributed data systems instead of loading the complete population into memory.

## Reservoir sampling

When a population is received as a stream and its total size is unknown, reservoir sampling can select a fixed-size random sample without storing the complete stream.

For a reservoir of size `k`:

1. Store the first `k` observations.
2. For the `i`-th subsequent observation, generate a random position.
3. Replace an existing reservoir element under the appropriate probability rule.

This is especially useful for:

- Large logs
- Streaming events
- Data pipelines
- Continuous telemetry
- Very large files

It is distinct from ordinary random sampling from an already materialized finite population.

## Production implementation considerations

A production sampling system should record:

- Target population definition
- Sampling frame source
- Frame version or timestamp
- Sampling unit definition
- Sampling design
- Selection probabilities
- Random seed policy
- Sample size
- Stratum definitions
- Cluster definitions
- Nonresponse handling
- Weight construction
- Data-quality checks
- Exclusion rules
- Replacement rules
- Audit information

Reproducibility is especially important when random selection is used. A controlled random seed can make development and testing reproducible, although production systems may require stronger randomization and governance depending on the application.

## Security considerations

Sampling software may process sensitive datasets.

Important controls include:

- Restricting access to sampling frames
- Minimizing personally identifiable information
- Encrypting sensitive data
- Separating identifiers from analytical variables
- Logging authorized access
- Protecting exported samples
- Avoiding unnecessary retention
- Validating imported data
- Preventing accidental disclosure through small subgroup reports

A sampling algorithm itself does not guarantee privacy.

Even an unbiased sample can create privacy risks if individual-level observations are exposed.

## Debugging considerations

Useful checks include:

- Confirm that the requested sample size is valid.
- Confirm that sampling without replacement creates unique IDs.
- Confirm that stratum allocations add to the requested sample size.
- Confirm that no stratum exceeds its available population.
- Confirm that cluster selection uses the intended cluster variable.
- Compare repeated-sampling estimates with the known population parameter in simulations.
- Test invalid input explicitly.
- Use fixed random seeds during development.
- Check population and sample counts before calculating statistics.
- Verify weighted totals before calculating weighted estimates.

The implementations include several of these checks directly.

## Real-world relevance

Sampling is used across many fields.

### Public administration

Governments may sample households, businesses, or geographic areas to estimate population characteristics without surveying every unit.

### Market research

Organizations sample customers to estimate preferences, satisfaction, awareness, and purchasing behavior.

### Quality control

Manufacturers sample products or production lots to estimate defect rates.

### Healthcare research

Researchers may sample eligible participants or medical records to study outcomes and characteristics.

### Financial analysis

Institutions can sample transactions for audit, fraud investigation, quality assurance, or risk analysis.

### Data engineering

Sampling can reduce computational cost during exploratory analysis of very large datasets.

### Scientific research

Researchers use sampling to make observations manageable while maintaining a defined relationship between the observed sample and the population of interest.

## Cross-language comparison

| Area | Python | JavaScript | C++ |
|---|---|---|---|
| Population model | `dataclass` | Object | `struct` |
| Random generator | `random.Random` | Custom seeded generator | `std::mt19937` |
| Random sampling | `Random.sample` | `SeededRandom.sample` | `std::shuffle` |
| Grouping | Dictionaries | `Map` | `std::map` |
| Statistics | Standard library | Custom functions | Standard library algorithms |
| Validation | Exceptions | Errors and range checks | Exceptions |
| Main emphasis | Educational statistical implementation | Application-oriented data processing | Industry-style systems case study |
| External packages | None | None | None |
| Reproducibility | Explicit seed | Explicit seed | Explicit seed |

## Conceptual workflow demonstrated by all three programs

The complete process can be represented conceptually as:

`Define population → construct sampling frame → choose design → determine sample size → select units → collect observations → validate data → calculate statistic → estimate parameter → quantify uncertainty → interpret within design limitations`

The sampling design should be selected before data collection because the design determines how observations should be interpreted and how uncertainty should be estimated.

The central distinction throughout the implementations is between the **population**, which is the complete group of interest, and the **sample**, which is the observed subset used to learn about that population.
