# Campaign Analytics: ROI, ROAS and Campaign Performance

## 1. Project Overview

This project implements a campaign analytics system for measuring, comparing and evaluating digital marketing performance.

The system examines advertising expenditure, attributed revenue, conversions, customer acquisition costs, campaign profitability and budget utilization.

It covers six marketing channels:

- Paid Search
- Paid Social
- Email Marketing
- Display Advertising
- Affiliate Marketing
- Video Advertising

The implementations use five complementary approaches:

| File | Engineering perspective |
|---|---|
| Python | Campaign simulation, analytical calculations and reporting |
| JavaScript | Event-driven monitoring, campaign state and budget policies |
| C++17 | Efficient performance computation, aggregation and optimization |
| Java 17 | Enterprise domain modeling, immutable records and governance |
| PostgreSQL | Relational campaign data management, attribution and reporting |

The implementations use consistent campaign scenarios and financial definitions while demonstrating different approaches to data processing and application architecture.

## 2. Marketing Performance Fundamentals

### 2.1 Campaign

A campaign is a coordinated marketing activity designed to achieve a measurable objective.

A campaign contains:

- Campaign identifier
- Campaign name
- Marketing channel
- Allocated budget
- Actual advertising expenditure
- Impressions
- Clicks
- Conversions
- Attributed revenue
- Campaign status

Campaign status is represented by three states:

| State | Meaning |
|---|---|
| ACTIVE | Campaign is currently operating |
| PAUSED | Campaign expenditure and delivery are temporarily suspended |
| COMPLETED | Campaign has reached its operational end state |

Campaign status and financial performance are separate concepts. A paused campaign can retain historical expenditure and revenue, while a profitable campaign can still exceed its budget.

### 2.2 Marketing Funnel

The marketing funnel represents the progression from advertising exposure to measurable customer action.

`Impressions → Clicks → Conversions → Revenue`

| Metric | Meaning |
|---|---|
| Impressions | Number of times advertisements were displayed |
| Clicks | Number of recorded advertisement clicks |
| Conversions | Number of completed conversion events |
| Revenue | Monetary value attributed to marketing activity |

The implementations enforce basic funnel consistency:

- Clicks cannot exceed impressions.
- Conversions cannot exceed clicks.
- Financial values cannot be negative.
- A campaign must have a valid identifier and positive planned budget.

These constraints detect invalid reporting data before performance calculations are performed.

## 3. Financial Performance Metrics

### 3.1 Return on Investment (ROI)

ROI measures the net financial return relative to the investment.

\[
ROI = \frac{Revenue - Investment}{Investment}\times100
\]

Where:

- Revenue represents attributed marketing revenue.
- Investment represents advertising expenditure.
- Profit represents revenue minus expenditure.

Example:

| Component | Amount |
|---|---:|
| Advertising expenditure | ₹50,000 |
| Attributed revenue | ₹150,000 |
| Profit | ₹100,000 |
| ROI | 200% |

A positive ROI indicates that attributed revenue exceeds advertising expenditure under the implemented direct-advertising-cost definition.

A negative ROI indicates that expenditure exceeds attributed revenue.

A zero ROI indicates that revenue equals expenditure.

**Important accounting distinction:** Advertising-only ROI is not necessarily the same as business-level ROI. A comprehensive business calculation may include product costs, employee expenses, agency fees, platform charges, discounts, taxes and other operating costs.

### 3.2 Return on Ad Spend (ROAS)

ROAS measures the revenue generated for each monetary unit spent on advertising.

\[
ROAS = \frac{Attributed\ Revenue}{Advertising\ Spend}
\]

Example:

| Component | Value |
|---|---:|
| Advertising expenditure | ₹20,000 |
| Attributed revenue | ₹80,000 |
| ROAS | 4.0 |

A ROAS of 4 means that every ₹1 of advertising expenditure generated ₹4 in attributed revenue.

ROAS is expressed as a ratio, not a percentage.

### 3.3 ROI and ROAS Distinction

| Characteristic | ROI | ROAS |
|---|---|---|
| Measurement | Net return | Attributed revenue |
| Formula | (Revenue - Spend) / Spend | Revenue / Spend |
| Typical presentation | Percentage | Ratio |
| Includes deduction of advertising spend | Yes | No |
| Primary purpose | Profitability evaluation | Advertising efficiency |

Their mathematical relationship is:

\[
ROI\% = (ROAS-1)\times100
\]

This relationship holds when both metrics use exactly the same revenue and advertising-spend definitions.

A ROAS of 1 corresponds to a 0% advertising-only ROI.

A ROAS below 1 indicates negative advertising-only ROI.

A ROAS above 1 indicates positive advertising-only ROI.

Neither metric independently establishes overall business profitability.

### 3.4 Click-Through Rate (CTR)

CTR measures the percentage of impressions that produce clicks.

\[
CTR = \frac{Clicks}{Impressions}\times100
\]

A high CTR can indicate effective advertisement relevance and audience targeting.

CTR does not establish whether the resulting traffic generates profitable conversions.

### 3.5 Conversion Rate

Conversion rate measures the percentage of clicks that result in conversions.

\[
Conversion\ Rate =
\frac{Conversions}{Clicks}\times100
\]

It helps evaluate landing pages, customer experience and traffic quality.

### 3.6 Cost Per Click (CPC)

\[
CPC = \frac{Advertising\ Spend}{Clicks}
\]

CPC measures the average advertising cost associated with a recorded click.

### 3.7 Cost Per Acquisition (CPA)

\[
CPA = \frac{Advertising\ Spend}{Conversions}
\]

CPA measures the average cost of acquiring a conversion.

CPA should not automatically be interpreted as customer acquisition cost. A conversion might represent a lead, registration, download or transaction rather than a newly acquired customer.

### 3.8 Cost Per Thousand Impressions (CPM)

\[
CPM = \frac{Advertising\ Spend}{Impressions}\times1000
\]

CPM is useful for evaluating advertising delivery and awareness-oriented campaigns.

### 3.9 Budget Utilization

\[
Budget\ Utilization =
\frac{Actual\ Spend}{Allocated\ Budget}\times100
\]

A utilization value above 100% indicates that expenditure exceeds the planned budget.

## 4. Campaign Performance Evaluation

The project classifies campaigns using configurable performance thresholds.

| Classification | Implemented rule |
|---|---|
| EXCELLENT | ROI above 100% and ROAS at least 3 |
| PROFITABLE | Positive ROI and ROAS above 1 |
| BREAK EVEN | ROI equals zero |
| LOSS MAKING | Negative ROI |
| NO INVESTMENT | Advertising expenditure equals zero |

These categories are operational classifications rather than universal marketing benchmarks.

Industry, campaign objective, attribution methodology, contribution margin and customer lifetime value should influence real-world thresholds.

A campaign designed for brand awareness may have a different evaluation framework from a direct-response conversion campaign.

## 5. Portfolio-Level Analysis

Campaign-level results provide individual performance information.

Portfolio analysis combines multiple campaigns to evaluate the complete advertising investment.

### Aggregate portfolio ROI

\[
Portfolio\ ROI =
\frac{\sum Revenue-\sum Spend}{\sum Spend}\times100
\]

### Aggregate portfolio ROAS

\[
Portfolio\ ROAS =
\frac{\sum Revenue}{\sum Spend}
\]

An important implementation decision is to calculate portfolio ratios from aggregate financial totals rather than averaging individual campaign ratios.

For example, consider two campaigns:

| Campaign | Spend | Revenue | ROAS |
|---|---:|---:|---:|
| A | ₹10,000 | ₹40,000 | 4.0 |
| B | ₹90,000 | ₹90,000 | 1.0 |

The arithmetic average ROAS is 2.5.

The actual portfolio ROAS is:

\[
\frac{130000}{100000}=1.3
\]

The aggregate calculation correctly accounts for differences in campaign expenditure.

### Channel-level evaluation

Channel analysis groups campaigns by marketing channel.

It identifies:

- Total channel expenditure
- Total attributed revenue
- Channel-level profit
- Channel-level ROI
- Channel-level ROAS
- Number of campaigns

This allows marketing managers to compare Search, Social, Email, Display, Affiliate and Video performance without confusing individual campaign outcomes with channel-level outcomes.

## 6. Conversion Attribution

Attribution assigns conversion revenue to marketing interactions.

A customer may interact with multiple campaigns before completing a purchase.

For example:

`Search Advertisement → Social Advertisement → Email → Purchase`

The system implements three attribution models.

### 6.1 First-Touch Attribution

The first recorded marketing interaction receives the conversion credit.

This model emphasizes initial customer acquisition and discovery.

### 6.2 Last-Touch Attribution

The final recorded marketing interaction receives the conversion credit.

This model emphasizes the final interaction before conversion.

### 6.3 Linear Attribution

Conversion revenue is divided equally across recorded touchpoints.

For a conversion worth ₹12,000 involving three interactions:

| Interaction | Assigned revenue |
|---|---:|
| Search | ₹4,000 |
| Social | ₹4,000 |
| Email | ₹4,000 |

### Attribution limitations

Attribution is an analytical allocation mechanism, not proof of causality.

The implemented models do not independently measure:

- Incremental conversions
- Organic demand
- Customer behavior without advertising
- Cross-device identity
- Advertising exposure without recorded clicks
- Delayed conversion effects

The attribution results depend on the quality and completeness of recorded interaction data.

## 7. Campaign Budget Optimization

The budget optimization components identify active campaigns that satisfy configurable performance conditions.

The implemented eligibility rules include:

- Campaign must be active.
- ROAS must meet the minimum threshold.
- Budget utilization must remain below the configured maximum.
- Existing advertising expenditure must be positive.

Eligible campaigns receive additional budget proportionally to their existing advertising expenditure.

\[
Allocation_i =
Available\ Budget
\times
\frac{Campaign\ Spend_i}{Total\ Eligible\ Spend}
\]

The available budget is calculated after retaining the configured reserve.

For example, a ₹100,000 additional budget with a 10% reserve produces ₹90,000 available for allocation.

This is a transparent baseline allocation method, not a complete optimization model.

It does not establish that historical expenditure is the best predictor of marginal future returns.

A production optimization system should also consider:

- Marginal ROAS
- Conversion volume
- Campaign capacity
- Diminishing returns
- Audience saturation
- Forecast uncertainty
- Customer lifetime value
- Channel-specific constraints
- Minimum and maximum allocations

## 8. Python Implementation

The Python implementation provides a complete campaign simulation and reporting workflow.

### Main components

| Component | Responsibility |
|---|---|
| `Campaign` | Stores and validates campaign information |
| `CampaignMetrics` | Represents calculated performance |
| `CampaignAnalytics` | Calculates financial and funnel metrics |
| `CampaignManager` | Maintains campaign records and updates |
| `PerformanceAnalyzer` | Produces portfolio and channel reports |
| `BudgetOptimizer` | Calculates budget allocation recommendations |

### Important mechanisms

**Dataclasses and enums**

Campaigns use structured records and enumerated channel and status values.

This improves consistency and reduces errors caused by unstructured dictionaries.

**Validation**

Campaign initialization checks financial values and conversion-funnel constraints.

**State management**

The manager maintains campaign records using a dictionary indexed by campaign ID.

This provides average constant-time campaign retrieval.

**Outlier detection**

The implementation uses median absolute deviation (MAD) to identify unusually different campaign ROI values.

The method is more resistant to extreme values than standard-deviation-based detection.

**Reporting**

The program exports JSON and CSV files for downstream reporting and analysis.

**Testing**

Assertions verify ROI, ROAS, CAC calculations and invalid campaign rejection.

### Execution

Run `python campaign_analytics.py`.

Optional output arguments:

- `--output campaign_report.json`
- `--csv campaign_metrics.csv`

The script uses Python standard-library modules.

## 9. JavaScript Implementation

The JavaScript implementation adopts an event-driven application architecture.

### Main components

| Component | Responsibility |
|---|---|
| `Campaign` | Campaign validation and snapshots |
| `MetricCalculator` | Campaign metric computation |
| `CampaignStore` | In-memory state and event management |
| `PerformanceService` | Portfolio and channel analytics |
| `BudgetPolicy` | Campaign eligibility and allocation |
| `CampaignMonitor` | Event-driven performance monitoring |
| `AttributionService` | Last-touch revenue attribution |

### Event-driven architecture

The campaign store extends Node.js `EventEmitter`.

It emits events when:

- A campaign is created.
- Campaign information changes.
- Performance activity is recorded.
- A campaign is deleted.

The monitoring component responds to activity events and identifies budget overruns and campaigns with ROAS below one.

### Atomic update behavior

The store constructs and validates a replacement campaign before committing the new state.

If validation fails, the original campaign remains unchanged.

This avoids partially applied updates within the in-memory model.

### Asynchronous reporting

The report exporter uses Node.js asynchronous file operations.

It writes structured JSON reports without introducing third-party packages.

### Execution

Run `node campaign_analytics.js`.

The program generates `campaign_analytics_report.json`.

The implementation requires Node.js 18 or later.

## 10. C++17 Implementation

The C++ implementation focuses on computational efficiency, structured data processing and performance aggregation.

### Main components

| Component | Responsibility |
|---|---|
| `Campaign` | Campaign domain structure |
| `MetricEngine` | Financial and operational calculations |
| `CampaignRegistry` | Campaign storage and retrieval |
| `PortfolioAnalyzer` | Portfolio and channel aggregation |
| `BudgetOptimizer` | Performance-based allocation |
| `Metrics` | Calculated campaign results |

### Engineering decisions

**STL map**

The campaign registry uses `std::map` to provide deterministic key ordering and logarithmic lookup.

**Vectors**

Calculated metrics are stored in vectors to support sorting and efficient sequential aggregation.

**Enumerations**

Channel, campaign status and performance categories are represented by strongly typed enums.

**Standard algorithms**

`std::sort` ranks campaigns by profit, ROI and ROAS.

`std::accumulate` calculates the total recommended allocation.

**Validation**

Financial values are checked for finiteness and valid ranges. Funnel constraints are checked before calculations.

### Complexity

Let N represent the number of campaigns.

| Operation | Complexity |
|---|---|
| Campaign insertion | O(log N) |
| Campaign retrieval | O(log N) |
| Complete metric evaluation | O(N log N) |
| Portfolio aggregation | O(N) |
| Channel aggregation | O(N log K) |
| Campaign ranking | O(N log N) |
| Budget allocation | O(N) |

K represents the number of distinct marketing channels.

The implementation uses only the C++17 standard library.

### Compilation

Compile using:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic campaign_analytics.cpp -o campaign_analytics`

Run the executable using:

`./campaign_analytics`

On Windows:

`campaign_analytics.exe`

## 11. Java 17 Enterprise Implementation

The Java implementation models campaign analytics using immutable records, service classes and explicit business policies.

### Domain model

The implementation separates:

- Campaign information
- Campaign activity
- Calculated metrics
- Attribution interactions
- Portfolio reports
- Channel reports
- Budget rules

Java records provide immutable data structures for these entities.

### Repository layer

`CampaignRepository` manages campaign persistence in an in-memory map.

It provides:

- Campaign insertion
- Campaign retrieval
- Complete campaign listing
- Activity updates
- Campaign status transitions

The synchronized repository methods provide basic thread-safe access to the in-memory state.

### Service layer

`MetricService` calculates campaign performance.

`PortfolioService` produces campaign rankings, portfolio reports and channel aggregations.

`BudgetGovernanceService` applies eligibility rules before allocating additional budget.

`AttributionService` evaluates first-touch, last-touch and linear attribution.

### Business validation

The implementation rejects:

- Empty campaign identifiers
- Invalid financial values
- Negative funnel values
- Click counts exceeding impressions
- Conversion counts exceeding clicks
- Invalid attribution records
- Activity updates to completed campaigns

### Immutability and state transitions

Campaign records are immutable.

An activity update creates a replacement record and validates the complete replacement before changing the repository state.

This reduces accidental modification of shared campaign objects.

### Compilation

Compile using:

`javac --release 17 CampaignAnalytics.java`

Run using:

`java CampaignAnalytics`

No external dependencies are required.

## 12. PostgreSQL Database Architecture

The PostgreSQL implementation models campaign analytics as a relational information system.

### Entity relationships

`Organizations`

→ `Marketing Users`

→ `Marketing Channels`

→ `Campaigns`

→ `Campaign Daily Metrics`

→ `Conversions`

→ `Attribution Touchpoints`

→ `Campaign Budget Adjustments`

→ `Organization Budget Policies`

### Core tables

| Table | Purpose |
|---|---|
| `organizations` | Organization and reporting currency |
| `marketing_users` | User identities and organizational roles |
| `marketing_channels` | Marketing channel definitions |
| `campaigns` | Campaign master records |
| `campaign_daily_metrics` | Daily performance measurements |
| `conversions` | Recorded conversion events |
| `attribution_touchpoints` | Campaign interactions associated with conversions |
| `campaign_budget_adjustments` | Approved budget revisions |
| `organization_budget_policies` | Performance and allocation rules |

### Data integrity

The schema implements:

- Primary keys
- Foreign keys
- Unique constraints
- Check constraints
- Enumerated types
- Transaction boundaries
- Referential integrity

The unique external conversion-event identifier prevents duplicate conversion ingestion.

The unique campaign/date constraint prevents duplicate daily snapshots for a campaign.

### Daily metric ingestion

The SQL implementation uses `INSERT ... ON CONFLICT DO UPDATE`.

This allows an existing campaign/date snapshot to be replaced when the same reporting period is imported again.

The operation is idempotent when the source provides complete replacement snapshots.

It should not be used indiscriminately for incremental event records, where repeated ingestion could require separate event identifiers and deduplication logic.

### Performance views

The database provides:

- `campaign_performance`
- `campaign_performance_classified`
- `portfolio_performance`
- `channel_performance`
- `eligible_campaigns`

These views centralize calculation logic and reduce repeated aggregation queries.

### Attribution function

`calculate_attribution()` supports three attribution models:

- First touch
- Last touch
- Linear

Only confirmed conversions are included.

### Budget allocation function

`recommend_budget_allocation()` identifies eligible campaigns and calculates proportional budget recommendations.

### Indexing

Indexes support:

- Organization and campaign-status filtering
- Campaign-date retrieval
- Channel-based filtering
- Conversion-event retrieval
- Attribution-touchpoint lookup

### Transaction management

Daily metric ingestion and approved budget revisions use explicit transactions.

Budget adjustments retain the previous and revised values, approving user and reason.

## 13. Realistic Campaign Performance Scenario

The sample dataset contains five active campaigns and one paused campaign.

| Campaign | Channel | Spend | Revenue |
|---|---|---:|---:|
| Search Conversion | Search | ₹35,000 | ₹140,000 |
| Social Awareness | Social | ₹30,000 | ₹45,000 |
| Email Retention | Email | ₹12,000 | ₹96,000 |
| Display Remarketing | Display | ₹25,000 | ₹18,000 |
| Affiliate Acquisition | Affiliate | ₹15,000 | ₹75,000 |
| Video Awareness | Video | ₹0 | ₹0 |

The combined portfolio figures are:

| Metric | Result |
|---|---:|
| Campaign count | 6 |
| Total advertising expenditure | ₹117,000 |
| Total attributed revenue | ₹374,000 |
| Total advertising profit | ₹257,000 |
| Portfolio ROI | 219.66% |
| Portfolio ROAS | 3.1966 |

These results illustrate why individual campaign performance and aggregate portfolio performance should both be examined.

The Email campaign generates a high ROAS despite having a smaller budget than the Search campaign.

The Display campaign generates less attributed revenue than advertising expenditure and therefore has negative advertising-only ROI.

The paused Video campaign has no recorded expenditure and is classified as having no investment rather than being treated as a profitable or loss-making campaign.

## 14. Data Quality and Failure Handling

Campaign analytics depends on accurate and consistent source data.

Important failure conditions include:

| Failure | Control |
|---|---|
| Duplicate campaign identifier | Unique identifiers and duplicate checks |
| Negative expenditure | Financial validation |
| Clicks greater than impressions | Funnel validation |
| Conversions greater than clicks | Funnel validation |
| Duplicate conversion events | Unique external event identifier |
| Missing attribution interactions | Attribution validation queries |
| Campaign budget exceeded | Budget-utilization monitoring |
| Zero advertising expenditure | Safe division |
| Invalid campaign updates | Validate before committing |
| Repeated daily snapshot ingestion | Unique campaign/date constraint |

A zero denominator returns zero for the affected metric in these implementations.

This is a computational convention, not an assertion that the metric has a meaningful observed value. Production reports should distinguish zero, missing and not-applicable observations.

## 15. Security and Production Considerations

The examples use local in-memory repositories and a relational database schema to demonstrate the analytical workflow.

A production deployment requires additional controls.

### Data protection

- Restrict access to customer references.
- Avoid storing unnecessary personally identifiable information.
- Apply database privileges according to organizational roles.
- Protect database credentials.
- Encrypt sensitive data in transit and at rest.
- Retain audit records for financial changes.

### Data ingestion

- Validate source identifiers.
- Deduplicate incoming events.
- Track ingestion timestamps.
- Use consistent reporting currencies.
- Define time zones and reporting periods.
- Distinguish event-time data from ingestion-time data.
- Reconcile advertising-platform expenditure against billing records.

### Financial consistency

Campaign ROAS should use clearly defined attributed revenue.

Revenue should not be counted multiple times across campaigns when calculating a portfolio.

Refunds, cancellations, discounts, taxes and product costs should be accounted for according to the organization's reporting policy.

### Analytical governance

Campaign comparisons should specify:

- Attribution model
- Conversion definition
- Reporting period
- Currency
- Revenue recognition rules
- Advertising-cost definition
- Data freshness
- Treatment of missing observations

These definitions are necessary for meaningful comparisons between campaigns and marketing channels.

## 16. Important Analytical Limitations

The implementations provide deterministic calculations based on supplied campaign data.

They do not implement a complete advertising experimentation or forecasting platform.

The following distinctions remain important:

**Attributed revenue versus incremental revenue**

Attributed revenue is assigned to marketing interactions under a defined attribution model. Incremental revenue estimates the additional revenue caused by marketing activity compared with an appropriate counterfactual.

**Conversion versus customer acquisition**

A conversion event does not necessarily represent a new customer. Customer acquisition cost requires a reliable count of newly acquired customers.

**ROAS versus contribution margin**

A campaign can have positive ROAS while remaining unprofitable after product costs and other variable expenses.

**Historical performance versus future performance**

Historical ROAS does not guarantee equivalent returns from additional expenditure. Marginal returns may decline as audiences become saturated.

**Campaign performance versus marketing effectiveness**

A campaign can produce strong short-term conversion metrics without generating long-term customer retention or profitable customer lifetime value.

These distinctions should guide interpretation of the calculated metrics and budget recommendations.
