# A/B Testing: Experiment Design and Statistical Comparison

## 1. Introduction

A/B testing is a controlled experimentation method used to evaluate whether a change in a product, service, interface, business process, or operational system produces a measurable difference in an outcome.

An experiment divides eligible participants into groups that receive different versions of an intervention.

- **Control:** The existing experience or baseline condition.
- **Treatment:** The modified experience being evaluated.
- **Primary metric:** The principal outcome used to evaluate the hypothesis.
- **Guardrail metric:** An additional measurement used to identify undesirable effects.
- **Experiment:** The complete process of design, assignment, observation, analysis, and decision-making.

Consider an e-commerce checkout experiment.

The product team believes that redesigning the checkout button will increase completed purchases.

| Component | Definition |
|---|---|
| Control | Original checkout button |
| Treatment | Redesigned checkout button |
| Hypothesis | The redesigned button increases purchases |
| Primary metric | Purchase conversion rate |
| Guardrail metric | Checkout latency |
| Population | Eligible checkout visitors |
| Allocation | 50% control and 50% treatment |
| Significance level | 0.05 |
| Statistical power | 0.80 |
| Minimum detectable effect | 2 percentage points |

The objective is not simply to determine which variant has a higher observed conversion rate. The objective is to evaluate whether the observed difference provides sufficient statistical evidence and practical value to justify a product decision.

## 2. Experimental Design

Experimental design determines how participants are selected, how variants are assigned, which outcomes are measured, and how the experiment will be evaluated.

### 2.1 Formulating a hypothesis

A useful hypothesis specifies:

- The population being studied.
- The intervention being introduced.
- The expected direction of change.
- The measurable outcome.

Example:

The redesigned checkout interface will increase the purchase conversion rate among eligible visitors compared with the existing interface.

The null and alternative hypotheses are:

\[
H_0:p_T=p_C
\]

\[
H_1:p_T\neq p_C
\]

Where:

- \(p_T\) represents the treatment conversion probability.
- \(p_C\) represents the control conversion probability.

A two-sided hypothesis tests for a difference in either direction. A one-sided hypothesis is appropriate only when its direction is justified and established before examining the results.

### 2.2 Population and eligibility

The target population is the group to which the experimental findings are intended to apply.

Eligibility rules should be defined before assignment.

Examples include:

- First-time visitors.
- Customers using a particular checkout workflow.
- Users accessing a supported application version.
- Participants meeting a defined operational requirement.

Exclusion criteria must not be introduced selectively after examining outcomes. Such changes can introduce selection bias.

### 2.3 Random assignment

Random assignment allocates participants to variants independently of their characteristics and potential outcomes.

For a 50:50 experiment:

\[
P(C)=0.5
\]

\[
P(T)=0.5
\]

Randomization reduces systematic differences between experimental groups.

The implementations use deterministic hash-based assignment for reproducible participant allocation.

The assignment mechanism considers both the experiment identifier and participant identifier.

This has two important properties:

1. A participant receives the same assignment when returning to the experiment.
2. Different experiments can assign the same participant independently.

The assignment record is separate from the outcome record. This distinction makes it possible to monitor participants who were assigned but did not produce an observable outcome.

Production systems should use a well-defined bucketing mechanism, protect assignment identifiers, and maintain assignment consistency across devices and sessions where the experimental unit requires it.

### 2.4 Experimental unit

The experimental unit is the entity independently assigned to a variant.

Possible experimental units include:

| Experimental unit | Example |
|---|---|
| Individual | Website visitor |
| Customer | Registered account |
| Organization | Enterprise customer |
| Geographic region | Sales territory |
| Device | Connected device |
| Operational unit | Branch or service center |

The experimental unit must match the randomization and statistical analysis strategy.

For example, assigning individual employees to different treatments while their outcomes influence one another can introduce contamination.

Cluster randomization may be more appropriate when participants interact within groups.

### 2.5 Primary and secondary metrics

The primary metric should be selected before the experiment begins.

Common primary metrics include:

- Conversion rate.
- Revenue per participant.
- Average order value.
- Retention rate.
- Task completion rate.
- Time to complete a transaction.
- Error rate.

Secondary metrics provide additional information but should not replace the primary metric simply because they produce more favorable results.

Guardrail metrics monitor possible negative consequences.

For the checkout experiment:

| Metric | Role | Desired behavior |
|---|---|---|
| Purchase conversion | Primary | Increase |
| Revenue per participant | Secondary | Increase |
| Checkout latency | Guardrail | Remain acceptable |
| Payment failure rate | Guardrail | Avoid increase |
| Customer complaints | Guardrail | Avoid increase |

## 3. Sample Size and Statistical Power

Sample size planning estimates how many observations are required to detect an effect of a specified magnitude with a chosen probability.

Insufficient sample size can make an experiment unable to detect a meaningful difference.

### 3.1 Minimum detectable effect

The minimum detectable effect (MDE) is the smallest difference that the experiment is designed to detect at the specified statistical power and significance level.

Suppose:

- Baseline conversion rate: 10%.
- Expected treatment conversion rate: 12%.
- Absolute MDE: 2 percentage points.

Then:

\[
MDE=0.12-0.10=0.02
\]

Relative improvement is:

\[
Relative\ Lift=
\frac{0.12-0.10}{0.10}
=0.20
\]

The expected relative improvement is 20%.

Absolute and relative effects are not interchangeable. Sample size calculations require the effect definition to be consistent with the statistical model.

### 3.2 Statistical significance level

The significance level is represented by \(\alpha\).

A common selection is:

\[
\alpha=0.05
\]

It controls the probability of a Type I error under the null hypothesis when the statistical test assumptions hold.

A Type I error occurs when a true null hypothesis is rejected.

### 3.3 Statistical power

Statistical power is:

\[
Power=1-\beta
\]

Where \(\beta\) is the probability of a Type II error for a specified alternative.

A conventional design uses:

\[
Power=0.80
\]

This means that the experiment has an 80% probability of detecting the specified effect under the assumed model and conditions.

### 3.4 Sample size calculation

For an approximate two-independent-proportion comparison with equal group sizes:

\[
n=
\frac{
\left[
z_{1-\alpha/2}
\sqrt{2\bar p(1-\bar p)}
+
z_{1-\beta}
\sqrt{p_C(1-p_C)+p_T(1-p_T)}
\right]^2
}{
(p_T-p_C)^2
}
\]

Where:

\[
\bar p=\frac{p_C+p_T}{2}
\]

And:

- \(n\): approximate sample size per group.
- \(p_C\): baseline conversion rate.
- \(p_T\): expected treatment conversion rate.
- \(z_{1-\alpha/2}\): two-sided critical normal value.
- \(z_{1-\beta}\): power-related normal value.

The sample size calculators in all four programming implementations use this normal approximation.

The result is rounded upward to ensure that the planned sample size is not below the calculated requirement.

The calculation assumes independent observations and a conventional two-proportion testing framework.

Real-world planning may require adjustments for:

- Unequal allocation.
- Repeated observations.
- Cluster randomization.
- Attrition.
- Multiple comparisons.
- Overdispersion.
- Small sample sizes.
- Noncompliance.
- Multiple primary outcomes.

For unequal allocation, the sample size must be recalculated using the actual allocation ratio rather than assuming equal groups.

## 4. Statistical Comparison

Statistical comparison evaluates the difference between observed group outcomes.

### 4.1 Conversion rate

The conversion rate is:

\[
p=\frac{x}{n}
\]

Where:

- \(x\): number of conversions.
- \(n\): number of participants with observed outcomes.

Example:

| Metric | Control | Treatment |
|---|---:|---:|
| Participants | 10,000 | 10,000 |
| Conversions | 1,000 | 1,200 |
| Conversion rate | 10% | 12% |

### 4.2 Absolute lift

Absolute lift measures the direct difference between treatment and control.

\[
Absolute\ Lift=p_T-p_C
\]

For the example:

\[
0.12-0.10=0.02
\]

The absolute improvement is 2 percentage points.

### 4.3 Relative lift

Relative lift measures the improvement relative to the control.

\[
Relative\ Lift=
\frac{p_T-p_C}{p_C}
\]

For the example:

\[
\frac{0.02}{0.10}=0.20
\]

The relative improvement is 20%.

### 4.4 Pooled two-proportion z-test

For independent binary outcomes, the pooled conversion estimate under the null hypothesis is:

\[
\hat p=
\frac{x_C+x_T}{n_C+n_T}
\]

The pooled standard error is:

\[
SE_0=
\sqrt{
\hat p(1-\hat p)
\left(
\frac{1}{n_C}+\frac{1}{n_T}
\right)
}
\]

The test statistic is:

\[
z=
\frac{p_T-p_C}{SE_0}
\]

For a two-sided test:

\[
p\text{-value}=2\Phi(-|z|)
\]

Where \(\Phi\) represents the standard normal cumulative distribution function.

The implementations calculate this statistic using the pooled variance estimate under the null hypothesis.

### 4.5 P-value interpretation

The p-value measures the probability, assuming the null hypothesis and test assumptions are correct, of observing a result at least as extreme as the one obtained.

A p-value below 0.05 provides evidence against the null hypothesis at the selected significance level.

It does not establish:

- The probability that the null hypothesis is true.
- The probability that the treatment is successful.
- The size of the business benefit.
- The absence of bias.
- The validity of the experimental design.

Statistical significance should never be interpreted as proof of practical value.

## 5. Confidence Intervals

A confidence interval estimates a range of plausible values for the treatment-control difference under the statistical model.

For two independent proportions, an approximate unpooled standard error is:

\[
SE_{CI}=
\sqrt{
\frac{p_C(1-p_C)}{n_C}
+
\frac{p_T(1-p_T)}{n_T}
}
\]

The approximate confidence interval is:

\[
(p_T-p_C)\pm z_{1-\alpha/2}SE_{CI}
\]

For a 95% confidence interval:

\[
z_{0.975}\approx1.96
\]

The implementations use the pooled standard error for the hypothesis test and the unpooled standard error for the confidence interval.

These are different statistical calculations serving different purposes.

A confidence interval that excludes zero is generally consistent with rejection of the corresponding two-sided null hypothesis under the same normal-approximation framework.

For small samples or rare binary outcomes, exact or score-based methods may provide better coverage than the simple Wald interval used in these educational implementations.

## 6. Statistical Significance Versus Practical Significance

These concepts answer different questions.

| Concept | Question |
|---|---|
| Statistical significance | Is the observed difference inconsistent with the null hypothesis at the selected significance level? |
| Practical significance | Is the size of the observed difference sufficiently valuable to justify action? |

A very large experiment can identify a statistically significant difference that has negligible business value.

A small experiment can produce a substantial observed effect without enough evidence to establish statistical significance.

The implementations therefore evaluate both conditions independently.

A treatment is classified as meeting the implemented decision criteria when:

\[
p\text{-value}<\alpha
\]

And:

\[
Absolute\ Lift\geq MDE
\]

This is a simplified decision rule. A complete business decision should also consider uncertainty, implementation cost, risk, guardrail performance, and the economic value of the expected effect.

## 7. Experiment Lifecycle

An experiment is a controlled operational process rather than an isolated statistical calculation.

The implemented lifecycle is:

| Stage | Activity | Main control |
|---|---|---|
| Design | Define hypothesis and metrics | Design validation |
| Planning | Calculate sample size | Power analysis |
| Approval | Review experiment design | Approval decision |
| Launch | Activate experiment | State validation |
| Assignment | Allocate participants | Stable randomization |
| Observation | Record outcomes | Duplicate prevention |
| Monitoring | Check assignments and guardrails | Operational validation |
| Closure | Complete or stop experiment | State transition |
| Analysis | Compare variants | Statistical evaluation |
| Decision | Evaluate business implications | Evidence-based decision |

The lifecycle can be represented as:

Design
  |
  v
Planning and Sample Size
  |
  v
Design Approval
  |
  v
Experiment Launch
  |
  v
Random Assignment
  |
  v
Outcome Collection
  |
  v
Monitoring and Guardrails
  |
  v
Experiment Closure
  |
  v
Statistical Analysis
  |
  v
Business Decision

A draft experiment cannot accept assignments.

A completed experiment cannot accept new outcomes.

A stopped experiment can be analyzed using its available observations, but stopping early may compromise the intended statistical design.

## 8. Sample Ratio Mismatch

Sample Ratio Mismatch (SRM) occurs when the observed assignment distribution differs materially from the expected allocation.

For an expected 50:50 experiment:

\[
E_C=0.5N
\]

\[
E_T=0.5N
\]

The chi-square statistic is:

\[
\chi^2=
\sum_i\frac{(O_i-E_i)^2}{E_i}
\]

Where:

- \(O_i\): observed group count.
- \(E_i\): expected group count.

For two groups, the test has one degree of freedom.

The implementations use the chi-square survival probability to identify possible allocation mismatches.

An SRM alert can indicate:

- Assignment implementation defects.
- Incorrect participant eligibility.
- Unequal traffic allocation.
- Identity-resolution problems.
- Duplicate participants.
- Logging failures.
- Variant-specific data loss.

An SRM finding should trigger investigation before interpreting treatment performance.

The statistical significance threshold used for SRM monitoring is deliberately stringent in the examples.

## 9. Guardrail Metrics

A primary metric can improve while other important outcomes deteriorate.

For example, a redesigned checkout may increase conversion but also increase payment errors or page latency.

Guardrail metrics provide additional operational evidence.

Typical guardrails include:

| Guardrail | Risk |
|---|---|
| Page latency | Slower application performance |
| Payment failures | Revenue and customer impact |
| Refund rate | Lower transaction quality |
| Customer complaints | Poor user experience |
| Error rate | Reliability degradation |
| Retention | Long-term customer impact |

A guardrail should have an explicit measurement definition and acceptable threshold.

The SQL implementation includes guardrail observations and a variant-level aggregation view.

A production implementation should also define formal guardrail thresholds, monitoring windows, escalation rules, and automatic stopping conditions.

## 10. Python Implementation

The Python script provides a domain-oriented simulation and analysis engine.

### 10.1 Domain model

The implementation uses dataclasses to represent:

- `ExperimentConfig`
- `Participant`
- `VariantMetrics`
- `ExperimentResult`
- `Experiment`

Enums represent:

- Experiment status.
- Experimental variants.
- Outcome types.

This separation prevents experiment configuration, participant assignment, and statistical output from being mixed into a single structure.

### 10.2 Experiment state management

The experiment supports:

- Starting a draft experiment.
- Assigning participants.
- Recording conversion outcomes.
- Preventing duplicate outcomes.
- Completing an experiment.
- Stopping an experiment.
- Analyzing a closed experiment.

State validation prevents invalid operations.

### 10.3 Statistical analysis

`ExperimentAnalyzer` calculates:

- Participant counts.
- Conversion counts.
- Conversion rates.
- Revenue.
- Average revenue.
- Absolute lift.
- Relative lift.
- Pooled z-statistic.
- Two-sided p-value.
- Confidence interval.
- Statistical significance.
- Practical significance.

`ExperimentDesigner` estimates sample size using the normal approximation.

`SampleRatioMismatch` evaluates whether observed group counts differ from the planned allocation.

### 10.4 Execution

Run the file with Python 3.10 or later.

The program uses standard-library modules and does not require third-party packages.

The demonstration simulates 20,000 participants and evaluates a checkout conversion experiment.

## 11. JavaScript Implementation

The JavaScript implementation uses an event-driven architecture.

### 11.1 EventEmitter

The `Experiment` class extends Node.js `EventEmitter`.

It emits events when:

- An experiment starts.
- A participant is assigned.
- An outcome is recorded.
- An experiment completes.
- An experiment stops.

This separates experiment execution from operational monitoring.

### 11.2 Maps and immutable records

`Map` stores participant assignments and outcomes.

This provides direct lookup by participant identifier and avoids repeated linear searches.

The implementation uses immutable policy objects and frozen outcome records to reduce unintended changes after validation.

### 11.3 Asynchronous execution

The simulation processes participant batches through promises.

`Promise.all()` waits for each batch before continuing.

This demonstrates asynchronous workflow organization without requiring an external package.

The example uses a sequential experiment assignment service. A distributed production implementation would need atomic assignment persistence, idempotency controls, and appropriate concurrency handling.

### 11.4 Statistical evaluation

The JavaScript implementation provides:

- Normal distribution calculations.
- Inverse normal approximation.
- Sample size estimation.
- Two-proportion comparison.
- Confidence intervals.
- Significance evaluation.

Node.js built-in cryptographic hashing provides reproducible bucketing.

The simulation uses cryptographic random-number generation for conversion outcomes.

## 12. C++17 Implementation

The C++ implementation emphasizes explicit domain modeling, value structures, and controlled state transitions.

### 12.1 Core structures

The principal structures are:

| Structure | Responsibility |
|---|---|
| `ExperimentPolicy` | Validates experimental parameters |
| `Participant` | Stores assignment and outcome state |
| `GroupMetrics` | Aggregates group performance |
| `AnalysisResult` | Holds statistical comparison results |

Enums represent experimental variants and lifecycle states.

### 12.2 Experiment engine

The `Experiment` class manages:

- Experiment identity.
- Configuration.
- Participant registration.
- Variant assignment.
- Outcome recording.
- Experiment closure.
- Statistical analysis.

A `std::map` provides ordered participant storage and logarithmic lookup.

The implementation uses `std::mt19937` for reproducible simulation of outcomes.

The participant assignment mechanism uses the C++ standard-library hash function for the demonstration. Standard-library hash values are not guaranteed to remain identical across different implementations or versions. A production assignment service should use a specified stable hashing algorithm.

### 12.3 Statistical engine

The `Statistics` class implements:

- Standard normal cumulative distribution.
- Inverse normal approximation.
- Statistical critical values.

The `ExperimentDesigner` class handles sample size estimation.

The `SampleRatioMonitor` class identifies assignment imbalance.

The separation of these components makes it possible to test experimental execution independently of statistical calculations.

### 12.4 Complexity

For \(N\) participants:

| Operation | Approximate complexity |
|---|---|
| Assignment lookup | \(O(\log N)\) |
| Assignment insertion | \(O(\log N)\) |
| Outcome update | \(O(\log N)\) |
| Group aggregation | \(O(N)\) |
| Statistical comparison | \(O(1)\) |
| Sample size calculation | \(O(1)\) |

## 13. Java 17 Enterprise Implementation

The Java implementation models experiment governance as a service-oriented enterprise workflow.

### 13.1 Domain types

Java records represent immutable data:

- `ExperimentPolicy`
- `Participant`
- `Outcome`
- `GroupMetrics`
- `StatisticalResult`
- `ExperimentReport`

Enums distinguish variants, lifecycle states, and design-review decisions.

### 13.2 Design approval

Experiment design approval is separated from statistical analysis.

A design must be approved before the experiment can start.

This is an operational governance control rather than a statistical conclusion.

The approval process validates that the experiment has undergone the required review before participant assignment begins.

### 13.3 Service architecture

`ExperimentService` manages experiment execution and state transitions.

`SampleSizeCalculator` handles experimental planning.

`StatisticalFunctions` provides numerical calculations.

`ExperimentReportingService` creates a structured report.

The service uses synchronized methods to serialize operations within a single Java object.

This is not a replacement for distributed locking or database transactions when multiple application instances operate on the same experiment.

### 13.4 Enterprise considerations

A production enterprise implementation should persist:

- Experiment definitions.
- Approval decisions.
- Participant assignments.
- Outcomes.
- Metric definitions.
- Experiment versions.
- Statistical analysis versions.
- Audit records.

It should also maintain appropriate access controls and an immutable history of important experimental decisions.

## 14. PostgreSQL Database Architecture

The SQL implementation models the experiment lifecycle using relational structures.

### 14.1 Database relationship

The principal relationships are:

Experiments
  |
  +---- Experiment Variants
  |
  +---- Design Approvals
  |
  +---- Experiment Audit Log
  |
  +---- Experiment Assignments
             |
             +---- Participants
             |
             +---- Experiment Outcomes
             |
             +---- Guardrail Observations

The experiment identifier is the central relationship connecting the operational and analytical records.

### 14.2 Table responsibilities

| Table | Purpose |
|---|---|
| `experiments` | Experiment definition, hypothesis and policy |
| `experiment_variants` | Control and treatment configuration |
| `participants` | Participant identity |
| `experiment_assignments` | Randomization and variant allocation |
| `experiment_outcomes` | Conversion and revenue observations |
| `guardrail_observations` | Operational safety measurements |
| `design_approvals` | Design-review decisions |
| `experiment_audit_log` | Lifecycle and governance history |

### 14.3 Constraints and integrity

The database uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Enumerated types.
- Indexes.
- Trigger-based validation.

Examples include:

- Allocation ratios must be valid.
- Baseline conversion rates must be between zero and one.
- A participant cannot be assigned twice to the same experiment.
- An assignment must reference a variant belonging to its experiment.
- An outcome cannot be recorded for an unassigned participant.
- Outcomes cannot be inserted after experiment closure.
- Revenue cannot be negative.

### 14.4 Stored functions and procedures

The database provides:

| Function or procedure | Responsibility |
|---|---|
| `approve_experiment` | Records design approval or rejection |
| `start_experiment` | Validates and starts an approved experiment |
| `close_experiment` | Completes or stops a running experiment |
| `required_sample_size` | Estimates participants required per group |
| `inverse_standard_normal` | Calculates normal critical values |
| `analyze_experiment` | Produces variant-level metrics |
| `compare_experiment` | Performs statistical comparison |
| `check_sample_ratio` | Evaluates assignment imbalance |

The procedures use transactional database operations to preserve state consistency.

### 14.5 Views

`experiment_performance_report` provides a consolidated performance report.

`variant_guardrail_summary` aggregates operational metrics by experiment, variant, and guardrail.

These views support reporting without requiring repeated application-side joins.

### 14.6 Indexing

The database defines indexes on:

- Experiment-to-variant relationships.
- Experiment and variant assignment relationships.
- Assignment timestamps.
- Outcome timestamps.
- Experiment audit history.

These indexes support common filtering and reporting patterns.

For large production datasets, partitioning by experiment or time may be appropriate. Index selection should be validated against actual query plans and data volumes.

## 15. A/B Testing Failure Modes

Experimental results can be misleading even when the statistical calculations are correct.

| Failure mode | Description | Control |
|---|---|---|
| Selection bias | Groups differ systematically before treatment | Random assignment |
| Sample ratio mismatch | Assignment distribution differs from plan | SRM monitoring |
| Peeking | Repeatedly checking results and stopping on significance | Prespecified analysis plan |
| Multiple testing | Repeated tests increase false-positive risk | Multiplicity correction |
| Contamination | Participants experience both variants | Persistent assignment |
| Attrition | Outcomes are missing disproportionately | Missing-data monitoring |
| Novelty effect | Temporary behavior changes after launch | Adequate observation period |
| Seasonality | Time-dependent behavior affects results | Full business-cycle coverage |
| Metric manipulation | Outcome definitions change after launch | Metric governance |
| Simpson's paradox | Aggregated results hide subgroup differences | Prespecified segmentation |
| Instrumentation failure | Events are missing or duplicated | Data-quality checks |
| Interference | One participant's treatment affects another | Appropriate experimental unit |

### 15.1 Peeking and optional stopping

Repeatedly checking a conventional fixed-horizon p-value and stopping whenever it becomes significant can inflate the actual Type I error rate.

A fixed-horizon experiment should specify its sample size and stopping criteria before the analysis.

Experiments requiring continuous monitoring should use an appropriate sequential-testing method, alpha-spending approach, or other prespecified sequential design.

### 15.2 Multiple comparisons

Testing multiple treatments, metrics, and segments increases the probability of obtaining at least one false-positive result.

Methods such as Bonferroni correction and Holm's procedure can control family-wise error.

False discovery rate procedures may be appropriate when evaluating larger collections of hypotheses.

The implementations in this project perform a single primary two-sided comparison. They do not implement multiplicity correction.

### 15.3 Missing outcomes

Participants who receive an assignment but never produce an observed outcome require explicit treatment in the analysis plan.

The SQL schema distinguishes assignments from outcomes.

The reporting queries calculate the difference between assigned and observed participant counts.

The conversion-rate denominator in the supplied implementations is the number of participants with recorded outcomes, not the total number assigned.

This is a complete-case calculation. If outcome missingness differs by variant or relates to conversion probability, this approach can introduce bias. Production analyses should define the estimand and missing-data strategy in advance.

## 16. Security and Data Governance

Experimentation systems process participant identifiers and behavioral information.

Appropriate controls include:

- Pseudonymization of participant identifiers.
- Least-privilege database access.
- Encryption in transit and at rest.
- Restricted access to experiment configurations.
- Controlled outcome ingestion.
- Audit logging.
- Retention and deletion policies.
- Protection against duplicate event submission.
- Validation of externally supplied metrics.
- Separation of personally identifiable information from analytical datasets.

Participant identifiers should not contain unnecessary personal information.

Deterministic hashing supports assignment consistency but does not anonymize data or replace access controls.

The example SQL uses MD5 for reproducible simulation buckets. It is not intended as a security mechanism or as a production-quality randomization service.

## 17. Limitations of the Implementations

The five source files provide complementary educational implementations rather than a complete distributed experimentation platform.

| Area | Implementation | Limitation |
|---|---|---|
| Python | Stateful experiment simulator | In-memory persistence |
| JavaScript | Event-driven experiment engine | Single-process state |
| C++17 | Statistical and governance engine | No distributed storage |
| Java 17 | Enterprise-oriented experiment service | No external transaction manager |
| PostgreSQL | Relational experiment workflow | Simplified operational simulation |

The statistical implementations focus on independent binary outcomes and approximate two-proportion inference.

They do not provide complete implementations of:

- Welch's t-test for continuous outcomes.
- Mann-Whitney testing.
- Chi-square tests for arbitrary contingency tables.
- Fisher's exact test.
- Bayesian experimentation.
- Sequential testing.
- Cluster-randomized inference.
- CUPED variance reduction.
- Bootstrap confidence intervals.
- Multiple-testing corrections.
- Non-inferiority testing.
- Equivalence testing.
- Survival analysis.

These methods require different assumptions and statistical procedures.

The sample-size calculation assumes a conventional two-sided comparison with approximately equal group sizes. It should not be applied indiscriminately to every experiment design.

The SQL implementation also uses simplified synthetic data and demonstration-oriented assignment logic.

## 18. Running the Implementations

### Python

Requirements: Python 3.10 or later.

The program uses only the Python standard library.

### JavaScript

Requirements: Node.js 18 or later.

The program uses the built-in `crypto` and `events` modules.

### C++17

Requirements: A C++17-compatible compiler.

Compilation uses the standard language library and does not require third-party dependencies.

### Java 17

Requirements: JDK 17.

The source file is named `ABTestingEnterprise.java` to match its public class.

### PostgreSQL

Requirements: PostgreSQL 15 or later.

Execute the SQL script using a database account with permission to create schemas, tables, functions, procedures, and triggers.

The script creates the `ab_testing` schema and its demonstration experiment.

The script uses `CREATE ... IF NOT EXISTS` for the main database objects and `ON CONFLICT` for repeatable sample insertion. Existing objects are not automatically migrated when their definitions change.

## 19. Comparative Implementation Matrix

| Engineering dimension | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Experiment modeling | Dataclasses | Classes and objects | Structs and classes | Records and services | Relational tables |
| Assignment | Stable hash | SHA-256 | Standard hash | SHA-256 | Stored bucket |
| State management | Enum | Event-driven state | Enum | Explicit transitions | Enum and procedures |
| Outcome storage | Dictionary | Map | Ordered map | HashMap | Relational table |
| Sample size | Normal approximation | Normal approximation | Normal approximation | Normal approximation | Stored function |
| Statistical test | Two-proportion z-test | Two-proportion z-test | Two-proportion z-test | Two-proportion z-test | Two-proportion z-test |
| Confidence interval | Approximate Wald | Approximate Wald | Approximate Wald | Approximate Wald | Approximate Wald |
| Monitoring | SRM | Event monitor | SRM | Operational counters | SRM and views |
| Validation | Exceptions | Custom errors | Exceptions | Custom exceptions | Constraints and triggers |
| Reporting | Console report | Structured report | Console report | Report service | Views and functions |

## 20. Technical Interpretation

A/B testing combines experimental design, data collection, statistical inference, and operational governance.

The central distinction is between assignment, observation, and inference.

**Assignment** determines which intervention a participant receives.

**Observation** records what happens after that assignment.

**Inference** evaluates whether the observed differences provide sufficient evidence about the effect of the intervention.

These stages must remain distinguishable because a statistical test cannot correct a defective randomization process, incomplete instrumentation, inappropriate experimental unit, or biased outcome collection.

A valid experiment therefore requires both a defensible design and a statistically appropriate analysis.

The implementations demonstrate how the same experimental workflow can be represented through Python's domain modeling, JavaScript's event-driven architecture, C++17's explicit state management, Java's enterprise service design, and PostgreSQL's relational integrity and analytical operations.
