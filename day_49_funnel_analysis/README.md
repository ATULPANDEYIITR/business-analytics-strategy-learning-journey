# Funnel Analysis

## Scope

Funnel analysis measures how a population moves through an ordered sequence of customer-journey stages. The central question is not simply how many customers converted, but where customers stopped, how quickly they progressed, and whether conversion behavior differs between segments.

This implementation models an ecommerce journey with five distinct stages:

`Visited Landing Page → Viewed Product → Added to Cart → Started Checkout → Purchased`

The stages are deliberately kept separate because each represents a different behavioral state. A landing-page visit establishes the entry population. Product viewing indicates engagement with an offer. Cart creation represents stronger purchase intent. Checkout initiation indicates a customer has crossed into the transaction workflow. Purchase is the terminal conversion event.

A funnel is therefore a measurement model rather than merely a count of successful transactions.

## Funnel Mechanics

For a stage `S`, the stage population is the number of distinct customers who reached that stage.

The transition conversion rate is:

`conversion(S) = users reaching S / users reaching previous stage`

The stage drop-off is:

`drop-off(S) = 1 - conversion(S)`

Entry-based conversion is different:

`entry conversion(S) = users reaching S / users entering the funnel`

These measures answer different questions. Transition conversion identifies weakness between adjacent stages, while entry conversion shows how much of the original audience survives to a given point.

For the supplied data, customers can legitimately stop at different stages. A customer who reaches checkout but does not purchase is not treated as having an invalid record. The missing purchase event is itself useful funnel information.

## Customer Journey Representation

The Python implementation represents each journey with a customer identifier, segment, ordered stage timestamps, and realized revenue. It validates:

- stage names against the configured funnel;
- duplicate customer identifiers;
- non-negative revenue;
- increasing stage order;
- chronological event timestamps.

The JavaScript implementation represents events with a `Map` and uses `EventEmitter` to expose journey-registration and report-generation events. This makes the implementation event-driven rather than simply translating the Python data model.

The C++ implementation uses `enum class Stage` to prevent accidental mixing of arbitrary strings with stage identifiers. Event ordering is validated numerically through the enum's stage order.

The Java implementation separates `FunnelStage`, `FunnelEvent`, `CustomerJourney`, `FunnelPolicy`, and `FunnelService`. The explicit domain types make customer state and conversion policy independently testable.

The PostgreSQL implementation stores stages and events relationally. A missing row in `customer_events` represents a customer who did not reach that stage.

## Measuring Drop-Off

The most useful funnel diagnostic is often the transition with the largest customer loss.

The analysis calculates each stage's population and compares it with the immediately preceding stage. This avoids a misleading interpretation in which all losses are attributed to the final conversion step.

The supplied sample contains:

| Stage | Customers Reaching Stage |
| --- | ---: |
| Visited Landing Page | 10 |
| Viewed Product | 10 |
| Added to Cart | 8 |
| Started Checkout | 6 |
| Purchased | 4 |

The transition from product viewing to cart creation loses two customers, the checkout transition loses two customers, and the purchase transition loses two customers. The analytical code does not assume which transition is problematic; it derives the largest loss from the observed data.

## Segmentation

Aggregate conversion can hide materially different behavior between customer groups.

The implementations therefore segment journeys by `mobile`, `desktop`, and `tablet`.

The segment analysis calculates:

- total users;
- completed purchases;
- conversion rate;
- realized revenue.

The conversion rate is based on the complete segment population, not only on users who reached an intermediate stage. This makes segment rates comparable at the top of the funnel.

Segment-level analysis can then be combined with stage-level analysis. A segment may have strong overall conversion while still exhibiting a specific stage bottleneck. The SQL implementation is structured so the same event data can be grouped by segment and stage without duplicating customer records.

## Time to Conversion

A conversion funnel also contains a temporal dimension.

The programs calculate the elapsed time between landing and purchase for completed journeys. The Python implementation reports mean, median, minimum, and maximum duration. The JavaScript and Java implementations emphasize median duration, while the SQL implementation calculates the median using PostgreSQL's `percentile_cont`.

Median duration is particularly useful when a small number of unusually slow journeys would distort the arithmetic mean.

The data model records timestamps for every stage, which also makes it possible to study individual transition times rather than only total journey duration.

## Customer Paths

A strict funnel assumes a fixed sequence, but real event data can contain partial journeys. The implementations preserve those partial paths.

Examples represented by the sample include:

`Visited Landing Page → Viewed Product`

`Visited Landing Page → Viewed Product → Added to Cart`

`Visited Landing Page → Viewed Product → Added to Cart → Started Checkout`

`Visited Landing Page → Viewed Product → Added to Cart → Started Checkout → Purchased`

Path distribution makes abandonment visible without inventing an artificial event for customers who never reached a later stage.

## Python Implementation

The Python program uses `FunnelStage`, `CustomerJourney`, `FunnelMetrics`, and `SegmentReport` data classes to make the analysis records explicit.

`FunnelAnalyzer.stage_metrics()` calculates adjacent-stage conversion, entry conversion, drop-off, and median transition time. `segment_analysis()` groups journeys by customer segment. `time_to_conversion()` measures complete-journey duration. `identify_largest_dropoff()` finds the most severe transition loss.

The script also exports two operational artifacts:

- `funnel_output/funnel_report.json` contains stage, segment, timing, revenue, and path information.
- `funnel_output/funnel_stage_metrics.csv` provides tabular stage metrics for spreadsheet or reporting workflows.

The validation demonstration intentionally submits an event sequence with timestamps moving backwards. The analyzer rejects it instead of silently producing a misleading funnel.

## JavaScript Implementation

The JavaScript implementation uses an event-driven design.

`CustomerJourney.recordEvent()` enforces stage ordering and timestamp monotonicity. `FunnelAnalyzer` extends Node.js `EventEmitter`, emitting `journeyAdded` when a customer journey is registered and `reportWritten` after asynchronous report persistence.

The asynchronous `writeReport()` method uses Node.js `fs/promises` rather than blocking file operations. The generated JSON includes stage metrics, segment metrics, largest drop-off, median conversion time, and observed paths.

This design is useful when funnel data is produced continuously by application events rather than supplied as one static dataset.

## C++ Case Study

The C++ program models the funnel as a typed analytics system.

`enum class Stage` provides compile-time stage identity. `Event` stores the stage and relative event time. `Pull` represents a customer journey, including segment, events, and revenue.

`FunnelValidation` centralizes journey validation. It prevents duplicate stages, backward stage movement, backward timestamps, invalid customer identifiers, and negative revenue.

`RepositoryGovernanceCaseStudy` is the main analytics service. Despite the generic service name, its internal scenario is specifically an ecommerce customer journey. It calculates stage metrics, segment performance, largest drop-off, median conversion time, and observed customer paths.

The C++ implementation uses `vector` for ordered event storage, `map` for deterministic segment and path reporting, `set` for detecting duplicate stages, and `optional` for measurements that legitimately may not exist, such as conversion time when no customer completed the funnel.

## Java Implementation

The Java implementation models funnel behavior as an enterprise domain service.

`FunnelStage` is an enum representing the controlled vocabulary of the funnel. `FunnelEvent` is an immutable record containing a stage and timestamp offset. `CustomerJourney` owns the ordered events and prevents invalid state transitions.

The `FunnelPolicy` interface separates the definition of conversion from the analytics service. `CompletedJourneyPolicy` currently defines conversion as reaching the purchase stage. This separation matters because a production organization may define different conversion policies for different business funnels.

`FunnelService` performs aggregation, segmentation, path analysis, and timing calculations. Java Streams are used for grouping, filtering, aggregation, and ordering where they make the analytical transformation explicit.

The model also distinguishes `Optional`-style absence from a numerical zero. For example, no completed journey means that a median conversion time does not exist. It should not be represented as zero minutes.

## PostgreSQL Data Model

The SQL implementation uses the `funnel_analysis` schema and separates funnel configuration from observed behavior.

`funnels` defines the analytical funnel.

`funnel_stages` defines the ordered stages belonging to a funnel.

`customers` stores customer identity and segment.

`customer_events` stores the actual stage transitions and timestamps.

`purchases` stores realized purchase transactions and connects them to the corresponding purchase-stage event.

This separation prevents analytical definitions from being mixed with customer observations.

### Integrity Constraints

The database enforces several rules directly:

- `funnel_stages` requires unique stage keys within a funnel.
- Stage order is unique within a funnel.
- Customer external identifiers are unique.
- A customer cannot have the same stage recorded twice for the same funnel because of the composite uniqueness constraint on `customer_events`.
- Revenue cannot be negative.
- Purchase amounts must be positive.
- Foreign keys prevent orphaned stage events and purchases.

Database constraints are important because application-level validation alone does not protect data when multiple services or ingestion processes write to the same database.

## SQL Analysis

The SQL queries use PostgreSQL window functions to compare each stage with the preceding stage.

`LAG(reached_users)` provides the previous-stage population. `FIRST_VALUE(reached_users)` provides the funnel-entry population. These values allow transition conversion and entry conversion to be calculated from the same stage-count relation.

The largest-drop query orders transition losses and returns the most significant observed stage loss.

The time-to-conversion query uses PostgreSQL's `percentile_cont(0.5)` to calculate the median elapsed duration.

The path query uses `string_agg` ordered by stage position so partial customer journeys can be grouped into meaningful behavioral paths.

The reusable `funnel_conversion_summary` view exposes stage populations and entry-based conversion for reporting applications.

## Funnel Versus Simple Conversion Rate

A simple conversion rate might report:

`purchases / visitors`

That number is useful but incomplete.

Funnel analysis adds the intermediate states required to explain the result:

`visitors → product viewers → cart creators → checkout starters → purchasers`

If overall conversion declines, the funnel can show whether the change originated in product engagement, cart creation, checkout initiation, or final purchase completion.

This distinction prevents a final conversion metric from being treated as an explanation of customer behavior.

## Edge Cases

A robust funnel implementation must distinguish several cases.

A customer who never reaches the second stage is an abandonment after entry, not an invalid record.

A customer who reaches checkout but not purchase is a valid incomplete journey.

A customer with an event occurring before the previous event is invalid because the resulting sequence cannot represent a coherent journey.

A duplicate event for the same stage may indicate duplicate telemetry, repeated ingestion, or an incorrectly designed event model. The implementations reject it rather than silently counting it twice.

A funnel with no customers has zero measurable conversion but does not have a meaningful median conversion duration.

A segment with zero users must not cause division-by-zero errors.

Revenue should be counted only when a completed purchase is represented. Cart intent is not realized revenue.

## Performance Considerations

For in-memory implementations, stage analysis scans customer journeys repeatedly. With `n` journeys and a fixed number of funnel stages, the practical cost is approximately `O(n × s)`, where `s` is the number of stages.

Because real funnels usually contain a small number of stages, this is straightforward for moderate datasets.

For database workloads, indexes are more important. The PostgreSQL implementation indexes funnel-stage-time combinations for stage aggregation and customer-time combinations for journey reconstruction. Segment indexing supports segment-based analysis.

At larger scale, event storage may require partitioning, incremental aggregation, precomputed daily funnel tables, or columnar analytical storage. The underlying analytical definitions remain the same, but the execution strategy changes.

## Security and Data Quality

Funnel analysis frequently processes customer identifiers and behavioral timestamps. Production systems should minimize personally identifiable information in analytical tables and use stable pseudonymous identifiers when direct identity is unnecessary.

Event ingestion should validate timestamps, event names, funnel identifiers, and revenue fields before they enter analytical storage.

Revenue should not be inferred from a page-view event. It should originate from a trusted transaction source.

Duplicate events can inflate stage populations if customers are counted as events instead of distinct users. The SQL queries therefore use `COUNT(DISTINCT customer_id)` for stage populations.

A funnel should also have a clearly defined attribution window. Without one, a purchase made long after the initial interaction may be incorrectly attributed to an earlier journey.

## Interpretation Limits

A funnel identifies where observed customer volume decreases. It does not by itself establish why the decrease occurred.

A high checkout drop-off may be associated with payment errors, unexpected shipping costs, authentication friction, product availability, or measurement problems. Funnel analysis identifies the location of the loss; other evidence is required to determine causality.

Likewise, segment differences are descriptive unless the analysis controls for factors such as traffic source, product mix, geography, device capability, campaign exposure, and customer tenure.

The strongest interpretation therefore combines funnel counts, event timing, segment behavior, data-quality checks, and the operational context surrounding each stage.

## Practical Analytical Relationship

The five implementations preserve the same conceptual relationship:

`Customer Events → Ordered Journey → Stage Populations → Transition Rates → Drop-Off Diagnosis`

The implementation boundaries differ by language:

| Implementation | Primary technical perspective |
| --- | --- |
| Python | Data validation, analytical functions, segmentation, timing, and report export |
| JavaScript | Event-driven journey capture and asynchronous report generation |
| C++ | Strongly typed funnel state and efficient in-memory analytical structures |
| Java | Enterprise domain modeling, explicit policies, immutable records, and service abstractions |
| PostgreSQL | Relational event storage, integrity constraints, window functions, aggregation, and reporting views |

The common analytical model makes the results comparable while allowing each implementation to demonstrate techniques appropriate to its execution environment.
