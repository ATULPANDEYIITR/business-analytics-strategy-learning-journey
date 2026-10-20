# Pareto Analysis: 80/20 Analysis for Business Prioritization

## Purpose

Pareto analysis is a business decision-making technique that ranks items by their contribution to a measurable outcome and calculates their cumulative contribution. It helps managers identify the relatively small number of items that account for a substantial share of business value, cost, defects, workload, or risk.

The 80/20 principle is a useful heuristic, not a mathematical guarantee. A dataset may show that 20% of items contribute 80% of the outcome, but the actual distribution must be measured.

This project implements Pareto analysis in Python, JavaScript, C++17, Java 17, and PostgreSQL. Each implementation examines the same business prioritization problem through a different technical perspective.

## Business Scenario

A company wants to prioritize customers, operational workloads, technology investments, and internal initiatives according to their measured business value.

The sample dataset contains ten items:

| Business item | Category | Measured value |
|---|---|---:|
| Enterprise accounts | Customers | 420,000 |
| SMB accounts | Customers | 160,000 |
| Support tickets | Operations | 90,000 |
| Cloud infrastructure | Technology | 75,000 |
| Marketing campaigns | Marketing | 60,000 |
| Training programs | People | 40,000 |
| Internal tooling | Technology | 25,000 |
| Legacy reporting | Operations | 15,000 |
| Office services | Operations | 10,000 |
| Other requests | Operations | 5,000 |
| **Total** | | **900,000** |

The measured value is a business-specific quantity. Before applying the method, an organization must define whether it represents revenue, cost, incident volume, expected risk, customer lifetime value, or another consistent measure.

## Core Mathematical Concepts

### Contribution percentage

For an item with value \(v_i\), its share of the total is:

\[
p_i = \frac{v_i}{\sum_{j=1}^{n}v_j}
\]

Multiplying by 100 expresses the share as a percentage.

### Cumulative contribution

Items are sorted in descending order of measured value. The cumulative contribution after the \(k\)-th item is:

\[
C_k = \sum_{i=1}^{k} p_i
\]

This calculation identifies how much of the total value is represented by the highest-ranked items.

### Selecting the vital few

For a target contribution \(t\), select items in descending order until the cumulative contribution reaches or exceeds the target.

\[
k = \min\left\{m : C_m \geq t\right\}
\]

For an 80% target, the selected set contains the fewest highest-ranked items required to reach at least 80% of the measured value.

The item that crosses the threshold is included. Otherwise, the selected items might account for less than the required contribution.

### Pareto principle versus the 80/20 ratio

These concepts are related but distinct:

- **Pareto analysis** is the ranking and cumulative-contribution method.
- **The 80/20 principle** is the heuristic that a minority of causes may account for a majority of effects.
- **The threshold** is a configurable business decision, such as 70%, 80%, or 90%.
- **The vital few** are the items selected to reach the chosen threshold.
- **The remainder** consists of lower-ranked items outside that selected set.

The actual number of selected items depends on the distribution of values, not a fixed requirement that exactly 20% of records must be selected.

## Analytical Workflow

The implementations follow this workflow:

Validate input data  
→ Calculate total measured value  
→ Sort items by descending contribution  
→ Calculate individual shares  
→ Calculate cumulative shares  
→ Identify threshold-crossing items  
→ Aggregate category contributions  
→ Report results and validate edge cases

Each stage has a distinct responsibility. Validation prevents meaningless results, ranking establishes the priority order, cumulative calculations quantify concentration, and reporting supports business decisions.

## Python Implementation

The Python script models business records using an immutable `BusinessItem` dataclass and returns structured `ParetoResult` records.

### Implemented mechanisms

- Dataclasses provide explicit types for business inputs and analysis results.
- Validation rejects empty names, empty categories, duplicate item names, negative values, non-finite values, and datasets whose total value is zero.
- Sorting ranks the highest-value items first.
- Cumulative contribution calculations identify the threshold-crossing item.
- Category aggregation groups values independently of item-level ranking.
- Concentration metrics calculate the contribution of the top 20% of records, mean value, median value, maximum, and minimum.
- CSV loading validates the required columns and reports invalid rows.
- CSV and JSON exports preserve ranks, values, percentages, cumulative shares, and priority classifications.
- Self-tests check ranking, total contribution, and zero-total rejection.

### Priority classification

The implementation distinguishes three classifications:

| Classification | Meaning |
|---|---|
| `CORE` | Item occurs before the target has been reached. |
| `THRESHOLD` | Item crosses the target contribution. |
| `REMAINDER` | Item occurs after the target has been reached. |

The classifications describe the item's position in the cumulative analysis. They do not independently establish business urgency or operational importance.

### Execution

Save the file as `pareto_analysis.py` and run:

`python pareto_analysis.py`

The script prints the analysis and creates a `pareto_output` directory containing JSON and CSV reports.

## JavaScript Implementation

The JavaScript implementation uses an event-driven analysis pipeline suited to Node.js applications that process business data asynchronously.

### Implemented mechanisms

- The `BusinessItem` class validates the business records.
- `validateItems()` checks record types, duplicate names, and the total measured value.
- `calculatePareto()` returns ranked records with shares and cumulative contributions.
- `selectVitalFew()` selects the items required to reach the target.
- `aggregateCategories()` groups values using a `Map`.
- `evaluateDecision()` compares the selected set with an available management capacity.
- `analyzeWithEvents()` schedules analysis through `queueMicrotask()` and returns a Promise.
- `renderReport()` displays ranked and category-level reports.
- Self-tests verify ranking, contribution totals, category aggregation, and rejection of zero-total datasets.

The capacity evaluation distinguishes value concentration from resource availability. A set of high-value items may exceed the number of initiatives that a team can manage simultaneously.

The asynchronous wrapper provides an integration point for event-driven applications. It does not itself perform network requests, parallel processing, or database operations.

### Execution

Save the file as `pareto_analysis.js` and run:

`node pareto_analysis.js`

The script uses built-in Node.js capabilities and does not require npm packages.

## C++17 Implementation

The C++ program implements a reusable `ParetoEngine` that separates business analysis from report presentation.

### Implemented mechanisms

- `BusinessItem` represents the input domain.
- `ReviewRecord` stores ranked results.
- `GovernancePolicy` configures the contribution target and optional maximum number of priority items.
- `ParetoEngine::analyze()` validates the dataset, sorts records deterministically, and calculates contribution shares.
- `select_priority_items()` applies both the target contribution and the optional item-capacity limit.
- `category_totals()` aggregates measured values by category.
- `captured_share()` calculates the contribution represented by a selected set.
- Exception handling prevents invalid input from producing a misleading report.
- Self-tests verify ranking, contribution totals, and zero-total rejection.

The implementation uses standard containers and algorithms, including `std::vector`, `std::map`, `std::unordered_set`, `std::sort`, and `std::accumulate`.

A maximum priority-item limit introduces a deliberate trade-off. If the limit is reached before the target contribution, the selected set may fail to reach the desired target. The report must therefore be interpreted alongside the selected capacity.

### Execution

Save the file as `pareto_analysis.cpp`.

Compile with a C++17-compatible compiler:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic pareto_analysis.cpp -o pareto_analysis`

Run the executable:

`./pareto_analysis`

On Windows, run `pareto_analysis.exe`.

## Java 17 Implementation

The Java implementation models prioritization as an enterprise service with explicit domain types and a configurable policy.

### Implemented mechanisms

- `BusinessItem` is a validated record representing a business measure.
- `ParetoRecord` represents an immutable ranked result.
- `Priority` defines the classification states.
- `PrioritizationPolicy` validates the target share and maximum focused-item count.
- `ParetoService` separates analysis, selection, and category aggregation.
- `List.copyOf()` protects returned result collections from modification through the returned reference.
- Stream operations calculate totals and sort category reports.
- Exception handling distinguishes invalid inputs from successful analysis.
- Self-tests check ranking, contribution totals, and zero-total rejection.

The enterprise-oriented design makes the analysis policy explicit rather than embedding the threshold throughout the reporting logic.

The target share and maximum item count serve different purposes. The target expresses the desired contribution, while the capacity limit represents a resource constraint. When both are configured, the capacity limit may prevent the target from being reached.

### Execution

Save the file as `ParetoBusinessPrioritization.java`.

Compile:

`javac ParetoBusinessPrioritization.java`

Run:

`java ParetoBusinessPrioritization`

Java 17 or later is required because the implementation uses records and other modern Java language features.

## PostgreSQL Implementation

The SQL script represents the analysis as a relational workflow. It stores source records, policies, analysis runs, ranked results, and audit events separately.

### Relational model

| Table | Responsibility |
|---|---|
| `business_category` | Defines business categories. |
| `business_item` | Stores measured values and active status. |
| `pareto_policy` | Stores target contribution and capacity settings. |
| `pareto_run` | Records an executed analysis and its total value. |
| `pareto_result` | Stores rank, individual share, cumulative share, and classification. |
| `analysis_event` | Records analysis completion metadata. |

Primary keys identify records, foreign keys maintain relationships, and check constraints reject invalid values. Uniqueness constraints prevent duplicate category names and duplicate item names within a category.

A partial index on active item values supports queries that retrieve active business items in descending value order.

### Database-level analysis

The `run_pareto_analysis()` function:

- Verifies that the requested policy exists and is active.
- Calculates the total value of active business items.
- Rejects a dataset whose total value is zero.
- Creates a run record.
- Uses window functions to calculate ranked and cumulative contributions.
- Classifies the records relative to the configured threshold.
- Stores the results and an analysis-completion event.
- Returns the generated run identifier.

The `pareto_analysis_report` view joins ranked results to business item and category information. The `category_contribution` view provides an independent category-level analysis.

The script also includes a validation trigger for business-item names and values. Table constraints remain important because they protect data integrity independently of application-level validation.

### Transactions and integrity

The sample analysis is executed inside a transaction. The negative-value test uses a nested exception block so that an expected validation failure does not leave the test insertion in place.

PostgreSQL's `NUMERIC` type is used for measured business values to avoid relying on binary floating-point arithmetic for monetary quantities. The share columns use a defined decimal precision, so reports can exhibit small rounding differences.

The sample script drops and recreates its dedicated schema. Run it only in a development database where replacing that schema is acceptable.

### Execution

Save the file as `pareto_analysis.sql` and execute it using `psql` against a PostgreSQL database:

`psql -d your_database -f pareto_analysis.sql`

Replace `your_database` with the name of an existing database. The script does not create the database itself.

## Interpreting the Results

The sample data totals 900,000 units of measured business value.

The two largest items contribute:

- Enterprise accounts: approximately 46.67%.
- SMB accounts: approximately 17.78%.
- Combined contribution: approximately 64.44%.

The third-largest item contributes another 10%, taking the cumulative contribution to approximately 74.44%. Adding cloud infrastructure raises the cumulative contribution to approximately 82.78%.

Therefore, under the 80% threshold, the vital-few set contains four items. These four items represent 40% of the records but approximately 82.78% of the measured value.

This is an example of Pareto-style concentration, not proof that every business dataset follows an exact 80/20 distribution.

## Item-Level and Category-Level Analysis

Item-level and category-level analyses answer different questions.

**Item-level analysis** identifies individual customers, activities, initiatives, or cost drivers that contribute the most value.

**Category-level analysis** aggregates related items and shows which business functions or operational areas account for the largest combined contribution.

For example, two technology initiatives may have relatively low individual ranks but together represent a significant portion of the technology category's value. Aggregation can reveal this concentration even when no single item dominates.

Category shares should be calculated using the same active-record population and measurement definition as the item-level analysis. Comparing results from different populations can produce misleading conclusions.

## Practical Business Applications

### Revenue concentration

Rank customers by revenue to identify accounts that account for a substantial share of total sales. Use the results to guide account-management effort while monitoring the risk of excessive dependence on a few customers.

### Operational workload

Rank incident types, support requests, or recurring process failures by volume or total handling cost. High-contribution categories can become candidates for root-cause investigation and process redesign.

### Technology investment

Rank proposed initiatives by a consistent measure such as expected annual benefit, risk reduction, or validated cost savings. The resulting priorities must also consider feasibility, implementation cost, dependencies, and strategic constraints.

### Quality management

Rank defect types by frequency, financial impact, or severity-weighted impact. A frequency-based Pareto chart may produce a different ranking from one based on total financial loss.

### Risk management

Rank risks using a documented and consistently applied measure. A low-frequency but catastrophic risk may require immediate treatment even if it falls outside the vital-few set.

## Validation and Edge Cases

Reliable Pareto analysis depends on input quality and clear measurement definitions.

- **Empty datasets:** No ranking can be calculated without records.
- **Zero total value:** Contribution percentages are undefined when all measured values are zero.
- **Negative values:** The implementations reject them because negative contributions can invalidate ordinary cumulative-share interpretation. Net financial datasets with credits or losses require a separately defined analytical method.
- **Non-finite values:** NaN and infinity are rejected in the in-memory implementations.
- **Duplicate records:** Duplicate item names are rejected by the Python and JavaScript implementations, while the C++ implementation rejects exact duplicate names. The Java implementation rejects names that match after lowercasing. The SQL model permits the same item name in different categories.
- **Ties:** Equal values are ordered deterministically where explicit tie-breakers are implemented. A tie may affect rank position without changing the total contribution.
- **Rounding:** Calculations use full available precision internally, while displayed percentages are rounded for readability.
- **Changing data:** A saved analysis reflects the dataset at the time it was run. Recalculate after source values or active status changes.
- **Capacity limits:** A limit on the number of selected items can prevent the chosen set from reaching the target contribution.
- **Measurement bias:** Inconsistent time periods, missing records, duplicated transactions, and incompatible value definitions can distort the ranking.

## Complexity and Performance

For \(n\) business items, sorting dominates the in-memory implementations.

| Operation | Typical complexity |
|---|---|
| Input validation | \(O(n)\) |
| Sorting by value | \(O(n \log n)\) |
| Calculating shares and cumulative values | \(O(n)\) |
| Selecting the vital few | \(O(n)\) in the worst case |
| Category aggregation | \(O(n)\) expected with hash-based maps, or \(O(n \log c)\) with ordered maps, where \(c\) is the number of categories |

The PostgreSQL implementation uses window functions and sorting to calculate rankings and cumulative contributions. Index usefulness depends on the actual query plan, table size, data distribution, and active-record filter.

For large datasets, aggregate raw transactions into a consistent analytical dataset before performing Pareto analysis. Preserve source lineage and the measurement period so that reported priorities remain reproducible.

## Limitations and Decision Governance

Pareto analysis measures concentration. It does not determine causality, guarantee a particular outcome, or replace managerial judgment.

A high contribution does not automatically imply high urgency, high risk, or high return on investment. The meaning of a large value depends on the selected business measure and the decision being made.

A responsible prioritization workflow should document:

- The outcome being measured.
- The population and reporting period.
- The treatment of inactive items, missing data, returns, and exceptional records.
- The threshold and any capacity constraints.
- The assumptions behind the measured values.
- The operational, legal, safety, and strategic constraints that can override a numerical ranking.

Pareto analysis is most useful when it narrows the field of investigation and makes trade-offs measurable. The final decision should combine contribution concentration with the business context, resource limits, and consequences of deprioritizing the remaining items.
