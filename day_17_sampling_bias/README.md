# Sampling bias: selection bias, survivorship bias and sampling errors

## Topic introduction

Sampling is the process of observing a subset of a population in order to learn about the population as a whole. Statistical analysis becomes useful only when the relationship between the observed sample and the target population is understood.

Three concepts are especially important:

- **Selection bias** occurs when the mechanism determining who enters the observed dataset systematically changes the characteristics of that dataset.
- **Survivorship bias** occurs when analysis focuses on entities that remain visible after a selection or survival process while excluding entities that disappeared.
- **Sampling error** is the random difference between a sample statistic and the corresponding population parameter.

These concepts are related but are not interchangeable. Sampling error is primarily a problem of random variation. Sampling bias is a problem of systematic distortion. A very large biased sample can provide a highly precise estimate of the wrong quantity.

The three implementations in this repository approach the subject from different technical perspectives:

- Python provides a broad educational simulation environment with reusable statistical demonstrations.
- JavaScript demonstrates the same subject through executable application-style data processing and deterministic random simulation.
- C++ develops an industry-style case study using classes, data structures, algorithms, validation, and explicit system components.

---

## Fundamental terminology

### Population

The **population** is the complete group about which the study intends to make a statement.

For an income survey, the population could be all adults in a country. The population does not have to be physically observed in its entirety.

### Target population

The **target population** is the population to which the research question actually refers.

A survey may collect data from people who can access an online form, while the target population is all adults. The difference between these two groups creates a potential coverage problem.

### Sample

A **sample** is the subset of population units that is actually observed.

If 2,000 people answer a survey intended to describe 200 million adults, the 2,000 respondents are the observed sample.

### Sampling frame

A **sampling frame** is the operational source from which sample units can be selected.

Examples include:

- a population register
- a customer database
- a list of households
- a registry of companies
- a database of eligible voters
- a list of employees

A sampling frame can differ from the target population.

### Parameter

A **parameter** is a numerical property of the population.

Examples include:

- population mean income
- population proportion employed
- population variance
- population median
- population treatment effect

The parameter is generally the quantity the researcher wants to estimate.

### Statistic

A **statistic** is calculated from observed sample data.

Examples include:

- sample mean
- sample proportion
- sample standard deviation
- sample median

The statistic is used as an estimator or descriptive measure of the population parameter.

---

## Sampling error

Suppose the true population mean is:

`μ = 50`

A random sample might produce:

`x̄ = 49.2`

The difference is:

`49.2 - 50 = -0.8`

That difference is sampling error.

A different random sample might produce:

`x̄ = 51.1`

The direction and magnitude of the error vary across samples.

### Important property

Random sampling error generally decreases as sample size increases.

For a simple random sample, the standard error of a mean is approximately related to:

`SE(x̄) = σ / √n`

where:

- `σ` is the population standard deviation
- `n` is sample size

The square-root relationship is important. Increasing the sample size by a factor of four reduces the standard error by approximately a factor of two.

This does not mean that increasing the sample size automatically eliminates bias.

---

## Sampling bias

Sampling bias is systematic distortion caused by the sample-selection process.

Consider a population with:

- low-income people
- middle-income people
- high-income people

If the sampling mechanism disproportionately includes high-income people, the sample mean can be consistently higher than the population mean.

Increasing the sample size from 1,000 to 1,000,000 does not necessarily solve the problem if the same biased selection mechanism is used.

The distinction can be expressed conceptually as:

`large random sample -> lower sampling error`

but:

`large biased sample -> potentially precise estimate of a biased quantity`

---

## Selection bias

Selection bias is a broad category of bias created by how observations become part of the analyzed dataset.

Selection can occur through:

- eligibility rules
- recruitment
- survey participation
- institutional admission
- treatment assignment
- database availability
- geographic access
- technological access
- filtering
- dropout
- survival
- publication
- historical record preservation

The critical question is not merely how many observations exist. The critical question is **why these observations exist in the dataset and which observations are absent**.

---

## Types of selection-related bias

### Undercoverage

Undercoverage occurs when some members of the target population have little or no opportunity to enter the sampling frame.

The Python, JavaScript, and C++ implementations model an internet-access frame.

Suppose the target population contains 20,000 adults but only 15,000 have internet access.

The online sampling frame covers only part of the population.

The coverage rate is:

`coverage rate = frame size / population size`

Undercoverage becomes important when the characteristics of excluded people differ from those of covered people.

### Convenience sampling

Convenience sampling selects observations because they are easy to access.

Examples include:

- asking people in a nearby location
- surveying website visitors
- using readily available employees
- analyzing only a convenient database
- collecting responses from a social-media audience

Convenience does not imply randomness.

A convenient sample can be useful for exploratory work, but its ability to represent a target population must not be assumed without evidence.

### Volunteer bias

Volunteer bias occurs when people who choose to participate differ systematically from people who do not volunteer.

For example, people with unusually strong opinions may be more willing to participate in a voluntary survey.

The resulting sample may overrepresent extreme views.

### Nonresponse bias

Nonresponse bias occurs when sampled units fail to provide data and their characteristics differ systematically from respondents.

The key issue is not simply a low response rate.

A survey with a 20% response rate can be approximately representative under some mechanisms, while a survey with a 90% response rate can still be biased if the missing 10% is systematically different.

The important relationship is:

`response mechanism -> composition of observed respondents`

---

## Survivorship bias

Survivorship bias is a specific selection mechanism.

An initial population exists, but only some members remain observable after a process.

Examples include:

- companies that remain active
- investment funds that continue operating
- products that remain on the market
- websites that remain online
- students who graduate
- patients who remain in a study
- military aircraft that return from missions
- published papers that survive editorial filtering

If analysis examines only survivors, the original population is no longer represented.

### Company example

Suppose 10,000 companies are created.

Some fail and disappear.

Others survive.

If an analyst examines only surviving companies and asks why they performed well, the analyst has already removed the failures from the dataset.

The Python, JavaScript, and C++ implementations explicitly generate companies and assign survival probabilities related to performance.

They then compare:

- all companies
- surviving companies
- failed companies

This demonstrates why survivor-only estimates can differ substantially from estimates based on the original population.

---

## Selection bias versus survivorship bias

Survivorship bias is a form of selection bias, but not every selection bias problem is survivorship bias.

| Concept | Main mechanism |
|---|---|
| Selection bias | Entry into the observed sample is systematically related to relevant characteristics |
| Survivorship bias | Only entities that remain visible after a process are analyzed |
| Undercoverage | Some population members are absent from the sampling frame |
| Nonresponse bias | Sampled units do not respond and differ from respondents |
| Convenience sampling | Units are selected primarily because they are easy to access |
| Volunteer bias | Participation is self-selected |
| Sampling error | Random variation between samples and the population |

---

## Python implementation

The Python script is organized as a sequence of executable demonstrations.

### Population construction

`make_population()` creates a synthetic numerical population.

The population is intentionally heterogeneous rather than perfectly uniform. A mixture of normal distributions creates different regions of the population.

The purpose is not to reproduce a real country's income distribution. The purpose is to create data in which different sampling mechanisms produce visibly different estimates.

### Random sampling

`random_sample()` uses Python's standard-library `Random.sample()`.

The function validates the requested sample size before selection.

This demonstrates an important implementation principle: statistical code should reject impossible inputs instead of silently producing invalid output.

### Sampling error simulation

`demonstrate_sampling_error()` repeatedly samples the same population.

It compares sample sizes:

- 10
- 50
- 200
- 1,000

For each sample size, it calculates repeated sampling errors.

The result illustrates the relationship between sample size and random variation.

### Selection bias

The `Person` data class represents an individual using:

- income
- age
- employment status
- internet access

`online_only_selection()` creates an internet-access sample.

`employed_only_selection()` creates an employed-only sample.

The script compares these means with the complete population mean.

The example demonstrates that selection criteria can change the estimand.

### Undercoverage

`demonstrate_undercoverage()` treats internet access as a simplified sampling-frame condition.

It reports:

- target population size
- frame size
- coverage rate
- population mean
- frame mean

It also creates a deliberately restrictive high-income subset to demonstrate how convenience-like selection can introduce substantial distortion.

### Nonresponse

`simulate_survey()` receives a response-probability function.

This design is important because it separates the survey mechanism from the analysis.

The example intentionally makes response probability depend on income.

The program then compares the respondent mean with the population mean.

This demonstrates how a response mechanism can create bias.

---

## Collider bias

Selection bias can also arise from conditioning on a variable affected by two other variables.

The Python implementation defines a `Patient` with:

- severity
- treatment effect
- hospitalization status

Hospitalization depends on both severity and treatment effect.

The program calculates the correlation between severity and treatment effect:

1. among all patients
2. among hospitalized patients

If two variables are approximately independent before selection but both affect selection, conditioning on the selected group can create an association between them.

This is commonly described using a causal graph:

`Severity -> Hospitalization <- Treatment effect`

Hospitalization is a **collider** because arrows from two variables point into it.

Conditioning on a collider can introduce statistical association.

The practical lesson is that restricting a dataset to a particular group is not always an innocent filtering operation.

---

## Bias and variance

An estimator can be characterized using:

- bias
- variance
- mean squared error

The bias of an estimator `T` for parameter `θ` is:

`Bias(T) = E[T] - θ`

Variance is:

`Var(T) = E[(T - E[T])²]`

Mean squared error is:

`MSE(T) = Var(T) + Bias(T)²`

This decomposition is important because an estimator can have:

- low bias and high variance
- high bias and low variance
- high bias and high variance
- relatively low values of both

The Python script compares a random sampler with a deliberately biased sampler.

The biased sampler repeatedly selects observations from the upper portion of the population.

Its estimates can be stable while remaining systematically displaced from the population parameter.

---

## Stratified sampling

Stratified sampling divides a population into defined groups called strata.

The Python, JavaScript, and C++ implementations divide people by age:

- under 35
- 35 to 59
- 60 and above

The implementations deliberately draw fixed numbers from each group.

Stratification can improve representation and precision when strata are meaningfully defined.

But an important distinction exists between:

`stratified sample`

and:

`simple random sample`

A stratified sample deliberately controls representation by subgroup.

If different strata are sampled at different rates, population estimates may require weights.

---

## Unequal inclusion probabilities

Not every sampling design gives every population unit the same probability of selection.

Suppose:

- young adults have inclusion probability 0.70
- middle-aged adults have inclusion probability 0.40
- older adults have inclusion probability 0.15

A simple unweighted average treats every selected observation equally.

That can be inappropriate when the sample composition differs from the population composition because of unequal selection probabilities.

---

## Inverse-probability weighting

If an observation has inclusion probability `πᵢ`, a basic inverse-probability weight is:

`wᵢ = 1 / πᵢ`

An observation with probability 0.10 receives a weight of 10.

An observation with probability 0.50 receives a weight of 2.

The weighted mean can be expressed as:

`weighted mean = Σ(wᵢyᵢ) / Σwᵢ`

The C++ case study implements this mechanism through `SelectedPerson` and `SelectionAnalyzer::weightedMean()`.

The Python implementation demonstrates the same principle using tuples containing an observation and its inclusion probability.

### Weight instability

Very small inclusion probabilities produce very large weights.

For example:

`π = 0.001`

gives:

`w = 1000`

A small number of highly weighted observations can therefore dominate an estimate.

Real survey methodology may use:

- weight trimming
- calibration
- post-stratification
- generalized regression weighting
- design-based variance estimation

The appropriate method depends on the sampling design.

---

## Bootstrap uncertainty

The bootstrap repeatedly resamples observations from the observed sample with replacement.

If the original sample is:

`[10, 20, 30]`

a bootstrap sample could be:

`[20, 20, 10]`

Another could be:

`[30, 10, 30]`

Repeated bootstrap samples create an empirical distribution of the statistic.

The implementations use bootstrap resampling to estimate uncertainty around a sample mean.

### Important limitation

Bootstrap resampling does not automatically correct sampling bias.

If a biased sample excludes an entire group, bootstrap resampling continues to draw from the biased observed sample.

In simplified form:

`biased sample -> bootstrap -> repeated biased samples`

The bootstrap addresses uncertainty conditional on the observed data. It does not reconstruct observations that were never observed.

---

## Sensitivity analysis

When a missing group cannot be measured directly, assumptions can be made explicit.

Suppose:

- observed fraction = 80%
- observed mean = 70
- missing fraction = 20%

If the missing group's mean is assumed to be 40:

`combined mean = 0.80 × 70 + 0.20 × 40`

`combined mean = 64`

If the missing group's mean is 90:

`combined mean = 0.80 × 70 + 0.20 × 90`

`combined mean = 74`

The Python, JavaScript, and C++ implementations vary the assumed missing-group mean.

This does not identify the true answer automatically. It demonstrates how conclusions depend on assumptions about the unobserved population.

---

## JavaScript implementation

The JavaScript file is a self-contained Node.js program.

### Deterministic random generation

`createRandom()` implements a small deterministic pseudo-random generator.

A deterministic generator is useful in an educational program because repeated executions can reproduce the same simulation.

### Sampling without replacement

`sampleWithoutReplacement()` copies an array, performs a Fisher-Yates shuffle, and returns the requested number of observations.

This makes the random-sampling mechanism explicit rather than relying on an external statistical library.

### Functional selection

JavaScript's `filter()` is used extensively to represent selection rules.

For example:

`people.filter(person => person.internetAccess)`

expresses a selection condition directly.

This is particularly useful for showing how data-processing pipelines can accidentally encode selection mechanisms.

### Nonresponse mechanism

`simulateSurvey()` accepts a function called `responseProbability`.

This is a flexible design because the survey-selection mechanism is supplied as behavior rather than hard-coded into the sampling function.

### Stratified sampling

`stratifiedSample()` accepts a collection of predicate functions and corresponding sample sizes.

This demonstrates a reusable design in which the sampling algorithm is separated from the definition of each stratum.

### Bootstrap

`bootstrapMean()` repeatedly selects observations from the original sample using random indices.

The function then sorts bootstrap estimates and extracts empirical percentile bounds.

---

## C++ case study

The C++ program models a national income-survey pipeline.

The architecture is intentionally more structured than the Python and JavaScript implementations.

### `Person`

`Person` is a domain structure containing:

- age
- income
- employment
- internet access

It represents an individual in the target population.

### `Company`

`Company` represents an organization with:

- starting performance
- survival status

This structure supports the survivorship-bias demonstration.

### `Patient`

`Patient` contains:

- severity
- treatment effect
- hospitalization status

It supports the collider-bias demonstration.

### `SelectedPerson`

`SelectedPerson` combines an observed person with an inclusion probability.

This is necessary for inverse-probability weighting.

---

## `PopulationGenerator`

`PopulationGenerator` constructs the synthetic population.

The class owns:

- a Mersenne Twister generator
- normal distribution generator
- uniform distribution generator

The design isolates population generation from sampling and analysis.

This separation makes the system easier to test and extend.

---

## `SamplingService`

`SamplingService` implements sampling algorithms.

### Simple random sampling

`simpleRandomSample()`:

1. validates sample size
2. copies the population
3. shuffles the copy
4. truncates the shuffled vector

This is approximately `O(N)` for the shuffle, where `N` is the population size.

### Stratified sampling

`stratifiedSample()` first partitions people into age-based strata.

It then shuffles each stratum and selects the requested number.

If the requested sample size exceeds a stratum's available members, the function throws an exception.

This is an example of explicit constraint validation.

---

## `SelectionAnalyzer`

`SelectionAnalyzer` provides analytical operations.

`incomeMean()` converts the income field into a numerical vector and computes the arithmetic mean.

`internetOnly()` demonstrates frame-based selection.

`employedOnly()` demonstrates another selection mechanism.

`weightedMean()` implements inverse-probability weighting.

The class keeps selection analysis separate from the generation of observations.

---

## `SurveySimulator`

`SurveySimulator` models nonresponse.

The response probability depends on normalized income.

This is deliberately constructed so that response is not independent of the quantity being estimated.

The simulator returns two datasets:

- respondents
- nonrespondents

The separation is useful because nonrespondents are not simply deleted from conceptual consideration. They remain part of the original population while being absent from the observed response dataset.

---

## `SurvivorshipStudy`

`SurvivorshipStudy` generates companies and assigns survival probabilities based partly on starting performance.

The `report()` method calculates:

- mean of all companies
- number of survivors
- number of failures
- survivor mean
- failure mean

The difference between these quantities demonstrates why studying survivors alone can distort historical conclusions.

---

## `ColliderStudy`

`ColliderStudy` generates patients and calculates hospitalization using both severity and treatment effect.

The resulting structure is:

`severity -> hospitalization <- treatment effect`

The class then compares correlations before and after selection on hospitalization.

This demonstrates that selection can create relationships that were not present in the original population.

---

## `BootstrapEstimator`

`BootstrapEstimator` encapsulates bootstrap estimation.

The implementation:

1. checks that the sample is non-empty
2. repeatedly samples indices with replacement
3. computes a mean for each bootstrap sample
4. sorts the bootstrap estimates
5. extracts empirical percentile bounds

The implementation uses the standard library and does not require a statistical dependency.

---

## Complexity considerations

Let:

- `N` = population size
- `n` = sample size
- `B` = number of bootstrap repetitions

A simple random shuffle is approximately:

`O(N)`

Computing a mean is:

`O(n)`

A bootstrap procedure that creates `n` observations for each of `B` repetitions is approximately:

`O(Bn)`

Sorting `B` bootstrap estimates is:

`O(B log B)`

The total bootstrap cost is therefore approximately:

`O(Bn + B log B)`

Memory requirements depend on whether resamples are stored simultaneously.

The implementations store bootstrap estimates so percentile intervals can be calculated.

---

## Sampling error and sample size

For simple random sampling, the standard error of a sample mean decreases approximately according to:

`1 / √n`

This creates diminishing returns.

For example, increasing sample size from:

`100 -> 400`

approximately halves the standard error.

Increasing it from:

`400 -> 900`

reduces the standard error by another factor of:

`√(400 / 900) = 2 / 3`

Large samples therefore improve precision, but the relationship is not linear.

---

## Precision versus validity

Precision and validity are separate concepts.

A narrow confidence interval indicates that the estimator is relatively stable under the assumed sampling process.

It does not prove that the estimator targets the correct population quantity.

For example:

- a biased estimator can have low variance
- a representative estimator can have high variance
- a large sample can be systematically unrepresentative

This distinction is central to survey design.

---

## Common mistakes

### Mistake: assuming a large sample is automatically representative

Sample size measures how much information has been collected.

It does not prove that the information represents the target population.

### Mistake: treating nonresponse as irrelevant

If respondents and nonrespondents differ systematically, simply analyzing respondents can introduce bias.

### Mistake: analyzing only survivors

If failed entities are absent from the dataset, estimates based on survivors can overstate success.

### Mistake: confusing sampling error with sampling bias

Sampling error varies randomly across samples.

Bias can persist in the same direction across repeated samples.

### Mistake: assuming bootstrap eliminates bias

Bootstrap samples are generated from the observed sample.

They cannot restore systematically excluded population members.

### Mistake: ignoring inclusion probabilities

Unequal sampling probabilities can make an unweighted sample statistic inappropriate for estimating a population quantity.

### Mistake: conditioning on a selected group without examining the selection mechanism

Filtering can create collider bias when the filtering variable is affected by multiple relevant variables.

### Mistake: assuming response rate alone determines bias

A response rate describes the amount of nonresponse.

It does not by itself describe whether the missing observations differ systematically from respondents.

---

## Edge cases

Statistical implementations must handle unusual inputs explicitly.

The programs demonstrate several such cases.

### Empty samples

A mean cannot be computed from zero observations.

### Single observations

A sample mean can be computed from one observation, but conventional sample variance cannot be estimated from one observation.

### Constant variables

Correlation is undefined if one variable has zero variance.

### Invalid sample sizes

A requested sample larger than the available population is invalid for sampling without replacement.

### Invalid probabilities

Probabilities must lie between zero and one.

### Very small inclusion probabilities

Inverse-probability weights can become extremely large.

### Empty strata

A stratified design must verify that each requested stratum contains enough eligible observations.

---

## Limitations of the simulations

These programs are educational simulations rather than representations of any specific real population.

The generated distributions are artificial.

The relationships between income, age, employment, internet access, response behavior, survival, and hospitalization are deliberately constructed to demonstrate statistical mechanisms.

Real surveys and observational studies may involve:

- clustered sampling
- multistage sampling
- finite population corrections
- calibration weights
- post-stratification
- panel attrition
- measurement error
- imputation
- duplicate records
- household-level dependence
- geographic clustering
- complex nonresponse mechanisms
- missing-not-at-random processes

The simplified implementations isolate individual mechanisms so their effects can be observed clearly.

---

## Implementation considerations

A production sampling system should separate at least four concerns:

1. population and frame definition
2. sampling mechanism
3. data collection and response
4. statistical estimation

Combining all four into a single function makes it difficult to determine where bias entered the pipeline.

Metadata should record:

- sampling-frame definition
- selection probabilities
- eligibility rules
- response status
- dropout status
- weights
- stratification variables
- clustering variables
- collection dates
- version of the sampling procedure

Without this information, later analysts may be unable to reconstruct the selection process.

---

## Security considerations

Sampling systems can process sensitive personal or organizational information.

Relevant engineering controls include:

- minimizing personally identifiable information
- restricting access to raw survey records
- separating identifiers from analytical variables
- protecting sampling-frame files
- auditing changes to inclusion rules
- preventing unauthorized modification of sampling weights
- validating imported records
- preserving provenance of analytical datasets
- avoiding accidental publication of individual-level observations

Security is relevant because unauthorized changes to a sampling frame or selection rule can alter the composition of a dataset without changing the analysis code.

---

## Practical applications

Sampling-bias analysis is relevant to:

- public opinion surveys
- epidemiology
- clinical studies
- market research
- customer analytics
- employee surveys
- education research
- financial analysis
- economic surveys
- reliability studies
- A/B testing
- observational studies
- machine-learning datasets
- historical research
- platform analytics
- product research

The common question is:

**Which observations became visible, which remained invisible, and why?**

---

## Important distinctions

| Issue | Primary question |
|---|---|
| Sampling error | How much would the statistic vary across random samples? |
| Selection bias | Did the selection mechanism systematically distort the sample? |
| Survivorship bias | Were failed or disappeared entities excluded from analysis? |
| Undercoverage | Which target units were absent from the sampling frame? |
| Nonresponse bias | Do respondents differ systematically from nonrespondents? |
| Convenience sampling | Were observations selected mainly because they were easy to access? |
| Volunteer bias | Did participation depend on an individual's decision to participate? |
| Collider bias | Did conditioning on a common effect create an association? |
| Weighting | Can unequal selection probabilities be accounted for? |
| Sensitivity analysis | How much do conclusions change under plausible assumptions about missing units? |

---

## Python, JavaScript, and C++ comparison

### Python

The Python implementation is suited to statistical exploration because the language makes data transformations and simulations concise.

The script demonstrates:

- reusable sampling functions
- data classes
- repeated simulation
- bias and variance comparisons
- stratification
- weighting
- bootstrap estimation
- sensitivity analysis
- validation

Its organization emphasizes statistical concepts and experimentation.

### JavaScript

The JavaScript implementation demonstrates how sampling logic can exist inside application-oriented data processing.

It uses:

- functions
- array transformations
- predicate-based filtering
- deterministic pseudo-random generation
- objects
- higher-order functions
- validation
- simulation

JavaScript is particularly useful when sampling logic becomes part of a web or application data pipeline, although production statistical inference generally requires careful methodology beyond the basic language features demonstrated here.

### C++

The C++ implementation focuses on system architecture and explicit data structures.

It demonstrates:

- classes
- structs
- encapsulation
- standard-library containers
- random distributions
- algorithms
- exceptions
- validation
- weighted estimation
- bootstrap computation
- modular case-study design

C++ is useful when statistical computation is embedded in high-performance systems or larger software architectures.

---

## Real-world analytical workflow

A defensible sampling analysis can be organized around the following questions:

### Define the population

State exactly who or what the research is intended to describe.

### Define the frame

Determine how population units become available for selection.

### Examine coverage

Identify groups that cannot enter the frame or have substantially lower access.

### Examine selection probabilities

Determine whether all eligible units have equal or known probabilities of selection.

### Examine participation

Study response, refusal, dropout, and missingness mechanisms.

### Examine survival

Determine whether the observed dataset contains only entities that survived an earlier process.

### Examine conditioning

Identify filters that may create collider structures.

### Estimate uncertainty

Use an uncertainty method appropriate to the actual sampling design.

### Perform sensitivity analysis

Vary assumptions about unobserved groups when their characteristics are uncertain.

### Document the design

Preserve the sampling rules and metadata required to reproduce the analysis.

---

## Conceptual interpretation of the complete case study

The C++ program models a chain in which a population exists before observations are collected.

The full population contains individuals with different ages, incomes, employment statuses, and internet-access characteristics.

An internet-only frame excludes some individuals.

A response process then excludes additional observations.

Unequal inclusion probabilities create a second estimation issue.

Weights can partially compensate for unequal selection when the probabilities are known or adequately estimated.

A separate company dataset demonstrates survivorship bias by comparing the complete historical population with the survivor-only population.

A patient dataset demonstrates collider bias by comparing a complete population with a selected hospitalized population.

Bootstrap estimation then demonstrates that uncertainty calculation and sample-selection validity are separate concerns.

Sensitivity analysis makes assumptions about missing groups explicit rather than hiding them inside an estimate.

The central technical principle is that statistical inference depends not only on the observed values but also on the mechanism that produced the observed dataset.

---

## Core equations

### Sampling error

`sampling error = statistic - population parameter`

### Standard error of a mean

`SE(x̄) ≈ σ / √n`

### Bias

`Bias(T) = E[T] - θ`

### Mean squared error

`MSE(T) = Var(T) + Bias(T)²`

### Inverse-probability weight

`wᵢ = 1 / πᵢ`

### Weighted mean

`weighted mean = Σ(wᵢyᵢ) / Σwᵢ`

### Coverage rate

`coverage rate = sampling-frame units / target-population units`

These equations describe different properties of a sampling process and should not be treated as interchangeable measures.

---

## Why selection mechanisms matter

Two datasets can contain the same number of observations and have very different inferential properties.

For example:

- Dataset A contains 100,000 randomly selected observations.
- Dataset B contains 100,000 observations selected because they were highly active users.

Dataset B is larger than many traditional surveys, but its size alone does not establish representativeness.

Likewise:

- 10,000 surviving companies
- 10,000 randomly selected companies from the original company population

are not equivalent samples if failure is related to the variable being studied.

The mechanism of observation is part of the statistical problem.

---

## Final implementation principle

A useful mental model for sampling analysis is:

`target population`
`-> sampling frame`
`-> eligibility`
`-> selection`
`-> participation`
`-> survival`
`-> observed dataset`
`-> estimator`
`-> uncertainty`

Every arrow is a possible location for systematic distortion.

The most important distinction is therefore not simply:

**How much data do we have?**

It is:

**What process produced the data we have, and how does that process relate to the population we want to understand?**
