# CASE Statements: Creating Business Logic Using SQL

## Introduction

The SQL `CASE` expression provides conditional business logic inside a query. It evaluates conditions in order and returns the result associated with the first matching branch. This makes it useful for transforming stored values into business classifications, calculating derived amounts, mapping operational states, and performing conditional aggregation.

This learning artifact uses a subscription-commerce domain. Customers have account status and lifetime value, while orders have payment state, order state, monetary values, and a customer relationship.

The central distinction is between **source facts** and **derived business meaning**. A database may store `lifetime_value = 62000`, but an application or report may need the business classification `GOLD`. `CASE` can derive that classification without modifying the underlying customer record.

The implementations deliberately approach the subject from different technical perspectives:

- Python models and tests business rules outside the database.
- JavaScript models an event-driven order-processing workflow.
- C++ presents a typed decision engine for deterministic business-rule evaluation.
- Java models an enterprise-oriented service with explicit domain types and validation.
- PostgreSQL implements the actual relational workflow, conditional expressions, aggregation, constraints, indexes, views, and transaction behavior.

## Core CASE Mechanism

A searched `CASE` expression evaluates Boolean conditions:

`CASE WHEN condition THEN result WHEN another_condition THEN another_result ELSE fallback END`

The conditions are evaluated from top to bottom. Once a `WHEN` condition is true, its corresponding result is returned and later branches are not selected.

A simple `CASE` compares one expression against several values:

`CASE payment_status WHEN 'paid' THEN 'SETTLED' WHEN 'pending' THEN 'AWAITING PAYMENT' ELSE 'UNKNOWN' END`

A searched `CASE` is preferable when the rules involve ranges or multiple predicates:

`CASE WHEN lifetime_value >= 100000 THEN 'PLATINUM' WHEN lifetime_value >= 50000 THEN 'GOLD' ELSE 'STANDARD' END`

The distinction matters because the two forms solve different classification problems. Exact status mapping is naturally represented by simple `CASE`, while threshold-based or compound business rules are naturally represented by searched `CASE`.

## Condition Ordering

Condition ordering is part of the business rule.

The customer classification used throughout the implementations gives a suspended account priority over monetary thresholds:

`WHEN account_status = 'suspended' THEN 'RESTRICTED'`

appears before:

`WHEN lifetime_value >= 100000 THEN 'PLATINUM'`

A suspended customer with a lifetime value of 200,000 therefore becomes `RESTRICTED`, not `PLATINUM`.

Reversing those branches would silently change the meaning of the rule. This is one of the most important practical characteristics of `CASE`: broad conditions placed before exception conditions can capture rows that were intended to be handled by later branches.

Threshold rules also require descending order when higher thresholds represent more specific categories. A customer worth 125,000 should match the 100,000 threshold before the 50,000 and 10,000 thresholds.

## ELSE and Unhandled Values

`ELSE` provides a fallback result when no `WHEN` condition matches.

For status translation, the SQL implementation uses:

`ELSE 'UNKNOWN PAYMENT STATE'`

This prevents an unrecognized value from silently producing a null classification.

An explicit `ELSE` is useful when a business rule must define behavior for data outside the expected domain. It is especially important when source data may originate from external systems, historical records, migrations, or incomplete validation.

An `ELSE` branch does not replace database constraints. The SQL schema still restricts payment states through a `CHECK` constraint. The `CASE` expression is responsible for deriving meaning from valid stored states, while the constraint prevents invalid states from being stored.

## NULL Behavior

SQL `NULL` represents an unknown or missing value. Comparisons involving `NULL` do not evaluate to ordinary true or false values.

For example:

`lifetime_value >= 50000`

is not true when `lifetime_value` is `NULL`. The result is `UNKNOWN`.

Consequently, a searched `CASE` can reach its `ELSE` branch when a comparison involving a nullable value cannot evaluate to true.

When missing data has its own business meaning, test it explicitly:

`WHEN lifetime_value IS NULL THEN 'MISSING VALUE'`

This is different from treating zero as missing. A numeric value of `0` is known and can legitimately be compared against thresholds.

The schema in the SQL implementation makes `lifetime_value` `NOT NULL`, so the production data model does not permit that particular missing state. The separate query demonstrates how the expression would behave when nullable data exists.

## CASE for Customer Segmentation

The customer segmentation rule is:

- Suspended accounts become `RESTRICTED`.
- Active customers with lifetime value of at least 100,000 become `PLATINUM`.
- Values from 50,000 through 99,999.99 become `GOLD`.
- Values from 10,000 through 49,999.99 become `SILVER`.
- Remaining customers become `STANDARD`.

The SQL expression derives this value from stored columns rather than storing another redundant customer attribute.

This approach is useful for reporting when the classification is entirely determined by current source data. A view can expose the derived segment so that multiple reports can consume the same expression.

The `customer_business_classification` view in the SQL implementation demonstrates this pattern.

## CASE for Payment Status

Payment status is an example of exact-value mapping.

The source value:

`paid`

becomes:

`SETTLED`

The source value:

`pending`

becomes:

`AWAITING PAYMENT`

The source value:

`failed`

becomes:

`PAYMENT FAILED`

The source value:

`refunded`

becomes:

`REFUNDED`

This is a strong use case for simple `CASE` because one column is compared with a controlled set of values.

The JavaScript implementation uses a JavaScript `switch` for the same conceptual mapping, while the Java implementation uses an enum and Java `switch` expression. Those implementations demonstrate language-level equivalents, but the SQL `CASE` remains useful when the mapping must happen during database retrieval.

## CASE for Monetary Business Rules

The order discount rule demonstrates why condition ordering and multiple predicates matter.

An unpaid order receives no discount. A suspended customer also receives no discount.

For eligible orders, the rules then evaluate customer value and order value:

`PLATINUM` customers with an order total of at least 5,000 receive 15%.

Customers with lifetime value of at least 50,000 receive 10%.

Orders of at least 10,000 receive 8%.

Orders of at least 5,000 receive 5%.

All other eligible orders receive no discount.

The discount is calculated with `NUMERIC` values in PostgreSQL. This is preferable for monetary data because exact decimal arithmetic is required for reliable financial calculations.

The Python implementation uses `Decimal`, and the Java implementation uses `BigDecimal`, providing language-level counterparts to the database's exact numeric representation.

## CASE and Conditional Aggregation

`CASE` becomes particularly powerful when combined with aggregate functions.

The SQL script uses:

`SUM(CASE WHEN payment_status = 'paid' THEN subtotal + shipping_amount ELSE 0 END)`

to calculate the gross value of paid orders.

It also uses:

`COUNT(CASE WHEN payment_status = 'failed' THEN 1 END)`

to count failed orders.

This technique allows a single query to calculate several conditional metrics from the same dataset.

Conditional aggregation is different from ordinary row classification. A normal `CASE` produces a value for each row. When that expression is placed inside `SUM`, `COUNT`, or another aggregate, the derived values become inputs to a group-level calculation.

This pattern is useful for operational dashboards, financial reporting, customer analytics, and compliance reporting.

## CASE and Data Quality

A `CASE` expression can expose suspicious combinations without modifying the underlying records.

The SQL implementation classifies combinations such as:

`payment_status = 'paid'` with `order_status = 'cancelled'`

as:

`REVIEW: PAID AND CANCELLED`

It also identifies failed payments that remain associated with confirmed orders.

This is different from a `CHECK` constraint. A `CHECK` constraint prevents an invalid row from being stored when its rule can be expressed at the row level. A reporting-oriented `CASE` can instead expose conditions for operational investigation.

The appropriate mechanism depends on whether the rule is a storage invariant or a derived operational classification.

## Relational Integrity Versus CASE

`CASE` is an expression, not a general integrity mechanism.

The PostgreSQL schema uses a primary key on `customers.customer_id`. It uses a foreign key from `orders.customer_id` to `customers.customer_id`. It also uses `CHECK` constraints for monetary values and controlled status values.

These mechanisms solve different problems:

| Mechanism | Purpose |
| --- | --- |
| `CASE` | Derives a business value from existing row data |
| `PRIMARY KEY` | Identifies each row uniquely |
| `FOREIGN KEY` | Protects relationships between tables |
| `UNIQUE` | Prevents duplicate values where uniqueness is required |
| `CHECK` | Enforces valid row-level conditions |
| `INDEX` | Improves access paths for suitable queries |
| `VIEW` | Provides a reusable query representation |
| `TRANSACTION` | Groups database operations into an atomic unit |

A common design error is trying to use `CASE` as though it were a constraint. A query can classify an invalid row, but classification does not automatically prevent the row from being stored.

## Python Implementation

The Python program models customers and orders using immutable dataclasses.

`classify_customer()` represents a searched `CASE` rule. Its ordering makes the suspended-account exception take precedence over lifetime-value thresholds.

`order_payment_label()` represents simple value mapping.

`shipping_priority()` combines order status, payment state, and monetary thresholds. This demonstrates that business rules often depend on several columns rather than one field.

`discount_rate()` demonstrates rule precedence, compound conditions, and an explicit zero result for ineligible orders.

The script also includes rule validation. Expected classifications are compared against actual results so that changes to business logic can be detected before deployment.

Python's `Decimal` is used for monetary calculations instead of binary floating-point arithmetic.

The script also explains SQL `NULL` behavior because a direct translation between Python conditional logic and SQL conditions can be misleading when database nullability is involved.

## JavaScript Implementation

The JavaScript implementation represents the same business domain from an event-driven perspective.

`classifyCustomer()` models threshold-based classification. `paymentLabel()` uses JavaScript's `switch` mechanism for exact status mapping.

The `OrderProcessor` class adds an event-oriented layer. After an order is classified, listeners can react to outcomes such as payment requirements or priority shipments.

This illustrates an important architectural distinction. SQL `CASE` is normally evaluated while producing relational query results. JavaScript event handling can use the resulting business classification to initiate application behavior.

The implementation also generates a PostgreSQL `CASE` expression as a string. This shows the boundary between application logic and database logic without requiring an external database package.

Input validation prevents negative monetary values and detects orders referencing unknown customers.

## C++ Case Study

The C++ program presents a typed order decision engine.

The domain uses enumerations for account, payment, and order states. This prevents arbitrary status strings from being used throughout the decision engine.

`customerSegment()` models a searched `CASE` through ordered conditions. `shippingPriority()` combines order state, payment state, and monetary thresholds.

`GovernanceEngine` separates customer lookup from business-rule evaluation. An order referencing an unknown customer causes an exception instead of producing an apparently valid classification.

The implementation uses `std::vector` for customer storage and an algorithm-based lookup. For a production system with a large in-memory customer population, an indexed structure such as `std::unordered_map` would normally provide faster repeated lookup.

The C++ program also demonstrates an important design boundary: the application can calculate derived business decisions, but database constraints remain necessary when persistent relational integrity must be guaranteed.

## Java Implementation

The Java program models an enterprise-oriented service using records, enums, collections, and `BigDecimal`.

`Customer` and `Order` are immutable records with constructor validation. This keeps invalid domain objects from entering the decision service.

`BusinessRuleService` contains explicit business operations:

- `classifyCustomer()` implements ordered threshold logic.
- `paymentLabel()` maps an enum to an operational label.
- `shipmentPriority()` derives fulfillment priority from several order conditions.
- `discountRate()` implements pricing policy.
- `evaluate()` combines the rules into a complete decision.

The use of `BigDecimal` is intentional. Enterprise financial logic should avoid binary floating-point arithmetic for exact monetary calculations.

The customer index uses an unmodifiable map created from the customer collection. This provides efficient identifier-based access while preventing accidental modification of the indexed collection.

The Java implementation makes the domain rules explicit rather than hiding all behavior inside print statements or generic condition examples.

## SQL Data Model

The PostgreSQL schema contains two primary entities:

`customers` stores customer identity, country, lifetime value, and account state.

`orders` stores the customer relationship, monetary values, payment state, order state, and creation timestamp.

The foreign key from `orders.customer_id` to `customers.customer_id` prevents an order from referencing a nonexistent customer.

Monetary columns use `NUMERIC(14, 2)` and include non-negative `CHECK` constraints.

Controlled status values are also constrained so that the `CASE` expressions operate against a defined domain.

Indexes are provided for customer-based order lookup, payment-status filtering, and account-status filtering. Indexes should be introduced for actual access patterns rather than added indiscriminately.

## Views and Reusable Business Logic

The `customer_business_classification` view demonstrates how a `CASE` expression can become a reusable database-level reporting interface.

The underlying customer table retains source facts. The view exposes the derived segment.

This separation is useful when a classification is deterministic and commonly consumed. It also prevents multiple reporting queries from independently implementing slightly different versions of the same rule.

A view does not automatically make a business rule immutable. If the underlying source data changes, the derived classification can change as well.

## Transactions and CASE

The SQL script includes a transaction containing a query that derives fulfillment states.

`BEGIN` and `COMMIT` control transaction boundaries. `CASE` controls the classification of each row.

These are separate responsibilities.

A transaction provides atomicity and consistency for a sequence of database operations. `CASE` determines which value an expression returns for a row.

Confusing these mechanisms leads to poor database design. A `CASE` expression cannot make a multi-statement workflow atomic.

## Common Failure Modes

### Incorrect branch ordering

Putting a broad threshold before a more specific exception can produce the wrong classification. A suspended high-value account is the central example.

### Missing ELSE

A classification without a deliberate fallback can produce `NULL` when no condition matches. Whether that is correct depends on the business rule.

### Ignoring NULL

`NULL` is not zero, an empty string, or false. Comparisons against `NULL` require explicit null-aware conditions such as `IS NULL` or `IS NOT NULL`.

### Overlapping thresholds

Thresholds should be designed so their intended ranges are clear. If multiple branches can match, the order determines the result.

### Using CASE as a constraint

A query expression cannot replace a foreign key, uniqueness rule, or storage constraint.

### Repeating business rules

If ten reports independently implement the same customer segmentation, their rules can drift. A shared view, carefully designed query layer, or centralized business-rule implementation can reduce that risk.

### Using floating point for money

Binary floating-point representations can produce unexpected decimal results. PostgreSQL `NUMERIC`, Python `Decimal`, and Java `BigDecimal` are better choices for exact monetary calculations.

## Performance Considerations

A `CASE` expression itself does not automatically require a table scan, nor does it automatically use an index. Query performance depends on the complete query plan.

A `CASE` used only in the `SELECT` list may classify rows after PostgreSQL has already selected them.

A condition placed in a `WHERE` clause has different optimization implications. If a classification is repeatedly queried, a generated column, expression index, materialized view, or another design may be appropriate depending on the workload.

Conditional aggregation can process many rows efficiently as part of a single grouped query, but expensive expressions over very large datasets still require query-plan analysis.

Indexes should support actual filtering, joining, ordering, and grouping patterns rather than being created merely because a column appears inside a `CASE`.

## Security and Production Considerations

Business logic embedded in SQL must be treated as production logic.

If a `CASE` determines financial discounts, customer access levels, eligibility, or compliance states, changing it can materially affect application behavior.

SQL statements should use parameters rather than string concatenation for external values. The examples use fixed SQL literals and therefore do not require dynamic SQL.

When dynamic SQL is required, conditional business rules should not be constructed from untrusted strings.

Authorization should not be inferred solely from a display classification. A label such as `PLATINUM` is descriptive; access control requires explicit authorization rules.

For financial calculations, rounding rules should be deliberate and consistent across the database and application layers.

## Practical Design Boundary

A useful architectural separation is:

**Stored facts → CASE-derived meaning → constraints and transactions → application behavior**

Stored facts include customer status, lifetime value, payment state, and order amount.

`CASE` converts those facts into business classifications such as `GOLD`, `RESTRICTED`, `SETTLED`, `HOLD`, or `URGENT`.

Constraints protect structural validity.

Transactions protect multi-step database operations.

Application services can consume the resulting classifications to trigger workflows.

This separation keeps conditional expressions focused on deriving values rather than turning them into a substitute for every database and application mechanism.

## Technical Relationship Across the Five Implementations

The six artifacts represent the same subject from complementary perspectives.

The Python implementation emphasizes testable rule evaluation and exact decimal arithmetic.

The JavaScript implementation emphasizes event-driven handling of decisions after classification.

The C++ implementation emphasizes typed domain modeling, validation, and a deterministic decision engine.

The Java implementation emphasizes immutable enterprise domain objects, explicit policy methods, enums, and precise monetary arithmetic.

The SQL implementation places the business rules directly alongside relational data, allowing classification, aggregation, views, constraints, and transactional queries to operate close to the data.

The central SQL concept remains unchanged across these perspectives: `CASE` is a conditional expression that produces a value. Its effectiveness comes from precise conditions, deliberate ordering, explicit handling of unmatched cases, correct treatment of `NULL`, and a clear separation between derived business logic and database integrity mechanisms.
