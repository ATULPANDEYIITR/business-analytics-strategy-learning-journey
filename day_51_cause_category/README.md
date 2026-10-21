# Root Cause Analysis: 5 Whys, Fishbone and Analytical Diagnosis

## Scope

This project models **Root Cause Analysis (RCA)** as a structured diagnostic process rather than as a collection of symptoms or guesses.

The implementations distinguish three complementary activities:

| Method | Primary purpose | Main question |
|---|---|---|
| 5 Whys | Trace a causal chain | Why did this event occur? |
| Fishbone analysis | Organize alternative cause classes | What categories could contribute to the problem? |
| Analytical diagnosis | Test and rank hypotheses using evidence | Which explanations are supported strongly enough to act on? |

The central principle is that a root cause should be supported by observable evidence and connected to the failure mechanism. A frequently observed symptom is not automatically the root cause.

The five implementations use different technical perspectives:

- **Python** models an incident investigation with objects, evidence, causal trees, validation, and hypothesis ranking.
- **JavaScript** provides an event-driven investigation model in which operational evidence arrives asynchronously and corrective actions are evaluated.
- **C++17** implements a diagnostic engine with explicit ownership of evidence, causal structures, and an actionability gate.
- **Java 17** models an enterprise diagnostic workflow using records, enums, interfaces, immutable evidence, policies, and domain services.
- **PostgreSQL** persists incidents, causes, evidence, Why chains, corrective actions, and measurements while enforcing structural integrity at the database level.

## Analytical Model

A useful RCA workflow separates the observable problem from its explanations:

    Observed Incident
           |
           +--------------------+
           |                    |
        5 Whys              Fishbone
           |                    |
      Causal chain       Alternative causes
           |                    |
           +---------+----------+
                     |
               Evidence Testing
                     |
              Supported Cause
                     |
            Corrective Control
                     |
            Measurement / Verification

The methods answer different questions and should not be collapsed into one technique.

### 5 Whys

The 5 Whys implementation represents a sequence of causal questions.

Each step contains:

- the Why question,
- the causal answer,
- supporting evidence,
- an optional relationship to a formal cause.

The sequence is constrained to five levels. This prevents an investigation object from silently becoming an unrestricted causal narrative.

The fifth answer is treated as the current root-cause candidate, not as unquestionable truth. The model deliberately keeps evidence attached to every step so the investigator can challenge weak links.

A typical chain represented by the implementations is:

    Payment requests failed
            ↓
    Database connection pool exhausted
            ↓
    Connections were not reliably released
            ↓
    Resource-pressure tests were absent
            ↓
    Acceptance criteria ignored resource lifecycle
            ↓
    Delivery process lacked operational-resource checks

The chain moves from an immediate failure mechanism toward a process-level condition that allowed the failure to escape detection.

## Fishbone Analysis

Fishbone analysis organizes alternative explanations into cause categories.

The project uses:

- People
- Process
- Technology
- Data
- Environment
- Management

The categories are not treated as mutually exclusive theories. They are investigation branches.

For example:

                             PEOPLE
                               |
                               |
    PROCESS ---------------- INCIDENT ---------------- TECHNOLOGY
                               |
                               |
                             DATA
                               |
                          MANAGEMENT
                               |
                          ENVIRONMENT

A cause can also have children. This permits a category such as Process to contain a more specific explanation.

For example:

    Process
      └── Release acceptance omitted resource-lifecycle verification
            └── Regression tests did not measure connection release

This hierarchical representation is useful when a broad fishbone branch contains several increasingly specific mechanisms.

## Evidence and Hypothesis Strength

The implementations assign evidence three levels:

| Strength | Score | Interpretation |
|---|---:|---|
| Weak | 1 | Observation provides limited support |
| Moderate | 2 | Observation provides meaningful but incomplete support |
| Strong | 3 | Direct or highly relevant evidence |

The evidence score is not a statistical probability. It is an investigation aid.

A high score becomes more useful when evidence comes from independent sources.

For example:

    Application metrics
            +
    Database telemetry
            +
    Source inspection
            ↓
    Stronger causal support

This prevents one duplicated observation from being mistaken for several independent confirmations.

The Python, JavaScript, C++, and Java implementations therefore expose evidence scores and, where appropriate, independent-source checks.

## Python Implementation

The Python program models an RCA investigation through domain classes.

`Evidence` represents an observation and its source. `Cause` represents a possible explanation and can contain child causes. `FiveWhys` enforces the five-level causal chain.

`RCA` combines the structures into an investigation and ranks hypotheses by evidence score.

The incident scenario concerns database connection exhaustion after a deployment. The analysis distinguishes:

- connection-pool saturation as the immediate failure mechanism,
- missing resource cleanup as a technical cause,
- insufficient resource-pressure testing as a process cause,
- monitoring limitations as a data/observability cause,
- delivery criteria as a management/process factor.

The script also validates measurements before and after a corrective action. This is important because an RCA should not stop at identifying a cause. The proposed correction should produce an observable change in the relevant failure metric.

The recurring-signal analysis uses Python's `Counter` to identify repeated failure observations without introducing external dependencies.

Validation covers empty problem statements, malformed evidence, unsupported categories, invalid measurement directions, and excessive Why levels.

## JavaScript Implementation

The JavaScript implementation uses a different perspective.

The investigation engine supports asynchronous evidence collection. Metrics, logs, and test results are simulated as independent asynchronous sources and combined with `Promise.all`.

This reflects an operational investigation in which information can originate from separate systems.

The implementation also introduces corrective actions with a measurement function:

    Evidence
       ↓
    Hypothesis
       ↓
    Corrective Action
       ↓
    Measurement
       ↓
    Verified / Not Verified

The `RCAEngine` keeps fishbone causes and hypotheses separate from the Five Whys chain.

This distinction matters because a Why chain describes one causal path, while a fishbone can contain several competing hypotheses.

The JavaScript implementation uses `Map` for dynamic category and signal storage and validates malformed evidence before it enters the diagnostic model.

Failure handling occurs at the top-level asynchronous boundary so investigation failures produce a non-zero process status.

## C++17 Implementation

The C++ program models RCA as a technical diagnostic case study for a manufacturing motor shutdown.

The domain contains:

- `Evidence`,
- `Cause`,
- `FiveWhys`,
- `MergeGate`,
- measurement validation,
- recurring failure signals.

The manufacturing scenario demonstrates a condition-based maintenance problem:

    Motor shutdown
          ↓
    Thermal threshold reached
          ↓
    Cooling airflow decreased
          ↓
    Filter became obstructed
          ↓
    Replacement interval ignored dust conditions
          ↓
    Maintenance did not use pressure telemetry

The fishbone model then separates Process, Technology, and Data explanations.

A `MergeGate` represents an analytical decision rule. A hypothesis is considered actionable only when its evidence score passes a threshold and sufficient independent evidence sources exist.

This is deliberately different from simply selecting the most frequently mentioned cause.

The program uses standard C++17 containers and algorithms. No external framework is required.

The measurement comparison demonstrates how a corrective control can be evaluated using before-and-after observations.

## Java 17 Implementation

The Java implementation models an enterprise diagnostic service for warehouse label-printing failures.

Java records provide compact immutable representations for:

- evidence,
- Why steps,
- diagnostic context.

Enums constrain category and evidence values.

The `DiagnosticRule` interface provides a point for policy-based evaluation without coupling the domain model to a specific diagnostic implementation.

`GovernancePolicy` makes the evidence threshold explicit:

    Evidence score threshold
            +
    Independent-source threshold
            ↓
    Actionability decision

The scenario identifies unbounded printer retries as a technical mechanism and missing resilience acceptance criteria as a process cause.

The model therefore separates:

- the runtime mechanism that consumed worker capacity,
- the process condition that permitted the behavior,
- the data/observability limitation that failed to connect timeout evidence to an automatic control.

The enterprise-oriented design makes policy decisions explicit instead of embedding them inside reporting code.

## PostgreSQL Data Model

The PostgreSQL implementation treats RCA as persistent relational data.

The core relationships are:

    incidents
       |
       +---- evidence
       |
       +---- causes
       |       |
       |       +---- cause_evidence ---- evidence
       |
       +---- why_steps
       |       |
       |       +---- why_evidence ---- evidence
       |
       +---- corrective_actions
       |
       +---- measurements

`incidents` stores the failure event and its lifecycle.

`evidence` records observations and their sources.

`causes` stores fishbone hypotheses and supports parent-child relationships for hierarchical diagnosis.

`cause_evidence` creates a many-to-many relationship because one observation can support several hypotheses and one hypothesis can require several observations.

`why_steps` represents the causal sequence independently from the fishbone structure.

`why_evidence` links observations to individual Why steps.

`corrective_actions` connects a proposed intervention to a cause and records ownership, status, target date, and effectiveness criteria.

`measurements` supports before-and-after validation.

## Database-Level Integrity

The schema uses constraints to prevent invalid analytical structures.

The `why_steps.step_number` constraint limits the sequence to one through five.

A trigger verifies that a later Why step cannot be inserted without the preceding step.

Another trigger prevents multiple active root causes for the same incident.

Foreign keys ensure that evidence, causes, Why steps, and corrective actions cannot silently reference nonexistent incidents.

The schema also uses indexes for recurring query patterns:

- evidence retrieval by incident and strength,
- cause retrieval by incident and category,
- measurement retrieval by incident, metric, and phase.

These indexes target actual investigation queries rather than indexing every column indiscriminately.

## PostgreSQL Diagnostic Functions and Views

`evidence_score()` calculates the combined strength of evidence associated with a cause.

`evaluate_cause()` combines evidence score with the number of independent evidence sources. Its result is a diagnostic classification such as `SUPPORTED`, `PLAUSIBLE`, or `WEAK`.

`cause_diagnostic_report` provides a reporting view containing:

- category,
- hypothesis,
- evidence score,
- independent-source count,
- hypothesis status.

`why_chain` exposes the causal sequence in a form suitable for investigation reports.

`measurement_comparison` calculates average before-and-after values and indicates whether the measured value decreased.

The recursive `cause_tree` query traverses hierarchical fishbone causes.

## Corrective-Action Verification

Identifying a plausible root cause is only one stage of RCA.

The project therefore models corrective controls and measurements:

    Root-cause hypothesis
            ↓
    Corrective action
            ↓
    Target metric
            ↓
    Before measurement
            ↓
    Control implemented
            ↓
    After measurement
            ↓
    Effectiveness decision

For the payment-service scenario, connection utilization is measured before and after the corrective control.

A lower post-control average supports effectiveness, but it does not by itself prove causality. Production verification should also consider workload differences, unrelated infrastructure changes, sampling periods, and recurrence over time.

## Distinguishing Cause from Symptom

A recurring RCA failure is stopping at the first observable condition.

For example:

| Observation | Diagnostic interpretation |
|---|---|
| Payment requests failed | Incident symptom |
| Connection pool was exhausted | Immediate failure mechanism |
| Connections were not released | Technical cause |
| Resource-pressure tests were absent | Process cause |
| Acceptance criteria omitted resource lifecycle | Deeper process condition |

The distinction prevents a corrective action such as "restart the service" from being treated as a root-cause solution.

A restart may remove the immediate symptom while leaving the connection leak unchanged.

## Failure Modes in RCA

The implementations account for several common analytical failures.

### Confirmation bias

An investigator may select the first plausible explanation and stop collecting evidence.

Evidence scoring and competing fishbone hypotheses encourage comparison.

### Single-source evidence

One log message can be misleading. Independent sources such as metrics, database telemetry, tests, and source inspection provide stronger support.

### Symptom substitution

Treating an alert as the root cause can produce a weak corrective action. The alert indicates that something happened; it does not necessarily explain why it happened.

### Incomplete causal chains

A Why chain can stop at an implementation detail even though a process condition allowed that implementation defect to reach production.

### Measurement without context

Before-and-after measurements can change for reasons unrelated to the corrective action. Measurements should therefore be interpreted with workload and environmental context.

### Multiple plausible causes

Fishbone analysis intentionally allows multiple hypotheses. The investigator should not force every incident into one category prematurely.

## Security and Operational Considerations

RCA data can contain sensitive operational information, including infrastructure identifiers, error messages, employee information, and system behavior.

Production implementations should therefore apply:

- access control to incident records,
- least-privilege database roles,
- careful handling of application logs,
- removal of credentials and secrets from evidence,
- immutable audit records where investigation integrity matters,
- retention policies appropriate to organizational requirements,
- controlled modification of finalized root-cause records.

Evidence should describe an observation without exposing secrets unnecessarily.

For example, a database error can be recorded as a connection-pool exhaustion event rather than storing a complete connection string containing credentials.

## Performance Considerations

The in-memory implementations are designed for small to medium investigation models.

Sorting hypotheses by evidence score costs approximately `O(h log h)` for `h` hypotheses.

Evidence aggregation is linear in the number of evidence records associated with a cause.

The PostgreSQL implementation moves aggregation into SQL so large incident collections can be queried without loading every record into application memory.

Indexes are placed on columns used by incident-level evidence, category, and measurement queries.

The recursive cause query is appropriate for moderate diagnostic trees. Extremely deep or highly connected causal graphs would require additional controls on traversal depth and cycle prevention.

## Practical Diagnostic Workflow

A disciplined investigation represented by these artifacts follows this structure:

    Capture the incident
            ↓
    Define the observable failure precisely
            ↓
    Build a Five-Whys causal chain
            ↓
    Create alternative Fishbone hypotheses
            ↓
    Attach evidence to hypotheses
            ↓
    Compare independent evidence sources
            ↓
    Identify the strongest supported cause
            ↓
    Define a corrective control
            ↓
    Measure the relevant outcome
            ↓
    Verify whether the failure mechanism changed
            ↓
    Record the result

The important separation is maintained throughout:

- **5 Whys** structures a causal chain.
- **Fishbone** organizes alternative causes.
- **Analytical diagnosis** evaluates those causes against evidence.
- **Corrective-action verification** checks whether the intervention changed the relevant behavior.
