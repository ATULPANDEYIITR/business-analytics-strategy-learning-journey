# Customer Journey Analytics

## 1. Project Overview

Customer Journey Analytics examines how customers interact with an organization across digital and physical touchpoints.

It combines event collection, identity resolution, behavioral analysis, sessionization, conversion measurement, attribution, and customer retention analysis.

The project implements a complete analytical workflow using five technologies:

| Implementation | Engineering perspective |
|---|---|
| Python | Repository-style simulation, analytical algorithms, validation, and reporting |
| JavaScript | Event-driven collection, asynchronous processing, and behavioral state management |
| C++17 | Efficient event processing, domain modeling, and analytical computation |
| Java 17 | Enterprise-oriented services, immutable records, and domain-driven architecture |
| PostgreSQL | Relational event storage, integrity enforcement, analytical views, and reporting |

The demonstration represents an e-commerce business operating several acquisition channels.

Customers interact through advertising, search engines, product pages, shopping carts, checkout, and purchase events.

The system measures how these interactions contribute to customer conversion and revenue.

## 2. Customer Journey Fundamentals

A customer journey is the sequence of interactions between a customer and an organization.

A touchpoint is an individual interaction that can be recorded and analyzed.

Examples include:

- Viewing an advertisement.
- Clicking a search result.
- Visiting a landing page.
- Searching for a product.
- Viewing a product description.
- Adding a product to a shopping cart.
- Starting checkout.
- Completing a purchase.
- Registering an account.
- Contacting customer support.

An event represents one recorded occurrence of a touchpoint.

A customer journey consists of multiple events connected through customer identity and chronological relationships.

### 2.1 Journey structure

The analytical relationship is:

Customer
→ Identity
→ Sessions
→ Touchpoints
→ Behavioral Events
→ Journey Stages
→ Conversion
→ Revenue Attribution
→ Retention

A customer may have several sessions, and each session may contain multiple touchpoints.

A customer can also interact with multiple acquisition channels before purchasing.

### 2.2 Important terminology

| Term | Meaning |
|---|---|
| Customer | An identifiable individual interacting with an organization |
| Identity | An identifier associated with a customer |
| Touchpoint | An interaction between a customer and an organization |
| Event | A structured record of an interaction |
| Session | A collection of related events during an activity period |
| Journey | A sequence of customer interactions |
| Funnel | An ordered representation of conversion stages |
| Attribution | Assignment of conversion credit to marketing interactions |
| Cohort | A group of customers sharing a defined starting characteristic |
| Retention | Continued customer activity over time |
| Segmentation | Grouping customers according to behavioral characteristics |
| Conversion | Completion of a defined business objective |

## 3. Customer Journey Stages

The implementations use four analytical stages.

### 3.1 Awareness

Awareness represents initial exposure to a product, service, or organization.

Typical events:

- Advertisement impression.
- Advertisement click.
- Landing-page visit.
- General website visit.

The objective is to understand how potential customers discover the organization.

Relevant measurements include impressions, reach, clicks, traffic sources, and landing-page engagement.

### 3.2 Consideration

Consideration represents active evaluation of available products or services.

Typical events:

- Product search.
- Product-page viewing.
- Comparison activity.
- Adding products to a cart.

The objective is to understand whether customers demonstrate meaningful purchase intent.

Relevant measurements include product engagement, search behavior, cart additions, and product abandonment.

### 3.3 Conversion

Conversion represents completion of a defined business objective.

In the demonstration, the primary conversion is a completed purchase.

Typical events:

- Checkout initiation.
- Payment completion.
- Purchase confirmation.

Important measurements include:

- Purchase conversion rate.
- Average order value.
- Revenue.
- Cart abandonment.
- Checkout abandonment.

### 3.4 Retention

Retention examines interactions after initial conversion.

Typical events include account registration, repeat purchases, and customer support interactions.

The objective is to understand whether customers continue engaging with the organization.

Relevant measurements include repeat purchase rate, retention rate, customer activity, and customer lifetime value.

## 4. Event Collection and Data Modeling

All five implementations use a structured touchpoint model.

A typical event contains:

| Attribute | Description |
|---|---|
| Event ID | Unique event identifier |
| Customer ID | Customer associated with the interaction |
| Session ID | Session containing the interaction |
| Event type | Type of interaction |
| Timestamp | Time of occurrence |
| Channel | Acquisition or interaction channel |
| Page | Page or application location |
| Campaign | Associated marketing campaign |
| Value | Monetary value when applicable |
| Properties | Additional structured event attributes |

### 4.1 Event types

The implementations support:

- `ad_impression`
- `ad_click`
- `page_view`
- `product_view`
- `search`
- `add_to_cart`
- `checkout`
- `purchase`
- `signup`
- `support_request`

These event types represent different behavioral actions and must not be treated as equivalent.

A product view indicates interest, while a purchase indicates a completed commercial transaction.

### 4.2 Event validation

Event validation prevents invalid information from entering the analytical system.

The implementations validate:

- Required identifiers.
- Valid event types.
- Valid acquisition channels.
- Timestamp availability.
- Nonnegative monetary values.
- Positive purchase values.
- Valid page identifiers.
- Customer existence.
- Customer consent.

Duplicate events are rejected using unique event identifiers.

Validation is particularly important because duplicate purchases, incorrect timestamps, and malformed event values can distort business metrics.

### 4.3 Event-driven architecture

The JavaScript implementation uses Node.js `EventEmitter`.

An event is collected and emitted to interested application components.

The processing relationship is:

Event Collection
→ Validation
→ Consent Verification
→ Event Storage
→ Event Notification
→ Journey State Processing
→ Analytical Reporting

Asynchronous ingestion uses Promises and a serialized processing queue.

This makes the implementation useful for understanding event-driven analytical applications.

## 5. Customer Identity Resolution

Identity resolution connects multiple identifiers belonging to the same customer.

A customer might interact through:

- A web browser.
- A mobile device.
- An authenticated account.
- An anonymous session.

For example, a browser identifier can be associated with an existing customer account after authentication.

The identity registry maintains the relationship between external identifiers and customer identifiers.

The implementations reject an identifier that is already associated with another customer.

This prevents accidental identity collisions.

Identity resolution is essential for cross-session and cross-device journey analysis.

It must not assume that two anonymous devices belong to the same individual without an appropriate matching basis.

## 6. Sessionization

Sessionization converts a continuous event stream into meaningful activity sessions.

A session represents a group of related interactions occurring within a defined activity period.

The implementations use a 30-minute inactivity threshold.

A new session is created when:

1. A customer has no previous session.
2. The session identifier changes.
3. The inactivity threshold is exceeded.

Session duration is calculated as:

`Session Duration = Last Event Timestamp - First Event Timestamp`

Important session measurements include:

- Number of sessions.
- Average session duration.
- Events per session.
- Entry channel.
- Exit page.
- Session-level purchases.

A session with only one event has a duration of zero under this calculation.

This does not mean the visitor spent no time on the page. It means the available event data cannot establish a longer duration.

A production implementation may use heartbeat events, page visibility signals, or explicit session-end events to improve duration estimates.

## 7. Customer Funnel Analysis

A conversion funnel represents an ordered sequence of customer activities.

The demonstration uses five stages:

Page View
→ Product View
→ Add to Cart
→ Checkout
→ Purchase

The objective is to identify where customers stop progressing toward conversion.

### 7.1 Funnel conversion rate

The conversion rate between consecutive stages is:

\[
CR_i = \frac{N_i}{N_{i-1}}\times100
\]

Where:

- \(N_i\) represents customers reaching the current stage.
- \(N_{i-1}\) represents customers reaching the preceding stage.

### 7.2 Drop-off rate

\[
DropOff_i = 1-CR_i
\]

For example, if 100 customers view a product and 40 add it to their cart:

- Product viewers: 100.
- Cart additions: 40.
- Stage conversion: 40%.
- Drop-off: 60%.

### 7.3 Ordered conversion

The implementations use chronological event ordering.

A customer must reach the defined stages in sequence.

A purchase without the required preceding events does not automatically count as a completed journey in the sequential funnel.

This distinction matters when event collection is incomplete.

The SQL implementation also provides a relational funnel representation using timestamp comparisons.

For production use, funnel reporting should define its attribution window, treatment of repeated events, entry conditions, and whether customers can enter the funnel at intermediate stages.

## 8. Multi-Touch Attribution

Attribution determines how conversion credit is distributed across customer touchpoints.

A customer may encounter several channels before completing a purchase.

For example:

Social Advertisement
→ Organic Search
→ Product Page
→ Email Campaign
→ Purchase

Assigning all purchase credit to the last interaction ignores earlier interactions.

Multi-touch attribution provides alternative methods for distributing credit.

### 8.1 First-touch attribution

First-touch attribution assigns all conversion credit to the first recorded touchpoint.

\[
Credit_{first}=1
\]

It is useful for studying customer acquisition.

Limitation: It ignores later interactions that may have influenced conversion.

### 8.2 Last-touch attribution

Last-touch attribution assigns all credit to the final recorded touchpoint.

\[
Credit_{last}=1
\]

It is useful for studying the final interaction before conversion.

Limitation: It ignores earlier customer interactions.

### 8.3 Linear attribution

Linear attribution distributes credit equally across all recorded touchpoints.

\[
Credit_i=\frac{1}{n}
\]

Where \(n\) is the number of touchpoints.

For four interactions, each receives 25% credit.

Repeated interactions from the same channel are aggregated in the channel-level results.

### 8.4 Position-based attribution

Position-based attribution assigns:

- 40% to the first interaction.
- 40% to the last interaction.
- 20% to intermediate interactions.

For intermediate interactions:

\[
Credit_{middle}=\frac{0.20}{n-2}
\]

When the first and last interaction belong to the same channel, their credits are combined.

When only one touchpoint exists, it receives 100% credit.

### 8.5 Revenue allocation

Revenue attribution distributes purchase value according to attribution weights.

\[
AttributedRevenue_i=PurchaseRevenue\times Credit_i
\]

For a purchase worth ₹1,499, a channel receiving 40% credit receives ₹599.60 in attributed revenue.

Attribution represents a measurement model, not proof that a particular channel caused a purchase.

The models in this project are deterministic rule-based models. They do not estimate causal effects.

## 9. Behavioral Segmentation

Behavioral segmentation groups customers according to observed interactions.

The implementations classify customers into six categories.

| Segment | Classification condition |
|---|---|
| Visitor | Limited activity without conversion |
| Engaged visitor | More than three recorded events |
| Cart abandoner | Added to cart without purchasing |
| Converted customer | Completed one purchase |
| Repeat customer | Completed multiple purchases |
| Support engaged | Recorded a support request |

The classification uses a defined priority order.

For example, a customer who purchased and subsequently submitted a support request is classified as support engaged.

These categories are mutually exclusive in the demonstration.

Real organizations may use overlapping segments, where one customer can simultaneously be a repeat purchaser, a high-value customer, and a support-engaged customer.

Behavioral segmentation can support campaign targeting, customer experience analysis, and product improvement.

## 10. Cohort Analysis and Retention

Cohort analysis groups customers according to a shared starting period.

The implementations use registration month as the cohort definition.

For example:

- October 2026 cohort.
- November 2026 cohort.
- December 2026 cohort.

Customer activity is then measured across subsequent months.

### 10.1 Retention rate

\[
RetentionRate =
\frac{ActiveCustomers}{OriginalCohortSize}\times100
\]

If 100 customers register in October and 60 remain active in November:

\[
RetentionRate=\frac{60}{100}\times100=60\%
\]

The SQL implementation generates cohort retention records using monthly activity and registration periods.

The Python, JavaScript, and Java implementations calculate the same fundamental relationship using in-memory collections.

Cohort analysis helps identify changes in customer engagement over time.

A customer who registers in one month but makes no recorded event in a subsequent month is not counted as active for that month.

The demonstration uses calendar-month periods rather than fixed 30-day intervals.

## 11. Campaign Performance

Marketing campaign analysis examines the relationship between acquisition expenditure and observed customer activity.

The PostgreSQL implementation includes a campaign table with:

- Campaign identifier.
- Campaign name.
- Acquisition channel.
- Campaign expenditure.
- Start date.
- End date.

The campaign performance view measures:

- Touchpoints.
- Unique customers.
- Purchases.
- Revenue.
- Revenue-to-cost ratio.

The revenue-to-cost ratio is:

\[
RevenueToCostRatio=\frac{AttributedOrObservedRevenue}{CampaignCost}
\]

The demonstration's campaign reporting uses revenue directly recorded against campaign-linked purchase events.

It does not represent fully distributed multi-touch revenue.

A production financial analysis should distinguish gross revenue, net revenue, contribution margin, acquisition expenditure, refunds, and attribution methodology.

## 12. Technology Implementations

### 12.1 Python

File: `customer_journey_analytics.py`

Python provides the analytical simulation.

Important components:

| Component | Responsibility |
|---|---|
| `JourneyStore` | Customer and event storage |
| `EventValidator` | Event integrity validation |
| `SessionAnalyzer` | Session creation and duration |
| `FunnelAnalyzer` | Sequential conversion analysis |
| `AttributionModel` | Attribution calculations |
| `CohortAnalyzer` | Monthly retention |
| `BehaviorAnalyzer` | Behavioral metrics |
| `JourneyAnalytics` | Consolidated reporting |

The implementation uses dataclasses, enumerations, dictionaries, sets, counters, exceptions, and unit tests.

It also demonstrates JSON report export.

Execution:

`python customer_journey_analytics.py`

### 12.2 JavaScript

File: `customer_journey_analytics.js`

JavaScript emphasizes event-driven architecture.

Important components:

| Component | Responsibility |
|---|---|
| `JourneyCollector` | Event ingestion and notifications |
| `IdentityRegistry` | Cross-identifier resolution |
| `JourneyStateEngine` | Customer journey transitions |
| `SessionAnalyzer` | Session metrics |
| `FunnelAnalyzer` | Funnel conversion |
| `AttributionEngine` | Revenue credit distribution |
| `CustomerSegmenter` | Behavioral classification |
| `CohortAnalyzer` | Retention analysis |
| `AnalyticsReportService` | Business reporting |

The implementation uses:

- `Map` for keyed application state.
- `Set` for unique customer collections.
- `EventEmitter` for event notifications.
- Promises for asynchronous ingestion.
- `async/await` for report export.
- Node.js filesystem APIs for JSON output.

Execution:

`node customer_journey_analytics.js`

### 12.3 C++17

File: `customer_journey_analytics.cpp`

C++17 demonstrates domain modeling and efficient analytical processing.

Important components:

- `EventRepository`
- `IdentityRegistry`
- `SessionAnalyzer`
- `FunnelAnalyzer`
- `AttributionEngine`
- `BehaviorAnalyzer`
- `ChannelAnalyzer`
- `AnalyticsEngine`

The implementation uses STL containers, enumerations, structures, classes, algorithms, and exceptions.

The event repository uses hash-based containers for average constant-time identifier lookup.

Ordered maps provide deterministic reporting.

Compilation:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic customer_journey_analytics.cpp -o journey_analytics`

Execution:

`./journey_analytics`

### 12.4 Java 17

File: `CustomerJourneyAnalytics.java`

Java demonstrates an enterprise-oriented service architecture.

The implementation uses immutable records for customers, events, sessions, transitions, and analytical results.

Important services include:

- `EventValidationService`
- `IdentityService`
- `JourneyRepository`
- `JourneyStateService`
- `SessionAnalyticsService`
- `FunnelAnalyticsService`
- `AttributionService`
- `SegmentationService`
- `CohortAnalyticsService`
- `ReportingService`

Domain exceptions distinguish general analytical failures, validation failures, consent failures, and identity conflicts.

The repository uses synchronized methods for basic thread-safe access.

This is a demonstration architecture rather than a distributed transaction system.

Compilation:

`javac CustomerJourneyAnalytics.java`

Execution:

`java CustomerJourneyAnalytics`

### 12.5 PostgreSQL

File: `customer_journey_analytics.sql`

PostgreSQL implements persistent relational analytics.

The schema includes:

- Customers.
- Customer identities.
- Campaigns.
- Sessions.
- Touchpoints.
- Journey transitions.
- Attribution policies.

Database mechanisms include:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Enumerated data types.
- JSONB event properties.
- B-tree indexes.
- GIN indexes.
- Partial indexes.
- Triggers.
- Stored functions.
- Stored procedures.
- Analytical views.
- Common table expressions.
- Transactions.

The consent trigger rejects event insertion for customers without granted consent.

The session trigger updates the latest session activity timestamp.

The journey transition trigger automatically records the stage associated with an inserted event.

The reporting views support campaign analysis, customer segmentation, session analysis, funnel measurement, and cohort retention.

Execution:

`psql -U postgres -d postgres -f customer_journey_analytics.sql`

The script recreates the `customer_journey` schema. It should be executed against a dedicated development database rather than a database containing unrelated application data.

## 13. Database Architecture

The relational model follows these relationships:

- One customer can have multiple identities.
- One customer can have multiple sessions.
- One session can contain multiple touchpoints.
- One campaign can be associated with multiple touchpoints.
- One touchpoint can produce one journey transition.
- One customer can have multiple journey transitions.
- Attribution policies define the method used to distribute conversion credit.

### 13.1 Relationship diagram

Customer
→ Customer Identity

Customer
→ Sessions
→ Touchpoints
→ Journey Transitions

Campaign
→ Touchpoints

Touchpoints
→ Funnel Analytics

Touchpoints
→ Session Analytics

Touchpoints
→ Attribution Analysis

Customer
→ Cohort Retention

Touchpoints
→ Behavioral Segmentation

### 13.2 Data integrity

Foreign keys preserve relationships between customers, sessions, campaigns, and events.

Check constraints reject invalid monetary values.

Unique constraints prevent duplicate event references and identity assignments.

Indexes improve common access patterns, particularly:

- Customer event history.
- Session event ordering.
- Event-type filtering.
- Channel performance.
- Campaign reporting.
- Purchase retrieval.

The JSONB GIN index supports searches within structured event properties.

For large-scale event ingestion, index selection should be reviewed against actual query plans and write throughput.

## 14. Privacy and Data Governance

Customer journey analytics can involve personal data and persistent identifiers.

The demonstration includes a basic consent-aware ingestion model.

Events are accepted only when the customer has granted analytics consent.

The implementations also provide customer-erasure functionality.

The PostgreSQL model uses cascading foreign keys to remove associated identities, sessions, touchpoints, and journey transitions.

Important production controls include:

- Purpose-specific consent.
- Consent history and timestamps.
- Data minimization.
- Retention schedules.
- Access restrictions.
- Encryption in transit and at rest.
- Audit logging.
- Identifier pseudonymization.
- Secure export procedures.
- Appropriate deletion and backup-retention policies.

A simple consent flag is not a complete privacy-compliance system.

Production deployments must also account for applicable legal requirements, consent withdrawal, data-subject requests, downstream processors, backups, and derived analytical datasets.

## 15. Analytical Interpretation and Limitations

### 15.1 Observed behavior versus actual behavior

The system analyzes recorded events.

Missing tracking signals can cause an incomplete representation of customer activity.

For example, a customer may purchase through a channel that was not successfully recorded.

### 15.2 Attribution versus causality

Attribution allocates conversion credit according to a specified model.

It does not establish that a channel caused the conversion.

Causal evaluation requires additional experimental or statistical methods.

### 15.3 Identity resolution limitations

Incorrect identity matching can combine the behavior of different individuals.

The demonstration rejects conflicting identifiers but does not implement probabilistic identity matching.

### 15.4 Funnel limitations

The sequential funnel requires the defined events to appear in chronological order.

A production implementation should explicitly define:

- Conversion windows.
- Repeated-event handling.
- Cross-session funnel behavior.
- Missing-event treatment.
- Entry-stage rules.
- Time-zone conventions.

### 15.5 Retention limitations

The demonstration measures recorded monthly activity.

It does not distinguish different types of activity, such as passive visits and meaningful commercial engagement.

Retention definitions should match the business objective.

### 15.6 Scalability

The five implementations primarily demonstrate analytical logic over in-memory or relational data.

Large-scale production systems may require partitioned event storage, incremental aggregation, streaming ingestion, distributed identity resolution, and dedicated analytical warehouses.

## 16. Performance Considerations

| Operation | Main implementation approach | Typical complexity |
|---|---|---|
| Event lookup | Hash maps | Average O(1) |
| Duplicate detection | Hash sets/maps | Average O(1) |
| Event ordering | Sorting | O(n log n) |
| Sessionization | Sorting and linear scan | O(n log n) |
| Funnel analysis | Grouping and chronological scans | O(n log n) |
| Channel aggregation | Hash-based grouping | Average O(n) |
| Attribution | Event traversal | O(n) after ordering |
| Customer segmentation | Hash-based aggregation | Average O(n) |
| Cohort activity | Grouping and set intersection | Depends on cohort size |

Here, \(n\) represents the number of processed events unless otherwise specified.

The SQL implementation relies on composite indexes for customer and timestamp retrieval.

For very large datasets, monthly or daily partitioning by event timestamp can reduce the amount of data scanned.

Incremental materialized aggregates can also reduce the cost of repeated reporting.

## 17. Demonstration Dataset

The five implementations use a sample e-commerce dataset with four consented customers and one customer without analytics consent.

| Customer | Acquisition journey | Outcome |
|---|---|---|
| C001 | Social → Organic Search → Product → Cart → Checkout | Purchased |
| C002 | Paid Search → Product → Cart | Cart abandonment |
| C003 | Direct → Product → Checkout | Purchased |
| C004 | Display → Email → Product | No purchase |
| C005 | No analytics collection | Consent denied |

The four consented customer journeys contain 17 recorded events.

Two customers complete purchases.

Each completed purchase has a value of ₹1,499.

The expected recorded purchase revenue is ₹2,998.

This dataset provides examples of successful conversion, incomplete conversion, channel interaction, and consent-based collection restrictions.

## 18. Testing and Validation

The implementations include checks for important failure conditions.

| Test condition | Expected behavior |
|---|---|
| Duplicate event | Reject or ignore duplicate |
| Unknown customer | Reject event |
| Denied consent | Reject analytics ingestion |
| Invalid timestamp | Reject event |
| Negative revenue | Reject event |
| Zero-value purchase | Reject event |
| Invalid attribution total | Reject revenue allocation |
| Empty event collection | Return an empty analytical result |
| Unknown identity collision | Reject identity association |
| Customer erasure | Remove associated stored records |

The Python and JavaScript implementations include automated assertions.

The C++ and Java implementations include executable validation checks.

The PostgreSQL implementation uses relational constraints, triggers, and database functions to enforce data integrity.

## 19. Business Applications

Customer journey analytics supports several business activities:

| Business function | Analytical application |
|---|---|
| Marketing | Acquisition-channel performance |
| Sales | Purchase intent and conversion |
| Product management | Product engagement and abandonment |
| Customer experience | Journey friction identification |
| Customer support | Support-related behavior |
| Finance | Purchase revenue and campaign expenditure |
| Management | Customer retention and segment reporting |
| Digital operations | Session and behavioral monitoring |

The central analytical objective is to understand how customer interactions relate to business outcomes while maintaining accurate event records, transparent measurement rules, and appropriate privacy controls.
