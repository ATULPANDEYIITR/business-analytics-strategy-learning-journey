# Executive Business Dashboard with Excel

## Purpose

An executive business dashboard converts operational business data into a compact management view of performance, trends, targets, profitability, and exceptions.

The central design problem is not simply creating attractive Excel charts. A reliable dashboard must establish a controlled relationship between source data, calculations, business definitions, visual components, filters, and management decisions.

This project models that process through three complementary implementations:

- The Python program builds validated transaction data, calculates business KPIs, creates monthly summaries, performs target variance analysis, measures concentration, and exports dashboard-ready CSV datasets that Excel can consume.
- The JavaScript program models an event-driven dashboard state. It supports filters, recalculation, subscriptions, dimensional aggregation, monthly trends, target variance, and presentation-oriented state updates.
- The C++ program presents a typed governance and analytics engine that validates business records, aggregates them by management dimensions, calculates weighted margins, evaluates target performance, and generates material executive alerts.

The implementations deliberately use different perspectives rather than translating the same program between languages.

---

## Executive Dashboard Architecture

A practical Excel dashboard can be understood as a layered system:

`Source Data → Validation → Calculation Layer → Summary Tables → Dashboard Visuals → Filters → Management Interpretation`

The source data contains transaction-level facts such as date, region, product, channel, units, revenue, and cost.

The calculation layer derives measures such as gross profit, gross margin, average transaction value, monthly revenue, and target variance.

The summary layer organizes those calculations into structures appropriate for Excel charts, KPI cards, PivotTables, and conditional formatting.

The dashboard layer presents a small number of high-value indicators rather than exposing every source field.

Filters and slicers change the analytical population without changing the underlying source data.

The management interpretation layer is deliberately separate from the calculations. A dashboard can identify that revenue is below target, but the reason for that variance requires business investigation.

---

## Core Business Data Model

The transaction model used by the implementations contains:

| Field | Meaning | Dashboard relevance |
|---|---|---|
| Transaction Date | Date associated with the sale | Enables time-series analysis |
| Region | Geographic business area | Supports regional performance comparisons |
| Product | Product or service sold | Supports portfolio analysis |
| Channel | Direct, online, or partner route | Shows channel contribution |
| Units | Quantity sold | Measures volume |
| Revenue | Recorded sales value | Primary financial KPI |
| Cost | Associated business cost | Required for profitability |
| Gross Profit | Revenue minus cost | Measures absolute profitability |
| Margin | Gross profit divided by revenue | Measures profitability relative to revenue |

Revenue and cost are treated as additive financial measures.

Margin is not safely aggregated by simply averaging row-level percentages. A weighted margin is calculated as total gross profit divided by total revenue. This prevents a small transaction with a high percentage margin from receiving the same influence as a large transaction.

---

## Executive KPI Design

The Python implementation calculates a core executive KPI set:

- **Revenue** measures total sales value for the selected dataset.
- **Gross Profit** is revenue minus cost.
- **Gross Margin** is gross profit divided by revenue.
- **Units** represents total business volume.
- **Transactions** represents the number of source records.
- **Average Transaction Value** divides revenue by transaction count.

These measures answer different management questions. Revenue describes scale, while gross profit describes absolute contribution. Margin provides a relative profitability measure. Units show volume, and average transaction value provides a transaction-level commercial indicator.

A dashboard should not place every available metric into the primary view. A KPI becomes useful when its definition, time period, population, and comparison basis are clear.

---

## Time-Series Analysis

Monthly aggregation is implemented separately from transaction-level data.

The Python `monthly_summary()` function creates a dashboard-ready table containing:

`month`, `revenue`, `cost`, `gross_profit`, `margin`, and `units`.

The JavaScript implementation creates the equivalent analytical concept through `buildMonthlyTrend()`.

The C++ implementation stores monthly results in `MonthlyPerformance`.

This separation is important because an Excel line chart should normally consume an organized time-series table rather than repeatedly calculating transaction-level expressions inside the chart itself.

A monthly dashboard can display:

- Revenue trend
- Gross profit trend
- Margin trend
- Units trend
- Actual versus target revenue

Time periods must use consistent definitions. A dashboard comparing calendar months should not silently mix calendar months with fiscal periods.

---

## Actual Versus Target Analysis

An executive dashboard becomes more useful when actual performance is compared with a defined management target.

The project models target revenue independently from actual revenue. The target begins from an initial planning relationship and then progresses through monthly growth assumptions.

For each month, the variance engine calculates:

`Variance = Actual Revenue - Target Revenue`

and:

`Variance % = Variance / Target Revenue`

A positive variance indicates that actual revenue exceeds the modeled target. A negative variance indicates that actual revenue is below the target.

The Python `variance_report()` function returns the resulting management table.

The JavaScript `calculateVariance()` function creates the same analytical relationship inside the dashboard state model.

The C++ `Variance` structure encapsulates the relationship between actual and target values and exposes methods for variance amount, variance percentage, and target status.

The target model is intentionally separate from the source data. If the target were copied directly from actual revenue, the dashboard would not provide meaningful performance measurement.

---

## Regional, Product, and Channel Analysis

### Regional Analysis

Regional aggregation answers where business revenue is being generated.

The Python implementation uses `group_revenue()` and `group_profit_margin()` to aggregate by `region`.

The JavaScript model uses `aggregateBy(sales, "region")`.

The C++ engine exposes `byRegion()`.

Regional analysis can reveal situations such as:

- A region contributing a large proportion of total revenue.
- A region generating high revenue but relatively low margin.
- A region whose revenue is below the management target.
- Geographic concentration that creates dependency on one market.

The implementations also calculate revenue concentration for the largest region. This is an analytical signal, not a diagnosis of business risk by itself.

### Product Analysis

Product analysis examines the economics of the portfolio rather than geography.

The dataset contains four products with different price and margin characteristics. This creates meaningful variation in both revenue and profitability.

A product can have high revenue without having the highest margin. Conversely, a product with a strong margin percentage may have a smaller contribution to total gross profit if its sales volume is low.

The dashboard therefore keeps revenue and margin as separate measures.

### Channel Analysis

Channel analysis distinguishes Direct, Online, and Partner sales.

The channel dimension is particularly useful when management wants to understand whether commercial performance is being generated through the organization's own sales operation or through external distribution mechanisms.

Channel revenue should be evaluated alongside transaction volume and profitability rather than treated as a standalone ranking.

---

## Python Implementation

The Python program acts as a data preparation and analytical engine for an Excel workflow.

### Source generation

`generate_sales_data()` creates a six-month transaction dataset. It includes regional multipliers, product prices, product-level margin assumptions, channel factors, transaction quantities, and month-end demand variation.

The deterministic random seed makes the generated dataset reproducible. Reproducibility is useful when testing dashboard calculations because the same input produces the same analytical result.

### Validation

`validate_record()` prevents invalid source rows from reaching KPI calculations.

The validation rules include:

- Recognized regions
- Recognized products
- Recognized channels
- Positive unit quantities
- Non-negative revenue
- Non-negative cost
- Cost not exceeding revenue

This is important because spreadsheet formulas generally cannot determine whether a business transaction is semantically valid. Data validation must occur at the source or preparation layer.

### Dashboard exports

The program writes:

- `sales_data.csv`
- `monthly_dashboard.csv`
- `variance_dashboard.csv`

The first file represents the normalized transaction source.

The second contains monthly KPI and trend measures.

The third contains actual-versus-target performance.

These tables can be imported into Excel and used as sources for PivotTables, charts, formulas, or Power Query transformations.

### Advanced analytical signals

The Python program also calculates revenue concentration and the correlation between transaction revenue and units.

These calculations illustrate why executive dashboards should contain analytical context rather than only raw totals.

---

## JavaScript Implementation

The JavaScript implementation models a dashboard as a stateful, event-driven application rather than as a static report.

### Dashboard state

`DashboardModel` stores:

- Source sales
- Active filters
- Current KPI snapshot
- Regional performance
- Product performance
- Channel performance
- Monthly trend
- Target variance
- Update timestamp

The model separates state from presentation.

### Event-driven refresh

The `subscribe()` method allows presentation components to register listeners.

When `setFilter()` changes the dashboard state, `refresh()` recalculates the filtered dataset and generates a new snapshot. Registered listeners are then notified.

This mirrors the behavior of a browser dashboard where changing a filter or slicer causes multiple visual components to refresh.

The approach avoids hard-coding a separate calculation into every visual.

### Filtering

`filterSales()` supports filtering by:

- Region
- Product
- Channel
- Start date
- End date

The filters operate on the source population before KPI calculations are performed. This means the KPI cards and analytical tables use the same filtered population.

### Error handling

The JavaScript implementation deliberately validates source records before processing them. Invalid dimensions, invalid quantities, non-finite values, and impossible cost relationships are rejected.

The use of `structuredClone()` when returning a dashboard snapshot also prevents callers from accidentally modifying the internal state object.

---

## C++ Case Study

The C++ program models an executive analytics engine for a business reporting system.

Its architecture is separated into three major responsibilities:

`SalesRepository → DashboardValidator → DashboardEngine`

The repository creates the business dataset.

The validator establishes data-quality constraints.

The engine performs aggregation, target evaluation, and alert generation.

### Typed data structures

`SalesRecord` represents an individual transaction.

`Aggregate` stores accumulated revenue, cost, units, and transaction count.

`MonthlyPerformance` represents a time-series aggregate.

`Variance` encapsulates the relationship between actual and target values.

`Alert` represents a material management exception.

This structure makes the analytical domain explicit rather than passing unstructured collections of values throughout the application.

### Aggregation

The engine supports:

- Regional aggregation
- Product aggregation
- Channel aggregation
- Monthly aggregation

The generic private `aggregateBy()` method accepts a key-extraction function. This demonstrates how strongly typed C++ code can reuse aggregation mechanics while still exposing business-specific public operations such as `byRegion()` and `byProduct()`.

### Alert generation

The C++ implementation does not treat every variance as an executive alert.

A revenue variance below the target is classified according to materiality:

- A variance of 8% or more below target produces a high-severity revenue alert.
- A smaller negative variance produces a medium-severity alert.

The engine also examines regional revenue concentration.

This demonstrates an important dashboard design principle: executive dashboards should prioritize material exceptions instead of displaying every possible anomaly.

---

## Excel Workbook Structure

A practical workbook based on these implementations can be organized into separate logical layers.

### Source Data

The source worksheet should contain one row per transaction and one column per field.

The transaction table should not contain manually merged cells, decorative blank rows, or repeated subtotal rows. A normalized table makes filtering, PivotTables, Power Query, formulas, and refresh operations more reliable.

### Calculations

Calculation worksheets can contain:

- Monthly aggregation
- Regional aggregation
- Product aggregation
- Channel aggregation
- Target calculations
- Variance calculations
- Supporting business measures

Keeping complex calculations away from the executive presentation reduces accidental changes to the visual layer.

### Dashboard

The primary dashboard can contain:

- KPI cards for revenue, gross profit, margin, units, and average transaction value
- A monthly revenue trend
- Actual versus target visualization
- Regional performance
- Product performance
- Channel performance
- Material exception indicators
- Interactive filters or slicers

The dashboard should use a consistent reporting period. If the selected date range changes, the KPI cards and charts should respond to the same filter population.

---

## Recommended Excel Formula Relationships

If the transaction source is stored as an Excel Table named `SalesData`, a row-level gross profit calculation can be represented conceptually as:

`=[@Revenue]-[@Cost]`

A row-level margin can be represented as:

`=IFERROR([@[Gross Profit]]/[@Revenue],0)`

For executive aggregation, total margin should be calculated from aggregated revenue and aggregated gross profit rather than by averaging the row-level margin column.

A management variance calculation can be represented as:

`=Actual-Target`

The corresponding variance percentage can be represented as:

`=IFERROR(Variance/Target,0)`

These formulas demonstrate the relationship between the underlying measures. The precise worksheet references should be adapted to the workbook's actual table and column names.

---

## Dashboard Visual Design

A useful executive layout generally places the highest-level metrics near the top.

A conceptual structure is:

```text
+-------------------------------------------------------------------+
|                     EXECUTIVE BUSINESS DASHBOARD                  |
+----------------+----------------+----------------+----------------+
| Revenue        | Gross Profit   | Margin         | Units          |
+----------------+----------------+----------------+----------------+
|                     Monthly Revenue Trend                        |
|                                                                   |
+-------------------------------------------------------------------+
| Actual vs Target                 | Regional Performance         |
|                                   |                              |
+-----------------------------------+------------------------------+
| Product Performance               | Channel Performance         |
|                                   |                              |
+-----------------------------------+------------------------------+
| Material Exceptions / Management Signals                           |
+-------------------------------------------------------------------+
