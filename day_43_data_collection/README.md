# Data Collection: Internal, External, Transactional, and Behavioral Data

## Purpose and scope

Data collection is the controlled process of obtaining information from operational systems, external providers, business transactions, and observed interactions. Reliable collection requires more than receiving a payload. A production pipeline must establish where the information originated, what it represents, when it was observed, why it is collected, whether the collection is authorized, and whether its structure and values satisfy the applicable rules.

This project implements a retail data collection scenario across four distinct categories:

| Category | Typical source | Primary purpose | Representative record |
|---|---|---|---|
| Internal | ERP, inventory management, operational databases | Reconcile organizational operations | Warehouse inventory snapshot |
| External | Supplier feeds, licensed datasets, partner APIs | Compare information supplied outside the organization | Supplier price quote |
| Transactional | Order management, billing, payment systems | Record a business event and its operational outcome | Paid or cancelled customer order |
| Behavioral | Website analytics, application events, interaction logs | Understand observed user activity | Product view or checkout event |

The categories describe the origin and meaning of data, not four interchangeable formats. A supplier quote does not become a transaction merely because it contains a price. A product view is an observed interaction, not evidence that a purchase occurred. An inventory snapshot is an operational measurement that can change over time.

## Collection architecture

The implementations use a common conceptual pipeline:

**Source registration → collection authorization → validation → normalization → deduplication → persistence → quality assessment → analysis**

Source registration defines the expected category and collection purpose. Authorization determines whether the requested collection is permitted. Validation checks source-specific rules. Normalization makes timestamps, identifiers, and field representations consistent. Deduplication prevents repeated delivery from creating duplicate records. Persistence retains accepted records and their provenance. Analysis then applies category-appropriate measures.

A useful logical representation of a collected record is:

- **Source identity:** The system or provider that supplied the record.
- **External record identity:** The identifier assigned by the originating system.
- **Category:** Internal, external, transactional, or behavioral.
- **Observation time:** When the source says the event or measurement occurred.
- **Collection time:** When the receiving pipeline obtained the record.
- **Purpose and collection basis:** Why the record is collected and the documented basis applicable to that collection.
- **Schema version:** The structure expected by the relevant collector.
- **Payload:** The category-specific attributes.
- **Quality outcome:** Acceptance, rejection, duplication, or a recorded validation issue.

Observation time and collection time should remain distinct. A supplier feed can describe a quote created earlier but received later. An inventory snapshot can be delayed by a network interruption. Treating collection time as the event time would distort reporting and hide delays in the pipeline.

## Internal data collection

Internal data originates in systems operated by the organization. Examples include inventory balances, warehouse status, production counts, service tickets, and operational performance measurements.

The Python implementation collects an ERP inventory snapshot containing a warehouse code, stock-keeping unit, available units, and reserved units. Its quality assessment checks that quantities are non-negative integers and that reserved units do not exceed available units. These rules describe inventory semantics rather than general JSON validity.

The C++ and Java implementations apply comparable inventory-specific validation within a broader ingestion architecture. The SQL implementation stores inventory in a typed `inventory_snapshots` table. Database constraints reject negative quantities and inconsistent reservations, protecting the data even if a client bypasses application-level validation.

Internal data often has strong operational ownership, but it is not automatically accurate. Incorrect synchronization, stale caches, duplicate feeds, inconsistent unit definitions, and incomplete updates can still produce invalid records. Operational systems should expose the age of each snapshot and distinguish current measurements from historical observations.

## External data collection

External data arrives from suppliers, partners, public datasets, licensed providers, or third-party APIs. Its reliability depends on the provider, contract, collection method, schema, update frequency, and any transformations applied before ingestion.

The examples collect a supplier quote for a product. The record retains the supplier name, product identifier, unit price, currency, and supplier revision. Keeping the revision is important because two feeds can report different prices without either record being a duplicate.

The Python implementation validates monetary amounts with `Decimal`, avoiding binary floating-point arithmetic for prices. The JavaScript implementation represents money as integer minor units using `BigInt`. C++ uses integer minor units, while Java uses `BigDecimal`. PostgreSQL stores monetary amounts in `NUMERIC` columns.

External data needs explicit freshness and provenance controls. A valid price can still be unsuitable for a current purchasing decision if the supplier feed is old. A currency value must be retained with its amount because `64500.00 INR` and `64500.00 USD` are not equivalent quantities. The examples validate supported currencies but do not perform foreign-exchange conversion.

External data may also contain unexpected fields, malformed values, duplicate deliveries, incompatible schema revisions, or values outside contractual limits. A production adapter should record the provider revision, fetch time, source endpoint or feed identifier, and validation outcome without exposing credentials or other secrets in logs.

## Transactional data collection

Transactional data represents business events with operational or financial consequences. Examples include order placement, payment capture, refund processing, shipment confirmation, and cancellation.

The examples model retail orders with an order identifier, customer reference, amount, currency, and status. The SQL implementation stores order headers in `sales_orders` and item-level details in `sales_order_items`. A foreign key connects each order to its generic collection record, and a separate unique constraint prevents the same business order identifier from being inserted twice.

Transaction status affects interpretation. A cancelled order must not be counted as completed revenue. A pending payment is not equivalent to a successful payment. A refund requires explicit treatment rather than silently rewriting the historical amount. The reporting logic therefore calculates paid revenue only from records marked `paid` and denominated in INR.

Transactional data also requires reconciliation between systems. An order management system can report an order as paid while a payment provider reports a failed capture. A production pipeline should retain source identifiers, event versions, timestamps, and reconciliation status so discrepancies can be investigated. Event delivery should be idempotent, meaning that replaying the same source event does not create a second business transaction.

Amounts require precise representation. Floating-point arithmetic can introduce rounding errors, especially when many transactions are aggregated. Integer minor units or decimal arithmetic are more suitable for financial values. Currency-specific rules, tax treatment, exchange-rate timing, refunds, and settlement differences must be handled explicitly in a real financial model.

## Behavioral data collection

Behavioral data records observed interactions rather than completed business transactions. Examples include page views, product views, searches, cart additions, and checkout initiation.

The JavaScript implementation defines a dedicated behavioral source adapter with an explicit event vocabulary. It validates event types and requires relative application paths rather than arbitrary URLs. The Python implementation applies similar event and path checks. The Java and C++ programs require a recognized event type and a valid relative path. The SQL implementation stores events in `behavioral_events` with indexes supporting event-type and page-level analysis.

A behavioral event may indicate intent but does not prove a transaction occurred. A visitor can view a product without adding it to a cart. A cart addition can occur without checkout. A checkout-start event does not establish successful payment. Funnel analysis must therefore distinguish interaction stages from confirmed business outcomes.

Behavioral collection also has specific privacy and data-minimization concerns. Identifiers can link multiple events to the same visitor, which can create a detailed activity history. The examples use a purpose-specific permission registry and reject events when permission is absent. This is a simplified teaching model, not a complete consent-management or legal-compliance system.

A production implementation should define the permitted purpose, consent evidence where applicable, retention period, identity handling, deletion and withdrawal behavior, access controls, and treatment of sensitive event attributes. It should avoid collecting unnecessary query parameters, authentication tokens, session secrets, or personal information in URLs.

## Python implementation

The Python script builds a reusable collection service around `CollectionContext`, `DataRecord`, `ConsentRegistry`, and `DataCollector`.

`CollectionContext` separates source metadata from the payload. `DataRecord` stores the normalized record and preserves its provenance. The collector derives a stable SHA-256 fingerprint from the source and external record identifier. This fingerprint supports deterministic deduplication without placing the raw external identifier in the generated record key.

The fingerprint is an identifier, not a guarantee of confidentiality. Predictable inputs can still be guessed, and hashing a low-entropy identifier does not replace encryption or access control. The source identity must also be trustworthy because a source-and-identifier pair is only unique within the chosen identity scope.

`collect_safely` demonstrates batch ingestion in which an invalid record can be rejected without terminating the entire batch. Rejected records are retained as diagnostic metadata. The implementation includes category-specific quality checks, separate transactional and behavioral summaries, and JSON and CSV export.

The use of `Decimal` for money, timezone-aware timestamps, structured record metadata, and source-specific validation illustrates how collection concerns can be separated from later analytics. The demonstration exports files inside a temporary directory, so they are intended for the duration of the run rather than permanent storage.

The implementation is an in-memory demonstration. Its dictionary-based storage is not durable, its consent registry is not a legal evidence system, and its record key is not a distributed transaction protocol. A production deployment would need persistent storage, access controls, bounded retention, operational metrics, retry policies, and durable handling of failed records.

## JavaScript implementation

The JavaScript file emphasizes source adapters and asynchronous ingestion. Each `SourceAdapter` has a source name, category, and normalization function. The adapter validates and converts raw input before the collection service persists it.

`DataCollectionService` uses private class fields to restrict access to its internal record map and dead-letter queue. It provides asynchronous ingestion and bounded retry behavior. Only a specifically classified transient source failure is retried. A validation error or consent rejection is not treated as a temporary network problem.

The retry implementation uses exponential backoff. This reduces repeated immediate requests during temporary failures. Production retry policies should also use time limits, jitter, source-specific rate limits, and cancellation behavior.

The collection service deduplicates records using a stable source key. Identical payloads are treated as repeated deliveries, while conflicting payloads require reconciliation. This is important when external systems retry requests after a timeout and cannot tell whether the original operation succeeded.

The `analyzeCollection` function uses `BigInt` for minor-unit arithmetic and separates paid transactional revenue from behavioral event counts. JavaScript's ordinary `Number` type cannot represent every integer exactly at arbitrary magnitudes, so integer monetary arithmetic needs explicit limits and representation rules.

The program uses Node.js built-in modules only. Its simulated transient failure demonstrates retry behavior but does not implement an actual network client, durable queue, or distributed exactly-once delivery guarantee.

## C++ case study

The C++ program models a governance-oriented collection engine for a retail organization.

`CollectionPolicy` declares the permitted source, category, purpose, collection basis, and whether permission is required. `CollectionRecord` carries the source identifier, timestamps, provenance, and category-specific fields. `CollectionEngine` checks that the record matches the registered policy before validating and storing it.

The `ConsentRegistry` provides purpose-specific permission checks. The ingestion engine rejects unauthorized behavioral records, malformed inventory measurements, unsupported currencies, invalid monetary amounts, and records whose observation time occurs after their collection time.

The engine stores accepted records in an `unordered_map`, using a composite source and external identifier as the key. Expected lookup is approximately constant time under ordinary hash-table behavior, although worst-case behavior and memory use depend on the implementation and workload. The audit log records accepted, duplicate, and rejected operations.

The revenue report uses integer minor units and includes only paid INR transactions. It does not infer revenue from product views or cart events. This distinction keeps business transaction outcomes separate from interaction measurements.

The C++ program demonstrates in-memory policy enforcement and validation. Its simplified composite key is suitable for the controlled demonstration but should be replaced or carefully encoded in a production system. The program also does not persist audit events or coordinate concurrent ingestion across multiple service instances.

## Java implementation

The Java program represents collection behavior with explicit domain types: `Category`, `OrderStatus`, `SourcePolicy`, `CollectionRequest`, `CollectedRecord`, and `IngestionOutcome`.

The record types preserve the difference between the incoming request and the accepted collection record. Their attribute maps are defensively copied and wrapped as unmodifiable maps, preventing callers from changing the stored attributes through a retained reference.

`CollectionService` coordinates policy validation, timestamp validation, consent checks, and category-specific validation. `CollectionRepository` handles idempotent insertion and records audit events. Synchronizing the repository insertion method prevents concurrent callers within the same repository instance from inserting two records under the same key.

The repository's duplicate comparison deliberately ignores the generated UUID and collection timestamp. A retry of an identical observation can therefore be recognized as a duplicate even if it arrives at a different time. A changed payload under the same source key is rejected for reconciliation.

`AnalyticsService` uses streams to select paid transactional records and `BigDecimal` to aggregate monetary values. Category counts are calculated separately, allowing operational snapshots, external quotes, orders, and behavioral events to be reported without conflating their meanings.

The repository is in memory, so Java synchronization does not provide coordination between different JVMs or application servers. A production repository would need database uniqueness constraints and transactional writes. The simplified permission registry would also need durable consent evidence, explicit withdrawal semantics, and protection against stale decisions.

## SQL data model

The PostgreSQL script separates common collection metadata from category-specific business attributes.

`collection_sources` registers the expected category, purpose, collection basis, schema version, and consent requirement. `collection_subjects` identifies the subjects relevant to the behavioral example. `collection_permissions` records purpose-specific permission events.

`collection_records` stores the shared provenance fields and a JSONB payload. Its unique constraint on `(source_id, external_record_id)` prevents the same external record from being inserted twice. Timestamp, payload-type, and metadata constraints enforce basic integrity at the database layer.

Typed tables retain attributes that require stronger relational constraints:

- `inventory_snapshots` stores stock quantities and enforces non-negative values and valid reservation totals.
- `supplier_quotes` stores supplier, product, price, currency, and revision information.
- `sales_orders` stores order identity, customer reference, monetary value, currency, and transaction status.
- `sales_order_items` stores order line items with positive quantities and a foreign key to the order.
- `behavioral_events` stores visitor references, recognized event types, and relative page paths.

The `collection_audit` table provides a structure for recording ingestion outcomes. The demonstration does not implement a complete rejection-ingestion procedure; rejected database writes would need to be captured at an application transaction boundary or in a dedicated database function.

The `enforce_source_category` trigger verifies that each generic record matches its registered source category, purpose, collection basis, and enabled state. For sources requiring permission, it checks the latest recorded decision for the declared subject and purpose. The subtype triggers ensure that an inventory row belongs to an internal record, a supplier quote to an external record, an order to a transactional record, and a behavioral event to a behavioral record.

Indexes support category-and-time filtering, source history, JSONB payload inspection, transaction status reporting, behavioral event analysis, and permission lookup. The GIN index is useful for appropriate JSONB queries, although its storage and write costs should be evaluated against actual query patterns.

The views `v_collection_profile`, `v_paid_revenue_by_currency`, `v_behavioral_funnel`, and `v_inventory_availability` provide distinct operational and analytical perspectives. The quality query identifies accepted generic records without their expected typed subtype.

The SQL demonstration uses a schema reset for reproducibility. The script should be run in a disposable database because it drops the existing `data_collection_lab` schema. In a real environment, migrations, role permissions, backups, and carefully controlled schema changes should replace destructive initialization.

## Data quality, provenance, and failure handling

Data quality should be evaluated according to the meaning of a record. A non-empty string is not enough to validate an inventory quantity. A syntactically valid price can still have the wrong currency. A well-formed behavioral event can still have been collected without the required permission. A unique order identifier does not prove that payment settled successfully.

The implementations distinguish several failure classes:

| Failure | Example | Appropriate handling |
|---|---|---|
| Schema failure | An order has no amount | Reject the record and retain a diagnostic reason |
| Domain failure | Reserved inventory exceeds available inventory | Reject the inconsistent measurement |
| Policy failure | Source purpose differs from its registration | Reject until the policy or request is corrected |
| Permission failure | Behavioral collection lacks purpose-specific authorization | Do not collect the event |
| Duplicate delivery | A source resends an identical event | Return the existing record or treat the operation as successful |
| Duplicate conflict | The same source identifier arrives with changed content | Quarantine for reconciliation rather than silently overwrite |
| Transient source failure | A temporary feed transport failure occurs | Retry within a bounded policy, then retain a failure record |
| Stale data | A valid supplier quote is too old for current use | Apply a freshness threshold appropriate to the decision |

Provenance enables the organization to trace a measurement or transaction to its origin. Schema versioning helps identify structural changes. Observation and collection timestamps support freshness calculations and ingestion-delay monitoring. Audit metadata provides evidence of the collection decision without requiring unrestricted logging of the complete payload.

## Performance and operational considerations

Collection volume, source behavior, and query patterns determine the appropriate architecture.

- **Batch ingestion:** Supplier feeds and historical exports can often be validated in batches. Batch size should be bounded to limit memory use and reduce the impact of a malformed input.
- **Event ingestion:** Behavioral events may arrive at high frequency and require partitioning, retention controls, and efficient aggregation.
- **Transactional integrity:** Order headers, order items, and corresponding collection records should be written atomically. A partial write can leave business records that cannot be reconciled with their source metadata.
- **Idempotency:** Source event identifiers and database uniqueness constraints should protect against repeated deliveries. An in-memory map cannot provide cross-process idempotency.
- **Schema evolution:** A new source revision should be validated against a versioned contract before it is allowed into production. Unexpected changes should be observable rather than silently coerced.
- **Backpressure:** A slow destination should not cause unbounded memory growth. Collection systems need bounded queues, rate limits, and clear failure behavior.
- **Observability:** Monitor accepted and rejected records, duplicate rates, source freshness, collection latency, retry counts, and dead-letter volume.
- **Retention:** Retention should reflect the purpose, business requirements, and applicable obligations for each category. Behavioral data often requires stricter minimization than aggregate operational measurements.

## Security and privacy controls

Collection governance begins before persistence. A pipeline should verify the source identity, validate input, authorize the intended purpose, and minimize the attributes it retains.

Credentials must not be embedded in sample payloads, audit messages, source code, or exported records. External requests should use authenticated connections, bounded response sizes, and explicit timeouts. Untrusted strings must be handled safely when inserted into SQL, logs, URLs, or downstream systems.

Behavioral identifiers should not be treated as anonymous merely because they are pseudonymous. Linkable activity can reveal patterns about individuals. Permission records should be scoped to a purpose and interpreted according to the applicable policy, with withdrawal and retention behavior defined explicitly.

Hashing identifiers supports stable key construction but does not by itself anonymize a dataset. Access controls, encryption, minimization, retention limits, and appropriate handling of deletion requests remain necessary.

## Practical interpretation of the four data categories

The same retail operation may use all four categories for a single business question, but each category contributes different evidence.

Internal inventory data describes the stock position recorded by the organization. External supplier data describes the price and terms supplied by an outside provider. Transactional data records what happened to an order or payment. Behavioral data describes interactions that may precede a purchase.

Combining these sources can help explain why a product was unavailable, whether supplier pricing changed, whether an order completed, and where customers stopped in the purchase process. The integration is reliable only when source identity, timestamps, currency, transaction status, collection purpose, and data quality remain explicit.

A robust collection system preserves these distinctions instead of forcing every incoming payload into a single undifferentiated dataset.
