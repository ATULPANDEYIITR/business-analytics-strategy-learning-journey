# SQL Analytics Project: Retail Business Performance

## Project purpose

This project examines how a retail business can turn transaction-level sales records into measurable business performance indicators. It uses a realistic retail scenario involving customers, products, regions, payment methods, discounts, returns, and monthly sales.

The analysis separates revenue generation from profitability. A product can generate substantial sales while contributing relatively little profit, and a region with fewer transactions can still outperform a higher-volume region on margin. Customer purchase history also supports segmentation and retention analysis, while monthly aggregates provide a foundation for forecasting.

The dataset contains synthetic transactions designed to illustrate business patterns. It is not a record of an actual company's sales, and conclusions drawn from it should not be presented as findings about a real retailer.

## Business questions

The project investigates questions that arise in routine commercial reporting:

- Which regions generate the most recognized revenue and contribution profit?
- Which product categories deliver the strongest profit margins?
- How do discounts relate to revenue, profit, and return activity?
- Which customers account for the largest share of historical revenue?
- How does monthly performance change over time?
- Which order values warrant investigation as statistical outliers?
- How does customer activity change after the first purchase?
- What does a simple moving-average forecast indicate, and where are its limitations?

These questions require consistent definitions of sales, cost, profit, returns, and customer activity. The implementations make those definitions explicit rather than mixing incompatible measures.

## Business definitions

| Measure | Definition used in the project |
|---|---|
| Gross sales | Quantity multiplied by unit selling price before discounts |
| Discount amount | Gross sales multiplied by the discount rate |
| Net sales before returns | Gross sales minus discount amount |
| Recognized revenue | Discounted sales for non-returned transactions; zero for a returned order |
| Recognized cost | Quantity multiplied by unit cost for non-returned transactions; zero for a returned order |
| Contribution profit | Recognized revenue minus recognized cost |
| Profit margin | Contribution profit divided by recognized revenue |
| Average revenue per transaction | Recognized revenue divided by the number of transactions |
| Return rate | Returned transactions divided by all transactions |

The returned-order treatment is deliberately simplified. A returned order contributes zero revenue and zero cost to the recognized figures. This model is appropriate for demonstrating analytics on complete-order returns, but it does not represent every accounting treatment. Real businesses may recognize returns in separate periods, refund only part of an order, retain some inventory cost, or incur shipping and handling losses.

The project preserves transaction counts when calculating average revenue per transaction. Consequently, returned transactions contribute zero to the numerator but remain in the denominator. Analysts should state this convention when comparing the metric with reports that exclude returned orders entirely.

## Data model and data quality

The data has a transaction grain: each row represents one order containing one product. The core attributes are the order identifier, date, customer, region, product category, product, quantity, selling price, unit cost, discount, payment method, and return status.

The data quality rules protect calculations from errors that can otherwise spread into every report:

- Order identifiers must be present and unique.
- Customer, region, product, and category identifiers must not be blank.
- Quantity must be a positive integer.
- Selling price and unit cost must be finite, non-negative numbers.
- Discount rates must be between zero and one.
- Dates must be valid calendar dates rather than strings that merely resemble dates.
- Payment methods must belong to the supported business vocabulary.

Validation and deduplication serve different purposes. Validation checks whether a record conforms to business rules. Deduplication checks whether the same business key occurs more than once. A valid-looking duplicate can still inflate revenue, transaction counts, and customer lifetime value.

The Python and JavaScript implementations reject duplicate order identifiers instead of silently summing them. This is safer than treating duplicates as additional sales. In a production ingestion pipeline, duplicate handling should also consider source-system identifiers, idempotency keys, correction events, and the possibility that two records share an identifier but contain conflicting values.

## Python implementation

The Python program is a standard-library analytics pipeline organized around an immutable `Order` data class.

Its principal mechanisms are:

- **Transaction validation:** `validate_order()` checks field-level business rules, while `validate_dataset()` detects duplicate identifiers and invalid records across the dataset.
- **Reproducible sample data:** `create_business_dataset()` uses a fixed random seed, allowing results to be reproduced and changes to the analytics logic to be compared reliably.
- **Business aggregation:** `aggregate_sales()` calculates revenue, costs, profit, margin, return rate, and average transaction revenue. The grouping functions reuse those definitions for regional, category, payment, and monthly reports.
- **Customer segmentation:** `customer_metrics()` derives purchase history, revenue, profit, and a segment from lifetime recognized revenue.
- **Discount analysis:** `discount_analysis()` compares transactions and financial outcomes across discount bands.
- **Statistical investigation:** `detect_revenue_outliers()` applies the interquartile-range rule to order revenue.
- **Baseline forecasting:** `monthly_revenue_forecast()` produces a three-month moving-average forecast.
- **Customer cohorts:** `cohort_retention()` compares monthly customer activity with the customer's first-purchase month.
- **Demand estimation:** `inventory_proxy()` estimates average daily demand and a 30-day demand proxy from observed sales.
- **File integration:** CSV input and output, JSON reports, and a PostgreSQL-oriented SQL export allow the analysis to be reused in a data workflow.

Run the script without arguments to generate a reproducible dataset and report files. Supply a CSV path to analyze external transactions, and use `--test` to execute the included unit tests.

The CSV loader validates required columns, dates, numeric values, and business rules. It fails explicitly when a record is malformed. This behavior avoids producing an apparently successful report from incomplete or invalid data.

The SQL export escapes string literals and creates compatible table and insert statements. It is intended for learning and small exports. PostgreSQL `COPY` or parameterized database operations are more suitable for large-scale ingestion.

### Statistical limitations

The IQR rule flags unusually large or small revenue observations relative to the distribution. An outlier is not automatically fraudulent or incorrect. A large order might be a legitimate wholesale purchase, while a smaller order could reflect a valid promotional transaction.

The moving-average forecast is a transparent baseline rather than a full predictive model. It does not explicitly model annual seasonality, holidays, price changes, marketing activity, stockouts, or changing customer demand. Recursive forecasting also propagates previous forecast values into later periods, which can flatten variation.

The inventory estimate is based on sales history alone. It cannot calculate actual inventory on hand, days of stock remaining, reorder points, or stockout risk without inventory snapshots, receipts, lead times, and replenishment data.

## JavaScript implementation

The JavaScript implementation emphasizes asynchronous file ingestion and report generation in Node.js.

`readCsv()` consumes a readable stream through an asynchronous iterator. This avoids loading the entire input file into memory as one large string before parsing it. The resulting normalized records are then validated and analyzed.

`parseCsvLine()` handles quoted fields and escaped quotation marks within an individual CSV record. It is suitable for the simple, line-oriented files used by the project. It is not a complete general-purpose CSV implementation for files that permit quoted fields to contain embedded newlines.

The normalization stage converts raw string values into explicit numbers and booleans. `Object.freeze()` prevents later mutation of the normalized order objects, helping keep analytics operations predictable.

The report uses JavaScript `Map` objects to group transactions by business keys and customer identifiers. The customer analysis maintains product sets so distinct products can be counted without counting repeated purchases as new products.

The discount analysis applies explicit, mutually exclusive bands. The outlier function uses an interpolated percentile calculation, and the forecast operates on sorted monthly aggregates. Reports are written through temporary files and renamed into place after successful writes, reducing the chance that readers encounter a partially written JSON file.

The JavaScript implementation expects a CSV schema with the same business fields used by the Python program. When a CSV contains duplicate identifiers, execution fails instead of silently discarding the additional record.

## C++ case study

The C++ program treats retail analytics as a profitability engine with a validated transaction collection.

The `Transaction` structure holds the business facts, while `Metrics` provides an aggregate representation. `RetailAnalytics` owns the validated transactions and exposes separate methods for overall performance, regional metrics, monthly metrics, product rankings, forecasts, and high-value outlier detection.

Construction is the validation boundary. The constructor validates each record and rejects duplicate order identifiers before any aggregation can occur. This design avoids repeating basic integrity checks in every report method.

Regional and monthly reports use `std::map`, which keeps grouping keys ordered and produces deterministic output. Product ranking first aggregates profit by product and then sorts the results by descending profit, using product names as a tie-breaker.

The moving-average implementation retains a sequence of monthly revenue values and uses the latest three observations when available. Future predictions are appended to the history so later periods use the forecasted values as part of the rolling window.

The case study includes an invalid quantity example to demonstrate that validation failure is handled through a specific exception. The top-level exception handler reports unexpected failures and returns a non-zero process status.

For the small dataset used here, aggregation is linear in the number of transactions for each report. If many different reports repeatedly scan millions of transactions, pre-aggregated data, indexed storage, or a columnar analytical engine may be more efficient. The program deliberately keeps the calculation logic visible rather than introducing an external dependency.

## Java implementation

The Java program uses immutable records and a service-oriented domain model.

`Order` validates its own state when constructed. It rejects blank business identifiers, invalid quantities, non-finite prices, negative costs, and discounts outside the supported range. Because an order is validated at creation, downstream calculations can assume those basic invariants hold.

`SalesMetrics`, `CustomerProfile`, `ProductPerformance`, and `ForecastPoint` represent distinct analytical results. They keep transaction facts separate from derived customer and product measurements.

The `AnalyticsPolicy` interface isolates customer segmentation from the aggregation service. `DefaultCustomerPolicy` implements the project's revenue thresholds, while `AnalyticsService` accepts a policy through its constructor. This separation makes it possible to change segmentation rules without rewriting transaction aggregation.

The service uses Java streams for grouping and numeric aggregation. It returns immutable copies of input and result collections where appropriate. `TreeMap` provides chronological ordering for month-based reports, and customer results are sorted by lifetime revenue with a deterministic identifier tie-breaker.

The forecast validates its requested horizon and calculates each future period from the most recent three historical or forecast values. The negative-margin query identifies non-returned transactions where discounted revenue is lower than recognized cost.

The program also rejects duplicate identifiers at the service boundary. This prevents duplicate records from being counted as independent transactions even when each record is individually valid.

## PostgreSQL data model

The SQL implementation separates the customer dimension, product dimension, and transaction fact table.

| Relation | Responsibility |
|---|---|
| `customers` | Customer identity, signup date, home region, and stored segment |
| `products` | Product identity, category, list price, unit cost, and active status |
| `retail_orders` | Transaction date, customer, product, region, quantity, pricing, discount, payment method, and return status |

Primary keys establish row identity. Foreign keys prevent transactions from referring to unknown customers or products. Check constraints enforce quantity, price, cost, discount, payment-method, and descriptive-field rules at the database layer.

The indexes support common filtering and grouping patterns. The date index supports date-range analysis, the region/date index supports regional time series, and the customer/date index supports customer history queries. The product/date index supports product-level historical analysis. Indexes improve suitable access paths but add storage and write-maintenance costs, so their value should be measured against actual query plans and data volumes.

### Analytical views

`order_line_metrics` joins the transaction fact table to customer and product dimensions. It derives gross sales, discount amount, recognized revenue, recognized cost, and contribution profit once, creating a consistent base for downstream queries.

`regional_sales_metrics` calculates regional totals and margin. `monthly_sales_metrics` provides monthly revenue and profit. `category_profitability` measures product-category contribution and non-returned unit volume. `customer_lifetime_metrics` aggregates customer purchase history and derives a revenue-based customer segment.

The use of `NULLIF()` prevents division-by-zero errors in margin calculations. PostgreSQL's `FILTER` clause allows returned transactions to be counted separately without changing the underlying grouping.

### Window functions and analytical queries

The monthly comparison query uses `LAG()` to retrieve the preceding month's revenue. It calculates the absolute revenue change and relative growth rate without a self-join.

The moving-average query uses a window frame of the current row and two preceding rows. Early months have fewer than three available observations, so their averages use the available history.

The cohort query identifies each customer's first purchase month, records distinct monthly activity, and calculates activity relative to the acquisition cohort. In this dataset, the acquisition cohort is based on all orders, while subsequent activity counts only non-returned transactions. That distinction should be preserved when interpreting retention.

The outlier query computes the 25th and 75th percentiles using PostgreSQL's ordered-set aggregate, then applies the upper IQR threshold. Its results are investigation candidates, not automatically invalid records.

### Transactions and integrity

The data-loading phase is wrapped in a transaction. If a constraint fails during loading, PostgreSQL can roll back the transaction instead of leaving a partially loaded dataset.

The customer-segment update is also transactional. It updates the dimension from the lifetime metrics view, so every stored segment is derived from the same set of analytical rules during that operation.

The duplicate-key example is commented out because it intentionally causes a constraint violation. It can be executed separately inside a transaction to observe how the primary key rejects duplicate business identifiers.

The SQL script uses PostgreSQL-specific constructs, including `FILTER`, `date_trunc`, `percentile_cont`, window functions, and transactional DML. It should be run in PostgreSQL rather than an arbitrary SQL engine without checking dialect compatibility.

## Interpreting the results

### Revenue and profitability are different measures

Revenue measures the value recognized from transactions under the project's return convention. Profit subtracts the recognized cost. A high-revenue product may have a lower margin than a smaller product because unit economics and discounts differ.

Regional revenue rankings therefore answer a different question from regional margin rankings. A management decision should consider both, together with transaction volume, return behavior, and the cost of serving each region.

### Discount analysis is descriptive

Comparing profit margins across discount bands can expose commercial patterns. It cannot establish that a particular discount caused a change in profitability. Discounted transactions may differ from full-price transactions in product mix, order size, season, customer type, or promotional purpose.

A causal evaluation would require a more carefully controlled design, such as a randomized experiment or a defensible comparison strategy that accounts for relevant differences between groups.

### Customer value and retention require context

Lifetime revenue is a historical measure, not a guaranteed prediction of future spending. Customer segments based on fixed revenue thresholds may behave differently as prices, product mix, and the observation period change.

Cohort retention measures whether customers appear active in subsequent months. A transaction-level dataset without explicit account closure, consent, or inactivity definitions cannot distinguish a permanently lost customer from a customer who simply purchases infrequently.

### Forecast accuracy must be measured

The moving-average forecast provides a benchmark that is easy to explain and reproduce. It should not be considered reliable merely because it returns numeric predictions.

Forecast evaluation should reserve historical periods for testing, compare predictions with actual results, and report errors such as mean absolute error or weighted absolute percentage error where the denominator is meaningful. The evaluation should also consider seasonal patterns and major business changes.

## Production considerations

A production implementation would normally extend the model in several ways:

- **Returns:** store return events and returned quantities separately, preserving the original sale and the date on which the refund or reversal occurred.
- **Inventory:** add stock snapshots, replenishment events, supplier lead times, and stockout observations before calculating inventory coverage or reorder recommendations.
- **Financial accuracy:** define currency, tax treatment, shipping, payment fees, refund costs, and revenue-recognition rules before comparing reported profit with accounting statements.
- **Data lineage:** record the source system, ingestion time, source transaction identifier, and correction history so that reports can be reproduced and reconciled.
- **Access control:** use least-privilege database roles and parameterized queries for application inputs. Protect customer identifiers and avoid exposing unnecessary personal information in analytical exports.
- **Scale:** consider incremental aggregation, date partitioning, query-plan analysis, and workload-specific indexes as transaction volumes increase.
- **Monitoring:** track rejected rows, duplicate identifiers, missing values, unexpected return rates, and abrupt changes in aggregate metrics as data-quality signals.

The definitions used by all reports should be documented and version-controlled. A change to return handling, discount treatment, or the transaction grain can alter every downstream metric, so changes to these rules require deliberate validation and comparison against previous results.
