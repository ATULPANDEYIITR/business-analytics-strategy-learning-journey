# Executive Dashboard: Management Performance Reporting with Power BI

## Business purpose

This project defines an executive performance dashboard for management teams monitoring revenue, profitability, order fulfilment, delivery reliability, and customer satisfaction.

The dashboard uses monthly results across two business units and two regions. Actual performance is evaluated against management targets. Managers can examine the consolidated position, identify underperforming segments, and inspect the operational indicators behind financial results.

The model is designed around five management questions:

- Is revenue meeting the approved target?
- Are revenue and operating profit translating into sustainable margins?
- Are customer orders being delivered, and are deliveries on time?
- Is customer satisfaction improving or deteriorating?
- Which business unit or region requires management attention?

The five source files implement data validation, aggregation, policy evaluation, access restrictions, and relational reporting. The report design and DAX measures described below define how these outputs are presented in Power BI.

## Dashboard operating model

The dashboard separates source facts, management targets, calculations, and presentation.

```text
Monthly operational and financial records
                    |
                    v
           Data validation and loading
                    |
                    v
            PostgreSQL data model
                    |
          +---------+---------+
          |                   |
          v                   v
    Actual performance   Management targets
          |                   |
          +---------+---------+
                    |
                    v
              KPI calculations
                    |
                    v
           Power BI semantic model
                    |
          +---------+----------+
          |         |          |
          v         v          v
       Overview  Performance  Operations
          |         |          |
          +---------+----------+
                    |
                    v
           Management decisions
```

The dashboard is a management reporting system, not simply a collection of charts. Financial, operational, and customer measures retain their own calculation rules. A change in a filter recalculates the measures for the selected reporting context.

## Management KPI framework

The measures use additive source values wherever possible. Ratios are calculated after aggregation. This prevents the dashboard from producing misleading results by averaging percentages or averages from separate regions.

| KPI | Calculation | Management interpretation |
|---|---|---|
| Revenue | Sum of actual revenue | Business scale and financial performance |
| Revenue target | Sum of approved revenue targets | Expected performance for the selected period |
| Revenue attainment | Revenue divided by revenue target | Progress against plan |
| Gross profit | Revenue minus cost of goods sold | Profit remaining after direct costs |
| Gross margin | Gross profit divided by revenue | Direct-cost efficiency |
| Operating profit | Gross profit minus operating expenses | Profit after recorded operating expenses |
| Operating margin | Operating profit divided by revenue | Operating profitability |
| Order fulfilment | Delivered orders divided by orders | Proportion of orders delivered |
| On-time delivery | On-time orders divided by delivered orders | Delivery reliability |
| Average CSAT | Sum of customer scores divided by response count | Average customer satisfaction |

### KPI calculation rules

**Revenue attainment**

Revenue attainment compares actual revenue with the sum of targets for the selected period and reporting segments.

A result of 100% means actual revenue equals the target. A result below 100% indicates a shortfall. A result above 100% indicates that the target has been exceeded.

The dashboard uses the ratio of aggregate revenue to aggregate target. It does not average individual regional attainment percentages.

**Gross margin**

Gross margin measures the proportion of revenue remaining after cost of goods sold.

The calculation is:

`(Revenue - COGS) / Revenue`

A falling gross margin can indicate increased input costs, discounting, pricing pressure, or an unfavourable sales mix. Management should examine revenue and COGS together rather than interpret the percentage in isolation.

**Operating margin**

Operating margin accounts for both direct costs and operating expenses.

The calculation is:

`(Revenue - COGS - Operating Expenses) / Revenue`

It provides a broader view of operating performance than gross margin.

**Order fulfilment and delivery reliability**

These are separate indicators:

- Order fulfilment measures delivered orders against all orders.
- On-time delivery measures on-time orders against delivered orders.

An organisation may have a high on-time delivery rate among completed deliveries while still having a significant number of undelivered orders. Showing both indicators prevents that distinction from being hidden.

**Customer satisfaction**

The average is calculated using the total score divided by the total response count.

The model assumes a response scale from 1 to 5. It does not average regional CSAT averages without considering their response counts. The response count should be displayed beside the average to give management visibility into the strength of the underlying evidence.

## Report page design

### 1. Executive overview

This is the landing page for senior management. It should provide the organisation's current performance position without requiring users to inspect detailed transaction records.

Recommended layout:

| Area | Power BI visual | Information |
|---|---|---|
| Top row | KPI cards | Revenue, attainment, gross margin, operating profit |
| Middle left | Line chart | Monthly revenue against target |
| Middle right | Bar chart | Revenue by business unit |
| Lower left | Matrix | Business unit and region performance |
| Lower right | Alert table | KPI breaches requiring attention |
| Header | Slicers | Reporting period, business unit, region |

The landing page should use a consistent reporting period across all visuals. KPI cards should show the current value and, where relevant, a comparison with the target.

### 2. Financial performance

This page supports deeper examination of revenue, costs, and profitability.

Recommended visuals:

- Monthly revenue and revenue target as a line and clustered column combination.
- Gross profit and operating profit by business unit.
- Gross margin and operating margin by region.
- A matrix containing revenue, target, attainment, COGS, gross profit, operating expenses, and operating profit.

The page should make it possible to identify whether a revenue shortfall is concentrated in a specific business unit or region. It should also show whether revenue growth is accompanied by a reduction in margin.

### 3. Operational performance

This page focuses on order execution.

Recommended visuals:

- Order count and delivered-order trend.
- Order fulfilment percentage by region.
- On-time delivery percentage by business unit.
- A matrix of orders, delivered orders, on-time orders, and outstanding undelivered orders.

Outstanding undelivered orders can be calculated as orders minus delivered orders. This is a derived operational measure and should not be described as an aged backlog unless the underlying data contains order-age information.

### 4. Customer experience

This page examines the customer satisfaction measure and its evidence base.

Recommended visuals:

- Monthly average CSAT trend.
- CSAT by business unit and region.
- Customer satisfaction against the management target.
- Survey response count beside the average score.

Averages should always be interpreted with their sample sizes. A change in response volume can affect the reliability of comparisons between reporting segments.

### 5. Management action and exceptions

This page consolidates underperformance and highlights where management review is needed.

The supplied implementations evaluate the following example thresholds:

| Indicator | Example threshold | Alert meaning |
|---|---|---|
| Revenue attainment | Below 95% | Critical revenue shortfall |
| Revenue attainment | 95% to below 100% | Revenue below plan |
| Gross margin | Below 35% | Critical margin position |
| On-time delivery | Below 90% | Critical delivery position |
| Average CSAT | Below 4.0 out of 5 | Customer satisfaction warning |

These thresholds are configurable business policies, not universal financial or operational standards. The organisation should approve them and assign accountable owners before they are used for formal performance management.

## Data model

The PostgreSQL model follows a star-schema approach with shared dimensions and separate fact tables.

### Dimensions

| Table | Grain | Purpose |
|---|---|---|
| `dim_month` | One row per month | Reporting year, month, quarter, and label |
| `dim_business_unit` | One row per business unit | Business-unit filtering and classification |
| `dim_region` | One row per region | Regional filtering and comparison |

### Fact tables

| Table | Grain | Main fields |
|---|---|---|
| `fact_monthly_actual` | Month, business unit, region | Revenue, COGS, expenses, orders, deliveries, CSAT totals |
| `fact_monthly_target` | Month, business unit, region | Revenue, margin, delivery, and CSAT targets |

Actuals and targets are separate because they represent different business facts. Combining them into one table with repeated target values can cause targets to be counted multiple times during aggregation.

The primary key on each fact table prevents duplicate reporting records at the declared monthly grain. The actual fact references the corresponding target row, ensuring that an actual reporting segment has a matching target.

### Power BI relationships

Create one-to-many, single-direction relationships from each dimension to both fact tables.

| One-side table | Many-side table | Relationship |
|---|---|---|
| `dim_month` | `fact_monthly_actual` | `month_start` |
| `dim_month` | `fact_monthly_target` | `month_start` |
| `dim_business_unit` | `fact_monthly_actual` | `business_unit_id` |
| `dim_business_unit` | `fact_monthly_target` | `business_unit_id` |
| `dim_region` | `fact_monthly_actual` | `region_id` |
| `dim_region` | `fact_monthly_target` | `region_id` |

Do not create a direct relationship between the two fact tables. Shared dimensions should filter both facts. This structure allows revenue and target measures to respond to the same month, business-unit, and region selections without introducing ambiguous fact-to-fact filtering.

Use the dimension columns for slicers rather than fields copied from fact tables.

## DAX measures for the Power BI semantic model

The following measures assume that the source tables have been imported with the names used below. Monetary values in PostgreSQL are stored in cents, so the measures divide by 100 for presentation in the model's currency unit.

**Revenue**

`Revenue = DIVIDE(SUM(FactMonthlyActual[revenue_cents]), 100)`

**Revenue Target**

`Revenue Target = DIVIDE(SUM(FactMonthlyTarget[revenue_target_cents]), 100)`

**Revenue Attainment**

`Revenue Attainment % = DIVIDE([Revenue], [Revenue Target])`

Format this measure as a percentage in Power BI. Do not multiply by 100 again when using percentage formatting.

**COGS**

`COGS = DIVIDE(SUM(FactMonthlyActual[cogs_cents]), 100)`

**Gross Profit**

`Gross Profit = [Revenue] - [COGS]`

**Gross Margin**

`Gross Margin % = DIVIDE([Gross Profit], [Revenue])`

**Operating Expenses**

`Operating Expenses = DIVIDE(SUM(FactMonthlyActual[operating_expense_cents]), 100)`

**Operating Profit**

`Operating Profit = [Gross Profit] - [Operating Expenses]`

**Operating Margin**

`Operating Margin % = DIVIDE([Operating Profit], [Revenue])`

**Orders**

`Orders = SUM(FactMonthlyActual[order_count])`

**Delivered Orders**

`Delivered Orders = SUM(FactMonthlyActual[delivered_orders])`

**Order Fulfilment**

`Order Fulfilment % = DIVIDE([Delivered Orders], [Orders])`

**On-Time Orders**

`On-Time Orders = SUM(FactMonthlyActual[on_time_orders])`

**On-Time Delivery**

`On-Time Delivery % = DIVIDE([On-Time Orders], [Delivered Orders])`

**CSAT Responses**

`CSAT Responses = SUM(FactMonthlyActual[csat_responses])`

**Average CSAT**

`Average CSAT = DIVIDE(SUM(FactMonthlyActual[csat_score_sum]), [CSAT Responses])`

Use `DIVIDE` rather than direct division so that zero denominators produce a blank result instead of a calculation error.

The DAX measures recalculate in the filter context supplied by the shared dimensions. The target measures must use the target fact table, and actual measures must use the actual fact table.

## Implementation details

### Python: validated reporting and snapshot generation

The Python implementation provides the main data-processing workflow.

It uses:

- Frozen dataclasses for monthly performance records and filter state.
- `Decimal` for financial and score calculations.
- Explicit conversion of CSV values into their domain types.
- Sets to detect duplicate month, business-unit, and region keys.
- Validation of financial values, order counts, and survey totals.
- Aggregation of additive measures before percentage calculation.
- Threshold-based alert evaluation.
- JSON serialization for downstream reporting.
- Assertions for duplicate records, invalid delivery counts, and empty-filter behaviour.

The CSV loader rejects missing fields and invalid values. It reports the line that caused an import failure rather than silently discarding bad records.

The JSON output contains both source records and a calculated dashboard snapshot. This allows the JavaScript implementation to consume the same reporting data.

Example execution:

- `python executive_dashboard.py`
- `python executive_dashboard.py --region North`
- `python executive_dashboard.py --from-month 2026-01 --to-month 2026-03`
- `python executive_dashboard.py --output executive_snapshot.json`

The script uses built-in Python libraries and does not require an external package.

### JavaScript: event-driven dashboard state

The JavaScript implementation represents an interactive dashboard service.

Its `ExecutiveDashboard` class maintains the active filter state and emits events when filters change or a new snapshot is ready.

The main mechanisms are:

- `EventEmitter` for filter and snapshot events.
- `Map` for business-unit and regional aggregation.
- `Set` for duplicate-key detection.
- Asynchronous refresh through the Node.js event loop.
- A refresh sequence number to discard outdated results.
- Immutable record and snapshot objects.
- An `AlertPolicy` object for threshold evaluation.
- Input file size checks before JSON parsing.

The refresh sequence is important when filter changes occur close together. A result created for an older filter state should not replace a more recent dashboard result.

The script can use the snapshot created by Python:

- `node executive_dashboard.js`
- `node executive_dashboard.js --input executive_snapshot.json`

The example performs an all-region refresh followed by a North-region refresh. The event stream makes the filter and refresh sequence explicit.

### C++17: aggregation engine

The C++ implementation provides a performance-oriented aggregation engine.

Its design uses:

- Structures for source records, filters, metrics, and dashboard results.
- Integer cents for financial aggregation.
- Checked integer addition to detect aggregation overflow.
- `std::optional` for ratios that cannot be calculated.
- `std::unordered_set` for duplicate reporting-key validation.
- `std::map` for ordered segment results.
- Regular expressions for reporting-month validation.
- Exception handling for invalid source data and processing failures.

The engine filters records and calculates executive and segment-level results in one traversal. It does not average regional percentages to produce executive ratios. It accumulates the underlying values first.

The built-in assertions verify the total record count, segment count, regional filtering, and no-data behaviour.

Compile and execute with:

- `g++ -std=c++17 -O2 executive_dashboard.cpp -o executive_dashboard`
- `./executive_dashboard`

### Java 17: enterprise dashboard service

The Java implementation models an enterprise reporting service with explicit access scopes and policy objects.

Its domain types include:

- `MonthlyPerformance` for validated monthly data.
- `AccessScope` for authorised regions and business units.
- `DashboardRequest` for reporting-period and segment filters.
- `KpiSnapshot` for calculated indicators.
- `Alert` for management exceptions.
- `MetricPolicy` for interchangeable alert rules.

Java records make the core domain objects immutable. The `DashboardService` applies the user's access scope before applying report filters and calculating metrics.

The four roles have different scope rules:

| Role | Access rule |
|---|---|
| Executive | All regions and business units |
| Regional manager | Explicitly assigned regions |
| Business-unit manager | Explicitly assigned business units |
| Analyst | Explicitly assigned regions and business units |

A user cannot request a region or business unit outside the user's authorised scope. An unauthorised request raises an `AccessDeniedException`.

The alert policies are separate objects. Their thresholds can be changed without rewriting the aggregation service.

Compile and run with:

- `javac --release 17 ExecutiveDashboard.java`
- `java ExecutiveDashboard`

### PostgreSQL: reporting database

The SQL implementation is the relational foundation for the Power BI semantic model.

It includes:

- Reporting dimensions and monthly fact tables.
- Primary, foreign, unique, and check constraints.
- Separate target and actual records.
- Indexes for common regional, business-unit, and period filters.
- Views for detailed, executive, and segment reporting.
- A parameterized dashboard summary function.
- Row-level security policies.
- Sample records and reporting queries.

The detailed view calculates monthly KPIs. The executive view recalculates ratios from additive totals. The segment view groups results by business unit and region.

The `fn_dashboard_summary` function accepts a reporting period and optional region and business-unit identifiers. It checks reporting-period boundaries before calculating the result.

Run the script against PostgreSQL with:

`psql -d analytics -f executive_dashboard.sql`

The script uses PostgreSQL 15 or later because the reporting views use the `security_invoker` view option.

## Power BI implementation workflow

### Connect the relational model

In Power BI Desktop:

1. Connect to the PostgreSQL database using the PostgreSQL database connector.
2. Import the three dimensions and both monthly fact tables.
3. Set the data types for dates, identifiers, counts, and monetary amounts.
4. Create the one-to-many relationships specified in the data-model section.
5. Confirm that all dimensions filter both fact tables.
6. Add the DAX measures to the semantic model.
7. Build the overview, financial, operational, customer, and management-action pages.

The detailed SQL view can also be imported for reporting and reconciliation. Avoid loading duplicate versions of the same fact data without a clear purpose.

### Configure the semantic model

Use the following model conventions:

| Model element | Configuration |
|---|---|
| Date dimension | Mark as the model's date table |
| Currency measures | Format with the approved reporting currency |
| Attainment and margin | Percentage format |
| CSAT | Numeric format with one or two decimal places |
| Counts | Whole-number format |
| Empty ratios | Preserve blanks rather than displaying misleading zero percentages |
| Slicers | Use date, business-unit, and region dimensions |

For financial reporting, confirm the currency, reporting calendar, accounting definitions, and treatment of adjustments with the finance function. The sample data uses a single unspecified currency unit and is not an accounting ledger.

### Design standards for management use

The dashboard should follow consistent visual conventions:

- Place the reporting period and active filters in a visible location.
- Display targets beside actual values.
- Use the same units and decimal precision across comparable visuals.
- Use colour to signal approved performance states, not as decoration.
- Show the exact reporting period and last refresh time.
- Keep detailed operational data behind the management-level indicators.
- Allow managers to drill from the consolidated view to the responsible region and business unit.
- Avoid presenting an empty or unavailable ratio as zero performance.

A KPI card should answer one question clearly. A trend chart should show whether performance is improving or deteriorating. A segment matrix should help management locate the source of a variance.

## Security and data governance

A management dashboard can expose financial and operational information across business units and regions. Access should be designed before report distribution.

### Power BI row-level security

Create Power BI roles for the organisation's approved access structure. Apply region and business-unit restrictions through the security model, not through ordinary slicers.

A slicer is a reporting control, not a security boundary. A user must not gain access to another region simply by changing a report selection.

Test each role with representative user accounts. Validate both report visuals and underlying model access.

### PostgreSQL row-level security

The SQL script enables row-level security on the actual and target facts.

The policies read two session settings:

- `app.allowed_region_ids`
- `app.allowed_business_unit_ids`

Both are required. Missing scope values result in no fact rows being visible to a role subject to the policies.

A trusted application layer must establish these settings from authenticated identity. Report parameters must never be treated as proof of authorisation.

The SQL table owner and privileged database roles can have different row-level security behaviour. Production access should use a dedicated, least-privilege reporting role rather than the schema owner or a superuser.

When Power BI uses a connection pool or gateway, session identity and session-setting behaviour must be tested. A session setting must not leak between users. Where the reporting connection cannot establish a trusted database session scope, enforce access through Power BI RLS and a suitably restricted data-access architecture.

### Operational controls

Before production deployment:

- Restrict write access to approved data-loading services.
- Give dashboard consumers read-only permissions.
- Keep database credentials outside source files and report parameters.
- Use encrypted database connections.
- Record refresh failures and data-quality failures.
- Validate source totals against approved finance and operations reports.
- Maintain an approved definition and owner for each KPI.
- Review access scopes when employees change roles or responsibilities.

## Validation and exception handling

The implementations reject duplicate reporting keys and invalid data rather than silently producing a dashboard from inconsistent records.

| Failure condition | Expected handling |
|---|---|
| Duplicate monthly reporting key | Reject the dataset |
| Missing CSV field | Stop the import and identify missing columns |
| Invalid reporting month | Reject the record or filter |
| Negative financial amount | Reject the record |
| Zero revenue target | Reject the record |
| Delivered orders exceed orders | Reject the record |
| On-time orders exceed delivered orders | Reject the record |
| Invalid CSAT total | Reject the record |
| Zero denominator in a ratio | Return an unavailable value |
| No records match filters | Produce a no-data alert |
| Unauthorised Java dashboard filter | Reject the request |
| Database scope not configured | Row-level security returns no matching fact rows |

The system does not automatically replace missing financial values with zero. Missing data and a genuine zero are different business conditions and should remain distinguishable.

## Performance considerations

The reporting grain is monthly. It is suitable for management trend reporting but does not provide transaction-level analysis.

The database primary keys support the composite reporting grain. Additional indexes support common region, business-unit, and reporting-period filter patterns. More indexes should only be added after reviewing actual query plans and workload.

The Python and JavaScript implementations aggregate the selected records in memory. Their work is linear in the number of input records, excluding grouping and sorting overhead.

The C++ implementation uses ordered maps for deterministic segment output and hash-based duplicate detection. Financial totals use checked integer arithmetic.

For larger Power BI deployments:

- Use a maintained date dimension covering the full reporting calendar.
- Consider incremental refresh when the fact volume and refresh pattern justify it.
- Avoid importing unused columns.
- Prefer measures over unnecessary calculated columns.
- Use an appropriate storage mode for the database workload.
- Monitor refresh duration, model size, and query performance.
- Test filter behaviour with realistic data volumes.

## Data assumptions and limitations

The sample dataset contains 12 monthly records covering January to March 2026, two business units, and two regions.

It is illustrative data, not evidence of actual organisational performance.

The model assumes:

- Monthly reporting periods begin on the first calendar day.
- Each business-unit and region combination has one actual record per month.
- Each actual record has a corresponding target record.
- Revenue, COGS, and operating expenses use one consistent currency unit.
- Customer satisfaction responses use a 1-to-5 scale.
- `on_time_orders` is a subset of delivered orders.
- `delivered_orders` is a subset of total orders.

The current model does not include:

- Transaction-level sales or order records.
- Product-level profitability.
- Customer-level segmentation.
- Cash flow, receivables, or working capital.
- Budget version history or target approval workflows.
- Forecasts and scenario planning.
- Inventory, workforce, or capacity data.
- Order ageing or backlog ageing.
- Currency conversion.
- Year-over-year comparisons.
- Automated source-system connections.
- A Power BI `.pbix` report binary.

These should not be inferred from the sample measures. They require additional source data and agreed business definitions.

## File execution reference

| Source file | Runtime | Main responsibility |
|---|---|---|
| `executive_dashboard.py` | Python 3 | Data validation, KPI calculations, CSV loading, JSON snapshot |
| `executive_dashboard.js` | Node.js | Event-driven filters, asynchronous refresh, segmentation, alerts |
| `executive_dashboard.cpp` | C++17 | Checked financial aggregation and segment-level performance |
| `ExecutiveDashboard.java` | Java 17 | Enterprise access scopes, domain validation, and alert policies |
| `executive_dashboard.sql` | PostgreSQL 15+ | Relational reporting model, constraints, views, security, and queries |

The Python snapshot can be passed to the JavaScript implementation. The C++ and Java programs contain standalone sample datasets so that their calculation and access-control behaviour can be executed independently.

The dashboard definitions, relational data model, and source implementations use the same monthly business-unit and regional reporting grain. For a production Power BI deployment, the organisation must still connect approved source systems, configure its semantic model and report pages, assign access roles, and publish the reviewed report.
