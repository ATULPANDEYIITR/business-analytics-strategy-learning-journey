import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;

/*
 * Enterprise data collection governance model.
 *
 * The system separates source registration, domain validation, permission
 * checks, immutable accepted records, duplicate handling, and reporting.
 * It uses Java 17 standard-library features only.
 */
public class DataCollectionGovernance {

    enum Category {
        INTERNAL,
        EXTERNAL,
        TRANSACTIONAL,
        BEHAVIORAL
    }

    enum OrderStatus {
        PENDING,
        PAID,
        REFUNDED,
        CANCELLED
    }

    record SourcePolicy(
        String sourceName,
        Category category,
        String purpose,
        String lawfulBasis,
        boolean consentRequired
    ) {
        SourcePolicy {
            sourceName = requireText(sourceName, "sourceName");
            Objects.requireNonNull(category, "category");
            purpose = requireText(purpose, "purpose");
            lawfulBasis = requireText(lawfulBasis, "lawfulBasis");
        }
    }

    record CollectionRequest(
        SourcePolicy policy,
        String externalId,
        Instant observedAt,
        Instant collectedAt,
        String purpose,
        String lawfulBasis,
        String subjectId,
        Map<String, String> attributes
    ) {
        CollectionRequest {
            Objects.requireNonNull(policy, "policy");
            externalId = requireText(externalId, "externalId");
            Objects.requireNonNull(observedAt, "observedAt");
            Objects.requireNonNull(collectedAt, "collectedAt");
            purpose = requireText(purpose, "purpose");
            lawfulBasis = requireText(lawfulBasis, "lawfulBasis");
            attributes = Collections.unmodifiableMap(
                new LinkedHashMap<>(attributes)
            );
        }
    }

    record CollectedRecord(
        UUID id,
        String sourceName,
        String externalId,
        Category category,
        Instant observedAt,
        Instant collectedAt,
        String purpose,
        String lawfulBasis,
        Map<String, String> attributes
    ) {
        CollectedRecord {
            Objects.requireNonNull(id, "id");
            Objects.requireNonNull(category, "category");
            attributes = Collections.unmodifiableMap(
                new LinkedHashMap<>(attributes)
            );
        }
    }

    record IngestionOutcome(
        boolean accepted,
        boolean duplicate,
        String message,
        CollectedRecord record
    ) {}

    static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(field + " is required");
        }
        return value.trim();
    }

    static BigDecimal parseMoney(String value) {
        try {
            BigDecimal amount = new BigDecimal(value).setScale(
                2,
                RoundingMode.UNNECESSARY
            );

            if (amount.signum() < 0) {
                throw new IllegalArgumentException(
                    "Amount cannot be negative"
                );
            }

            return amount;
        } catch (NumberFormatException | ArithmeticException exception) {
            throw new IllegalArgumentException(
                "Amount must be a non-negative decimal with at most two places",
                exception
            );
        }
    }

    static final class ConsentRegistry {
        private final Set<String> permissions = new HashSet<>();

        private String key(String subject, String purpose) {
            return requireText(subject, "subject") + "\u001f"
                + requireText(purpose, "purpose");
        }

        public void grant(String subject, String purpose) {
            permissions.add(key(subject, purpose));
        }

        public void revoke(String subject, String purpose) {
            permissions.remove(key(subject, purpose));
        }

        public boolean allows(String subject, String purpose) {
            return permissions.contains(key(subject, purpose));
        }
    }

    static final class CollectionRepository {
        private final Map<String, CollectedRecord> records =
            new LinkedHashMap<>();

        private final List<String> auditEvents = new ArrayList<>();

        private String key(String source, String externalId) {
            return source.toLowerCase() + "\u001f" + externalId;
        }

        public synchronized IngestionOutcome insert(
            CollectedRecord candidate
        ) {
            String recordKey = key(
                candidate.sourceName(),
                candidate.externalId()
            );

            CollectedRecord previous = records.get(recordKey);

            if (previous != null) {
                if (sameContent(previous, candidate)) {
                    auditEvents.add(
                        "Duplicate ignored from " + candidate.sourceName()
                    );
                    return new IngestionOutcome(
                        true,
                        true,
                        "Identical record already accepted",
                        previous
                    );
                }

                auditEvents.add(
                    "Conflicting duplicate from " + candidate.sourceName()
                );

                return new IngestionOutcome(
                    false,
                    false,
                    "Conflicting source record requires reconciliation",
                    null
                );
            }

            records.put(recordKey, candidate);
            auditEvents.add(
                "Accepted " + candidate.category() + " from "
                    + candidate.sourceName()
            );

            return new IngestionOutcome(
                true,
                false,
                "Record accepted",
                candidate
            );
        }

        private boolean sameContent(
            CollectedRecord left,
            CollectedRecord right
        ) {
            return left.category() == right.category()
                && left.observedAt().equals(right.observedAt())
                && left.purpose().equals(right.purpose())
                && left.lawfulBasis().equals(right.lawfulBasis())
                && left.attributes().equals(right.attributes());
        }

        public synchronized List<CollectedRecord> all() {
            return List.copyOf(records.values());
        }

        public synchronized List<String> auditEvents() {
            return List.copyOf(auditEvents);
        }
    }

    static final class CollectionService {
        private final ConsentRegistry consentRegistry;
        private final CollectionRepository repository;

        CollectionService(
            ConsentRegistry consentRegistry,
            CollectionRepository repository
        ) {
            this.consentRegistry = consentRegistry;
            this.repository = repository;
        }

        public IngestionOutcome collect(CollectionRequest request) {
            try {
                validatePolicy(request);
                validateTimestamps(request);

                if (request.policy().consentRequired()) {
                    if (request.subjectId() == null
                        || !consentRegistry.allows(
                            request.subjectId(),
                            request.purpose()
                        )) {
                        throw new IllegalArgumentException(
                            "Purpose-specific permission is absent"
                        );
                    }
                }

                validateAttributes(
                    request.policy().category(),
                    request.attributes()
                );

                CollectedRecord record = new CollectedRecord(
                    UUID.randomUUID(),
                    request.policy().sourceName(),
                    request.externalId(),
                    request.policy().category(),
                    request.observedAt(),
                    request.collectedAt(),
                    request.purpose(),
                    request.lawfulBasis(),
                    request.attributes()
                );

                return repository.insert(record);
            } catch (IllegalArgumentException exception) {
                return new IngestionOutcome(
                    false,
                    false,
                    exception.getMessage(),
                    null
                );
            }
        }

        private void validatePolicy(CollectionRequest request) {
            SourcePolicy policy = request.policy();

            if (!request.purpose().equals(policy.purpose())
                || !request.lawfulBasis().equals(policy.lawfulBasis())) {
                throw new IllegalArgumentException(
                    "Request conflicts with registered source policy"
                );
            }
        }

        private void validateTimestamps(CollectionRequest request) {
            if (request.observedAt().isAfter(request.collectedAt())) {
                throw new IllegalArgumentException(
                    "Observation cannot occur after collection"
                );
            }
        }

        private void validateAttributes(
            Category category,
            Map<String, String> attributes
        ) {
            switch (category) {
                case INTERNAL -> validateInventory(attributes);
                case EXTERNAL -> validateSupplier(attributes);
                case TRANSACTIONAL -> validateOrder(attributes);
                case BEHAVIORAL -> validateBehavior(attributes);
            }
        }

        private void validateInventory(Map<String, String> attributes) {
            int available = parseNonNegativeInteger(
                attributes.get("availableUnits"),
                "availableUnits"
            );
            int reserved = parseNonNegativeInteger(
                attributes.get("reservedUnits"),
                "reservedUnits"
            );

            requireText(attributes.get("warehouse"), "warehouse");
            requireText(attributes.get("sku"), "sku");

            if (reserved > available) {
                throw new IllegalArgumentException(
                    "Reserved units exceed available units"
                );
            }
        }

        private void validateSupplier(Map<String, String> attributes) {
            requireText(attributes.get("supplier"), "supplier");
            requireText(attributes.get("sku"), "sku");

            parseMoney(attributes.get("unitPrice"));

            Set<String> supportedCurrencies = Set.of(
                "INR", "USD", "EUR", "GBP"
            );

            if (!supportedCurrencies.contains(attributes.get("currency"))) {
                throw new IllegalArgumentException(
                    "Unsupported supplier currency"
                );
            }
        }

        private void validateOrder(Map<String, String> attributes) {
            requireText(attributes.get("orderId"), "orderId");
            requireText(attributes.get("customerId"), "customerId");
            requireText(attributes.get("currency"), "currency");
            parseMoney(attributes.get("amount"));

            try {
                OrderStatus.valueOf(attributes.get("status"));
            } catch (RuntimeException exception) {
                throw new IllegalArgumentException(
                    "Invalid order status",
                    exception
                );
            }
        }

        private void validateBehavior(Map<String, String> attributes) {
            requireText(attributes.get("visitorId"), "visitorId");
            requireText(attributes.get("pagePath"), "pagePath");

            String path = attributes.get("pagePath");
            if (!path.startsWith("/") || path.startsWith("//")) {
                throw new IllegalArgumentException(
                    "Page path must be relative"
                );
            }

            Set<String> eventTypes = Set.of(
                "page_view",
                "product_view",
                "add_to_cart",
                "search",
                "checkout_started"
            );

            if (!eventTypes.contains(attributes.get("eventType"))) {
                throw new IllegalArgumentException(
                    "Unsupported behavioral event"
                );
            }
        }

        private int parseNonNegativeInteger(
            String value,
            String field
        ) {
            try {
                int result = Integer.parseInt(value);

                if (result < 0) {
                    throw new NumberFormatException("negative");
                }

                return result;
            } catch (RuntimeException exception) {
                throw new IllegalArgumentException(
                    field + " must be a non-negative integer",
                    exception
                );
            }
        }
    }

    static final class AnalyticsService {
        static BigDecimal paidInrRevenue(
            List<CollectedRecord> records
        ) {
            return records.stream()
                .filter(record ->
                    record.category() == Category.TRANSACTIONAL
                )
                .filter(record ->
                    "PAID".equals(record.attributes().get("status"))
                )
                .filter(record ->
                    "INR".equals(record.attributes().get("currency"))
                )
                .map(record ->
                    parseMoney(record.attributes().get("amount"))
                )
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.UNNECESSARY);
        }

        static Map<Category, Long> countByCategory(
            List<CollectedRecord> records
        ) {
            Map<Category, Long> counts = new EnumMap<>(Category.class);

            for (Category category : Category.values()) {
                counts.put(
                    category,
                    records.stream()
                        .filter(record -> record.category() == category)
                        .count()
                );
            }

            return counts;
        }
    }

    private static CollectionRequest request(
        SourcePolicy policy,
        String externalId,
        Instant observed,
        Instant collected,
        String subject,
        Map<String, String> attributes
    ) {
        return new CollectionRequest(
            policy,
            externalId,
            observed,
            collected,
            policy.purpose(),
            policy.lawfulBasis(),
            subject,
            attributes
        );
    }

    public static void main(String[] args) {
        Instant now = Instant.parse("2026-10-13T08:30:00Z");

        ConsentRegistry consent = new ConsentRegistry();
        consent.grant("visitor-201", "product_experience_analytics");

        CollectionRepository repository = new CollectionRepository();
        CollectionService service = new CollectionService(
            consent,
            repository
        );

        SourcePolicy inventoryPolicy = new SourcePolicy(
            "erp_inventory",
            Category.INTERNAL,
            "inventory_reconciliation",
            "documented_business_purpose",
            false
        );

        SourcePolicy supplierPolicy = new SourcePolicy(
            "supplier_catalog_api",
            Category.EXTERNAL,
            "supplier_price_comparison",
            "contract_and_documented_purpose",
            false
        );

        SourcePolicy orderPolicy = new SourcePolicy(
            "order_management",
            Category.TRANSACTIONAL,
            "order_fulfillment",
            "contract_performance",
            false
        );

        SourcePolicy behaviorPolicy = new SourcePolicy(
            "web_analytics",
            Category.BEHAVIORAL,
            "product_experience_analytics",
            "consent",
            true
        );

        List<CollectionRequest> requests = List.of(
            request(
                inventoryPolicy,
                "stock-2026-10-13",
                now.minusSeconds(60),
                now,
                null,
                Map.of(
                    "warehouse", "DEL-01",
                    "sku", "LAPTOP-14",
                    "availableUnits", "184",
                    "reservedUnits", "16"
                )
            ),
            request(
                supplierPolicy,
                "supplier-feed-8842",
                now.minusSeconds(120),
                now,
                null,
                Map.of(
                    "supplier", "Northstar Components",
                    "sku", "LAPTOP-14",
                    "unitPrice", "64500.00",
                    "currency", "INR"
                )
            ),
            request(
                orderPolicy,
                "ORD-2026-1001",
                now.minusSeconds(30),
                now,
                null,
                Map.of(
                    "orderId", "ORD-2026-1001",
                    "customerId", "CUS-0081",
                    "amount", "72999.90",
                    "currency", "INR",
                    "status", "PAID"
                )
            ),
            request(
                behaviorPolicy,
                "evt-5001",
                now.minusSeconds(10),
                now,
                "visitor-201",
                Map.of(
                    "visitorId", "visitor-201",
                    "eventType", "checkout_started",
                    "pagePath", "/checkout"
                )
            ),
            request(
                behaviorPolicy,
                "evt-5002",
                now.minusSeconds(10),
                now,
                "visitor-202",
                Map.of(
                    "visitorId", "visitor-202",
                    "eventType", "page_view",
                    "pagePath", "/home"
                )
            )
        );

        for (CollectionRequest item : requests) {
            IngestionOutcome outcome = service.collect(item);
            System.out.println(
                (outcome.accepted() ? "Accepted: " : "Rejected: ")
                    + outcome.message()
            );
        }

        // A retry using the same external ID and content remains idempotent.
        IngestionOutcome duplicate = service.collect(requests.get(0));
        System.out.println("Duplicate: " + duplicate.message());

        System.out.println("\nAccepted records by category");
        AnalyticsService.countByCategory(repository.all())
            .forEach((category, count) ->
                System.out.println(category + ": " + count)
            );

        System.out.println(
            "\nPaid INR revenue: Rs "
                + AnalyticsService.paidInrRevenue(repository.all())
        );

        System.out.println("\nAudit events");
        repository.auditEvents().forEach(System.out::println);
    }
}
