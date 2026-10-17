# Customer, Product, Geographic, and Behavioral Segmentation

## Scope

This project models four related but distinct forms of market segmentation:

- **Customer segmentation** groups customers according to relatively stable attributes such as age, income, loyalty tier, acquisition channel, and preferences.
- **Product segmentation** groups products according to characteristics such as category, product family, price, and margin.
- **Geographic segmentation** groups customers according to physical market location such as country, region, and city.
- **Behavioral segmentation** derives groups from observed customer actions, particularly transaction frequency, recency, monetary value, product-category diversity, and channel usage.

The distinction is important. A customer being located in a particular region is a geographic fact. A customer having high income is a customer attribute. A product having a high margin is a product characteristic. A customer making repeated purchases is behavioral evidence. These dimensions can be combined for analysis, but they should not be treated as interchangeable.

## Segmentation Model

The implementations use a retail-style dataset containing customers, products, locations, and purchase transactions.

A customer record contains demographic and commercial attributes:

`customer_id`, age, annual income, region, city, preferred category, loyalty tier, and acquisition channel.

A product record contains product attributes:

`product_id`, category, product family, price, and margin.

A purchase connects a customer to a product and records quantity, transaction value, date, and sales channel. This transaction layer is especially important for behavioral segmentation because behavior must be inferred from observed activity rather than assumed from demographic characteristics.

The resulting analytical structure can be viewed as:

Customer attributes → Customer segmentation

Product attributes → Product segmentation

Location attributes → Geographic segmentation

Transactions over time → Behavioral segmentation

These dimensions can then be crossed for analysis without collapsing their meanings. For example, revenue can be compared across customer segments and product categories while preserving the fact that the first describes customers and the second describes products.

## Customer Segmentation

Customer segmentation in the Python, JavaScript, C++, and Java implementations uses age and income thresholds to create distinct customer groups.

The example identifies young higher-income customers, established higher-income customers, and value-conscious customers. The thresholds are calculated from the supplied dataset rather than hard-coded around a single arbitrary income value.

This approach demonstrates an important distinction between a segmentation rule and a customer attribute. Age and income are input variables. The segment is the analytical classification derived from those variables.

The model also retains loyalty tier, acquisition channel, and preferred category because those attributes can support more detailed customer profiles. They are not automatically treated as behavioral variables.

Customer segments can overlap when business rules permit it. For example, a customer may satisfy a demographic segment while also belonging to a geographic segment and a behavioral segment. A production system should explicitly decide whether its segment definitions are mutually exclusive or intentionally overlapping.

## Product Segmentation

Product segmentation uses the product catalog rather than customer records.

The implementations classify products using price and margin. Products above the portfolio median price are treated as premium products, while products with margins of at least 30 percent are treated as high-margin products.

These classifications answer product-oriented questions such as:

- Which products occupy the premium price range?
- Which products provide stronger unit economics?
- Which categories generate the largest revenue?
- Which products combine premium positioning with attractive margins?

Product segmentation is therefore not a disguised form of customer segmentation. The same customer may purchase products belonging to several product segments.

The SQL implementation preserves this distinction by keeping product attributes in the `products` table and transaction observations in `purchases`.

## Geographic Segmentation

Geographic segmentation uses actual location fields:

`country`, `region`, `city`, and postal code.

The SQL model stores geographic information separately in `geographic_locations`. This prevents location from becoming an unstructured attribute embedded inside unrelated transaction records.

The geographic queries aggregate customer counts and average income by region and city. They also connect geographic markets to premium-product revenue.

This creates a useful analytical relationship without redefining geography as purchasing behavior. A region remains a geographic segment even when the business later compares its purchasing patterns with another region.

## Behavioral Segmentation

Behavioral segmentation is derived from observed transactions.

The central example uses three RFM-style measures:

| Measure | Meaning in this project |
| --- | --- |
| Recency | Number of days since the customer's latest purchase |
| Frequency | Number of recorded purchase transactions |
| Monetary | Total transaction value |

A customer with high frequency and high monetary value can enter the `loyal_high_value` segment. A recently active customer with lower frequency can enter `recent_low_frequency`. A customer whose most recent transaction is sufficiently old can enter `at_risk`.

These rules are intentionally separate from customer demographics.

A high-income customer is not automatically high-value behaviorally. Likewise, a young customer is not automatically a recent customer. Behavioral classification requires evidence from activity.

The JavaScript implementation extends this idea through an event-driven purchase model. When a new purchase event arrives, the transaction is validated, stored, and behavioral segmentation can be recalculated. This reflects the fact that behavioral segments can change as new activity occurs.

## Python Implementation

The Python program provides the most complete analytical model.

`Customer`, `Product`, and `Purchase` dataclasses establish explicit domain structures. The `SegmentationEngine` validates relationships between customers, products, and purchases before performing segmentation.

Customer segmentation operates on demographic and economic attributes. Product segmentation operates on product economics. Geographic segmentation groups customers by region. Behavioral segmentation computes recency, frequency, and monetary values from transactions.

The Python implementation also creates cross-dimension customer profiles. A profile can show a customer's customer segments, geographic segments, preferred category, purchased categories, and behavioral segments without pretending that these categories represent the same kind of information.

The validation logic rejects invalid ages, negative income, invalid product pricing, unknown customer references, unknown product references, non-positive quantities, and negative transaction prices.

A cosine-similarity function provides a separate numerical mechanism for comparing normalized behavioral profiles. It checks vector dimensionality and handles zero vectors rather than producing an undefined division result.

## JavaScript Implementation

The JavaScript program emphasizes dynamic and event-driven behavior.

`SegmentationService` stores customers and products in `Map` objects. This provides explicit identifier-based lookup and makes validation of transaction references straightforward.

Behavioral metrics are recalculated from the current purchase collection. The service can also accept a new purchase after validating the customer, product, quantity, and value.

`PurchaseEventBus` demonstrates an event-driven workflow. A `purchase.completed` event invokes a listener that adds the purchase and refreshes behavioral segments. This is a useful model for systems where customer behavior changes continuously as events arrive.

JavaScript-specific error handling is demonstrated through exceptions around invalid transactions. The implementation also uses `Map`, `Object.fromEntries`, array transformations, filtering, aggregation, and event listeners where those mechanisms directly support segmentation.

The program does not simply translate the Python class structure. Its primary emphasis is dynamic behavioral updates and event processing.

## C++ Case Study

The C++ program models a high-performance segmentation engine suitable for a service that needs explicit validation and efficient in-memory lookups.

Customers and products are indexed through `std::unordered_map`. Segment memberships use `std::set`, providing deterministic ordered output and preventing duplicate membership identifiers.

The case study separates:

- customer attributes,
- product attributes,
- geographic information,
- purchase events,
- behavioral metrics.

The behavioral engine accumulates transaction frequency, monetary value, and minimum recency for each customer. Median thresholds are calculated from the observed population.

The implementation also demonstrates defensive state validation. Unknown customers and products are rejected before transactions enter the behavioral dataset. Negative amounts, future-oriented recency values, invalid ages, and invalid margins are rejected.

The use of unordered maps gives expected constant-time identifier lookup, while sorting inside the median calculation produces `O(n log n)` threshold computation. Segment membership then requires a pass over the relevant population.

This design is useful when segmentation is treated as an analytical service rather than a simple collection of isolated calculations.

## Java Enterprise Model

The Java program emphasizes explicit domain types and enterprise-style separation of responsibilities.

Java records represent immutable domain objects for customers, products, purchases, segments, and behavioral metrics. This reduces accidental mutation of core business data.

`SegmentDimension` explicitly identifies whether a segment belongs to the customer, product, geographic, or behavioral dimension. This prevents segment categories from becoming untyped strings throughout the application.

The `SegmentRule` interface represents customer-classification logic as an explicit abstraction. Customer segmentation rules can therefore be expressed as predicates over customer and contextual data rather than being embedded entirely inside output statements.

`RepositoryGovernanceService` acts as the domain service responsible for registration, transaction validation, segmentation, and aggregation. Although the service name reflects a broader enterprise-style application context, its actual behavior remains focused on segmentation data and rules.

Java Streams are used where they naturally express filtering, mapping, grouping, and aggregation. Exceptions protect domain invariants such as valid customer ages, non-negative income, unique identifiers, valid product margins, and references to existing entities.

## SQL Data Model

The PostgreSQL implementation provides the strongest relational representation of the domain.

The `customers` table stores customer attributes. The `products` table stores product characteristics. The `geographic_locations` table stores physical location information. The `purchases` table records the transaction events needed for behavioral analysis.

Foreign keys ensure that purchases cannot reference nonexistent customers or products.

Check constraints enforce rules at the database layer:

- customer age must be at least 18;
- annual income cannot be negative;
- product prices cannot be negative;
- product margin must remain between 0 and 1;
- purchase quantities must be positive;
- purchase unit prices cannot be negative.

Indexes support common access patterns such as finding a customer's recent transactions, filtering purchases by product, and grouping customers by geographic region.

The SQL uses PostgreSQL's `percentile_cont` to calculate median income, price, frequency, and monetary value. This avoids relying on an arbitrary hard-coded threshold.

The behavioral query calculates recency using a fixed reference date of `2026-10-17`. Fixing the reference date makes the example reproducible while retaining the same logic that a production system would apply against a current business date.

## Cross-Dimension Analysis

Segmentation becomes more useful when dimensions can be combined without losing their individual meanings.

For example, a query can calculate revenue by customer segment and product category:

`customer segment → product category → revenue`

This does not make product category a customer attribute. It creates a cross-dimensional analytical view.

Similarly:

`geographic region → premium product revenue`

connects geography with product performance while preserving geography as the location dimension and premium status as the product dimension.

A behavioral analysis can identify customers with purchases across multiple categories or sales channels. That result remains behavioral because the evidence comes from observed transactions.

This distinction is essential when designing analytical data models. A segment label should describe the rule that generated it.

## Edge Cases and Failure Conditions

Customers without transactions have no observed purchasing history. A behavioral implementation must not silently treat missing history as the same thing as a normal low-frequency customer. The Python implementation represents this with infinite recency and zero frequency and monetary value.

A customer can belong to more than one analytical dimension at the same time. This is expected because customer, product, geographic, and behavioral segments answer different questions.

A segmentation rule can also produce overlapping memberships within a dimension unless exclusivity is explicitly enforced. Production systems should define whether a customer is allowed to belong to multiple customer segments.

Small populations can make median-based thresholds unstable. A segment definition derived from a few records may change significantly when one record is added.

Missing or inaccurate transaction data can distort behavioral segmentation. Recency, frequency, and monetary values depend directly on transaction completeness.

A purchase with an unknown customer or product should be rejected rather than silently excluded. The SQL foreign keys and application-level validation demonstrate two layers of protection.

## Common Modeling Errors

Treating income as behavior is a category error. Income describes the customer; purchase frequency describes observed activity.

Treating premium products as premium customers is also incorrect. Product price belongs to the product dimension, while customer value must be established through customer-level attributes or observed customer behavior.

Using geography as a substitute for customer demographics can hide important variation inside a region. Geographic segmentation should describe location first.

Assigning a customer to an `at_risk` segment solely because the customer has low income would mix customer segmentation with behavioral segmentation. Risk in this project is derived from purchase recency.

Hard-coding a threshold such as `income > 100000` can be valid for a specific business policy, but it should not be presented as an objective market boundary. The example uses population medians to demonstrate data-derived thresholds.

## Performance Considerations

Customer and product identifiers are indexed through dictionaries or maps in the Python, JavaScript, C++, and Java implementations.

The SQL implementation uses indexes on transaction customer/date, product identifiers, geographic location, and product category.

Median calculation requires sorting or an equivalent order-statistics operation. For a small analytical dataset this is straightforward. Large production systems may calculate segmentation thresholds through database analytics, distributed processing, pre-aggregated tables, or scheduled feature pipelines.

Behavioral metrics can also be precomputed rather than recalculated from every historical transaction for every request. A production implementation may maintain customer-level aggregates such as lifetime value, purchase count, latest purchase date, category count, and channel count.

The appropriate optimization depends on whether segmentation is performed interactively, in scheduled batches, or in response to real-time customer events.

## Security and Data Governance

Customer segmentation frequently uses sensitive commercial information such as income, purchase history, location, and transaction value. Access should therefore follow least-privilege principles.

Segmentation outputs should not expose unnecessary raw customer data to users who only need aggregated results.

The SQL schema separates identifiers and analytical attributes into structured tables, which supports controlled access policies. Production systems should also audit changes to segmentation rules because changing a threshold can change which customers receive an offer, classification, or business treatment.

Behavioral data should have clear retention and governance rules. Incorrect transaction records can create incorrect classifications, so data validation is part of segmentation quality rather than a separate concern.

## Practical Interpretation

Customer segmentation answers **who the customer is**.

Product segmentation answers **what the business is selling and how products differ**.

Geographic segmentation answers **where the market is located**.

Behavioral segmentation answers **what customers have actually done**.

A robust analytical system keeps these dimensions distinct and then combines them deliberately. The implementations demonstrate this principle through different programming models, domain structures, event processing, validation mechanisms, and relational queries rather than treating segmentation as a single classification formula.
