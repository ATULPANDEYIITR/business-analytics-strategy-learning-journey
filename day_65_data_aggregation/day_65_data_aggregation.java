import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.function.Function;
import java.util.stream.Collectors;

/*
 * Data Aggregation: Enterprise Sales Intelligence.
 *
 * Java 17 implementation covering:
 * - Domain modeling using records and enums.
 * - Multi-dimensional grouping.
 * - Aggregation policies.
 * - Conditional aggregation.
 * - Pivot and unpivot.
 * - Financial precision.
 * - Incremental aggregation.
 * - Access-controlled reporting.
 * - Reconciliation and validation.
 */

public class DataAggregation {

    enum TransactionStatus {
        COMPLETED,
        PENDING,
        CANCELLED
    }

    enum AggregationOperation {
        COUNT,
        SUM,
        AVERAGE,
        MINIMUM,
        MAXIMUM,
        DISTINCT_COUNT
    }

    enum ReportingRole {
        ANALYST,
        MANAGER,
        AUDITOR
    }

    record SalesTransaction(
        String transactionId,
        String region,
        String category,
        String product,
        String salesperson,
        int quantity,
        BigDecimal unitPrice,
        LocalDate transactionDate,
        TransactionStatus status
    ) {
        SalesTransaction {
            requireText(transactionId, "transactionId");
            requireText(region, "region");
            requireText(category, "category");
            requireText(product, "product");
            requireText(salesperson, "salesperson");

            Objects.requireNonNull(unitPrice, "unitPrice");
            Objects.requireNonNull(transactionDate, "transactionDate");
            Objects.requireNonNull(status, "status");

            if (quantity <= 0) {
                throw new ValidationException(
                    "Quantity must be positive."
                );
            }

            if (unitPrice.signum() < 0) {
                throw new ValidationException(
                    "Unit price cannot be negative."
                );
            }

            if (unitPrice.scale() > 2) {
                throw new ValidationException(
                    "Unit price supports at most two decimal places."
                );
            }

            if (unitPrice.precision() > 15) {
                throw new ValidationException(
                    "Unit price exceeds supported precision."
                );
            }
        }

        BigDecimal revenue() {
            return unitPrice.multiply(BigDecimal.valueOf(quantity));
        }

        private static void requireText(String value, String field) {
            if (value == null || value.isBlank()) {
                throw new ValidationException(
                    field + " must be nonempty."
                );
            }
        }
    }

    record GroupKey(List<String> dimensions) {
        GroupKey {
            dimensions = List.copyOf(dimensions);

            if (dimensions.isEmpty()) {
                throw new ValidationException(
                    "A group must have at least one dimension."
                );
            }
        }
    }

    record AggregateResult(
        GroupKey key,
        long count,
        long totalQuantity,
        BigDecimal totalRevenue,
        BigDecimal averageRevenue,
        BigDecimal minimumRevenue,
        BigDecimal maximumRevenue,
        int distinctProducts
    ) {}

    record PivotCell(
        String row,
        String column
    ) {}

    record ReportRequest(
        ReportingRole role,
        boolean includePending,
        boolean includeCancelled
    ) {
        ReportRequest {
            Objects.requireNonNull(role, "role");
        }
    }

    static class ValidationException extends RuntimeException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class PolicyException extends RuntimeException {
        PolicyException(String message) {
            super(message);
        }
    }

    interface AggregationPolicy {
        boolean accepts(SalesTransaction transaction);
        String name();
    }

    static class CompletedTransactionsPolicy
        implements AggregationPolicy {

        @Override
        public boolean accepts(SalesTransaction transaction) {
            return transaction.status() ==
                TransactionStatus.COMPLETED;
        }

        @Override
        public String name() {
            return "completed-only";
        }
    }

    static class AllTransactionsPolicy
        implements AggregationPolicy {

        @Override
        public boolean accepts(SalesTransaction transaction) {
            return true;
        }

        @Override
        public String name() {
            return "all-transactions";
        }
    }

    static class AggregateAccumulator {
        private long count;
        private long totalQuantity;
        private BigDecimal totalRevenue = BigDecimal.ZERO;
        private BigDecimal minimumRevenue;
        private BigDecimal maximumRevenue;
        private final Set<String> products = new HashSet<>();

        void add(SalesTransaction transaction) {
            BigDecimal revenue = transaction.revenue();

            count = Math.addExact(count, 1);
            totalQuantity = Math.addExact(
                totalQuantity,
                transaction.quantity()
            );

            totalRevenue = totalRevenue.add(revenue);

            minimumRevenue = minimumRevenue == null
                ? revenue
                : minimumRevenue.min(revenue);

            maximumRevenue = maximumRevenue == null
                ? revenue
                : maximumRevenue.max(revenue);

            products.add(transaction.product());
        }

        AggregateResult result(GroupKey key) {
            BigDecimal average = count == 0
                ? BigDecimal.ZERO
                : totalRevenue.divide(
                    BigDecimal.valueOf(count),
                    2,
                    RoundingMode.HALF_UP
                );

            return new AggregateResult(
                key,
                count,
                totalQuantity,
                totalRevenue,
                average,
                minimumRevenue,
                maximumRevenue,
                products.size()
            );
        }
    }

    static class AggregationService {
        private final List<SalesTransaction> transactions;

        AggregationService(List<SalesTransaction> transactions) {
            Objects.requireNonNull(transactions);

            Set<String> identifiers = new HashSet<>();

            for (SalesTransaction transaction : transactions) {
                Objects.requireNonNull(transaction);

                if (!identifiers.add(transaction.transactionId())) {
                    throw new ValidationException(
                        "Duplicate transaction: " +
                        transaction.transactionId()
                    );
                }
            }

            this.transactions = List.copyOf(transactions);
        }

        List<AggregateResult> groupAndAggregate(
            List<Function<SalesTransaction, String>> dimensions,
            AggregationPolicy policy
        ) {
            if (dimensions == null || dimensions.isEmpty()) {
                throw new ValidationException(
                    "Grouping dimensions cannot be empty."
                );
            }

            Objects.requireNonNull(policy);

            Map<GroupKey, AggregateAccumulator> groups =
                new TreeMap<>(
                    Comparator.comparing(
                        key -> String.join("|", key.dimensions())
                    )
                );

            for (SalesTransaction transaction : transactions) {
                if (!policy.accepts(transaction)) {
                    continue;
                }

                List<String> values = dimensions.stream()
                    .map(dimension -> Objects.requireNonNull(
                        dimension.apply(transaction),
                        "Grouping values cannot be null."
                    ))
                    .toList();

                GroupKey key = new GroupKey(values);

                groups.computeIfAbsent(
                    key,
                    ignored -> new AggregateAccumulator()
                ).add(transaction);
            }

            return groups.entrySet().stream()
                .map(entry -> entry.getValue().result(entry.getKey()))
                .toList();
        }

        Map<String, Map<String, BigDecimal>> pivot(
            String rowField,
            String columnField,
            Function<SalesTransaction, BigDecimal> valueSelector,
            AggregationOperation operation,
            AggregationPolicy policy
        ) {
            Map<PivotCell, List<BigDecimal>> cells = new HashMap<>();

            for (SalesTransaction transaction : transactions) {
                if (!policy.accepts(transaction)) {
                    continue;
                }

                String row = selectDimension(transaction, rowField);
                String column = selectDimension(
                    transaction,
                    columnField
                );

                BigDecimal value = Objects.requireNonNull(
                    valueSelector.apply(transaction)
                );

                cells.computeIfAbsent(
                    new PivotCell(row, column),
                    ignored -> new ArrayList<>()
                ).add(value);
            }

            Map<String, Map<String, BigDecimal>> result =
                new TreeMap<>();

            for (Map.Entry<PivotCell, List<BigDecimal>> entry :
                 cells.entrySet()) {

                BigDecimal aggregated = applyOperation(
                    entry.getValue(),
                    operation
                );

                result.computeIfAbsent(
                    entry.getKey().row(),
                    ignored -> new TreeMap<>()
                ).put(
                    entry.getKey().column(),
                    aggregated
                );
            }

            return result;
        }

        private String selectDimension(
            SalesTransaction transaction,
            String field
        ) {
            return switch (field) {
                case "region" -> transaction.region();
                case "category" -> transaction.category();
                case "product" -> transaction.product();
                case "salesperson" -> transaction.salesperson();
                case "status" -> transaction.status().name();
                default -> throw new ValidationException(
                    "Unsupported dimension: " + field
                );
            };
        }

        private BigDecimal applyOperation(
            List<BigDecimal> values,
            AggregationOperation operation
        ) {
            return switch (operation) {
                case COUNT -> BigDecimal.valueOf(values.size());

                case SUM -> values.stream()
                    .reduce(BigDecimal.ZERO, BigDecimal::add);

                case AVERAGE -> values.stream()
                    .reduce(BigDecimal.ZERO, BigDecimal::add)
                    .divide(
                        BigDecimal.valueOf(values.size()),
                        2,
                        RoundingMode.HALF_UP
                    );

                case MINIMUM -> values.stream()
                    .min(BigDecimal::compareTo)
                    .orElseThrow();

                case MAXIMUM -> values.stream()
                    .max(BigDecimal::compareTo)
                    .orElseThrow();

                case DISTINCT_COUNT -> BigDecimal.valueOf(
                    values.stream().distinct().count()
                );
            };
        }

        Map<String, Map<String, BigDecimal>> conditionalAggregation() {
            Map<String, Map<String, BigDecimal>> result =
                new TreeMap<>();

            for (TransactionStatus status :
                 TransactionStatus.values()) {

                Map<String, BigDecimal> regional = transactions.stream()
                    .filter(t -> t.status() == status)
                    .collect(Collectors.groupingBy(
                        SalesTransaction::region,
                        TreeMap::new,
                        Collectors.reducing(
                            BigDecimal.ZERO,
                            SalesTransaction::revenue,
                            BigDecimal::add
                        )
                    ));

                result.put(status.name(), regional);
            }

            return result;
        }

        List<Map<String, Object>> unpivot(
            Map<String, Map<String, BigDecimal>> pivot
        ) {
            List<Map<String, Object>> rows = new ArrayList<>();

            pivot.forEach((row, columns) ->
                columns.forEach((column, value) -> {
                    Map<String, Object> item =
                        new LinkedHashMap<>();

                    item.put("region", row);
                    item.put("category", column);
                    item.put("revenue", value);

                    rows.add(Collections.unmodifiableMap(item));
                })
            );

            return List.copyOf(rows);
        }

        BigDecimal totalRevenue() {
            return transactions.stream()
                .map(SalesTransaction::revenue)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        List<SalesTransaction> records() {
            return transactions;
        }
    }

    static class ReportingService {
        private final AggregationService aggregationService;

        ReportingService(AggregationService aggregationService) {
            this.aggregationService = aggregationService;
        }

        List<AggregateResult> execute(ReportRequest request) {
            if (
                request.role() != ReportingRole.ANALYST &&
                request.role() != ReportingRole.MANAGER &&
                request.role() != ReportingRole.AUDITOR
            ) {
                throw new PolicyException("Reporting access denied.");
            }

            if (
                request.includeCancelled() &&
                request.role() != ReportingRole.AUDITOR
            ) {
                throw new PolicyException(
                    "Only auditors can include cancelled transactions."
                );
            }

            if (
                request.includePending() &&
                request.role() == ReportingRole.ANALYST
            ) {
                throw new PolicyException(
                    "Analysts cannot access pending transaction reports."
                );
            }

            AggregationPolicy policy =
                request.includePending() || request.includeCancelled()
                    ? new AllTransactionsPolicy()
                    : new CompletedTransactionsPolicy();

            return aggregationService.groupAndAggregate(
                List.of(
                    SalesTransaction::region,
                    SalesTransaction::category
                ),
                policy
            );
        }
    }

    static class IncrementalAggregationService {
        private final Map<String, AggregateAccumulator> groups =
            new HashMap<>();

        private final Set<String> processedIds = new HashSet<>();

        public synchronized void process(
            SalesTransaction transaction
        ) {
            if (!processedIds.add(transaction.transactionId())) {
                throw new ValidationException(
                    "Duplicate event rejected."
                );
            }

            try {
                groups.computeIfAbsent(
                    transaction.region(),
                    ignored -> new AggregateAccumulator()
                ).add(transaction);
            } catch (RuntimeException exception) {
                processedIds.remove(transaction.transactionId());
                throw exception;
            }
        }

        public synchronized int groupCount() {
            return groups.size();
        }

        public synchronized int processedCount() {
            return processedIds.size();
        }
    }

    static List<SalesTransaction> sampleData() {
        return List.of(
            new SalesTransaction("T001", "North", "Electronics", "Laptop", "Asha", 2, new BigDecimal("65000.00"), LocalDate.parse("2026-10-01"), TransactionStatus.COMPLETED),
            new SalesTransaction("T002", "North", "Electronics", "Phone", "Asha", 3, new BigDecimal("25000.00"), LocalDate.parse("2026-10-02"), TransactionStatus.COMPLETED),
            new SalesTransaction("T003", "South", "Furniture", "Chair", "Ravi", 5, new BigDecimal("3000.00"), LocalDate.parse("2026-10-03"), TransactionStatus.COMPLETED),
            new SalesTransaction("T004", "South", "Electronics", "Laptop", "Ravi", 1, new BigDecimal("65000.00"), LocalDate.parse("2026-10-04"), TransactionStatus.PENDING),
            new SalesTransaction("T005", "East", "Furniture", "Table", "Neha", 2, new BigDecimal("12000.00"), LocalDate.parse("2026-10-05"), TransactionStatus.COMPLETED),
            new SalesTransaction("T006", "East", "Electronics", "Phone", "Neha", 4, new BigDecimal("25000.00"), LocalDate.parse("2026-10-06"), TransactionStatus.CANCELLED),
            new SalesTransaction("T007", "West", "Furniture", "Chair", "Arun", 3, new BigDecimal("3000.00"), LocalDate.parse("2026-10-07"), TransactionStatus.COMPLETED),
            new SalesTransaction("T008", "West", "Electronics", "Laptop", "Arun", 2, new BigDecimal("65000.00"), LocalDate.parse("2026-10-08"), TransactionStatus.COMPLETED),
            new SalesTransaction("T009", "North", "Furniture", "Table", "Asha", 1, new BigDecimal("12000.00"), LocalDate.parse("2026-10-09"), TransactionStatus.PENDING),
            new SalesTransaction("T010", "South", "Furniture", "Chair", "Ravi", 2, new BigDecimal("3000.00"), LocalDate.parse("2026-10-10"), TransactionStatus.COMPLETED)
        );
    }

    public static void main(String[] args) {
        try {
            AggregationService service =
                new AggregationService(sampleData());

            System.out.println("1. Multi-dimensional aggregation");

            List<AggregateResult> groups =
                service.groupAndAggregate(
                    List.of(
                        SalesTransaction::region,
                        SalesTransaction::category
                    ),
                    new AllTransactionsPolicy()
                );

            groups.forEach(System.out::println);

            System.out.println("\n2. Completed-only aggregation");

            service.groupAndAggregate(
                List.of(SalesTransaction::region),
                new CompletedTransactionsPolicy()
            ).forEach(System.out::println);

            System.out.println("\n3. Conditional aggregation");
            System.out.println(service.conditionalAggregation());

            System.out.println("\n4. Pivot table");

            Map<String, Map<String, BigDecimal>> pivot =
                service.pivot(
                    "region",
                    "category",
                    SalesTransaction::revenue,
                    AggregationOperation.SUM,
                    new AllTransactionsPolicy()
                );

            pivot.forEach((region, columns) ->
                System.out.println(region + " => " + columns)
            );

            System.out.println("\n5. Unpivot");
            service.unpivot(pivot).forEach(System.out::println);

            System.out.println("\n6. Role-based reporting");

            ReportingService reporting =
                new ReportingService(service);

            ReportRequest request = new ReportRequest(
                ReportingRole.MANAGER,
                false,
                false
            );

            reporting.execute(request).forEach(System.out::println);

            System.out.println("\n7. Policy conflict");

            try {
                reporting.execute(
                    new ReportRequest(
                        ReportingRole.ANALYST,
                        true,
                        false
                    )
                );
            } catch (PolicyException exception) {
                System.out.println(
                    "Policy rejected: " + exception.getMessage()
                );
            }

            System.out.println("\n8. Incremental aggregation");

            IncrementalAggregationService incremental =
                new IncrementalAggregationService();

            for (SalesTransaction transaction :
                 service.records()) {
                incremental.process(transaction);
            }

            System.out.println(
                "Processed events: " +
                incremental.processedCount()
            );

            System.out.println(
                "Regional groups: " +
                incremental.groupCount()
            );

            System.out.println("\n9. Reconciliation");

            BigDecimal groupedTotal = groups.stream()
                .map(AggregateResult::totalRevenue)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

            if (groupedTotal.compareTo(service.totalRevenue()) != 0) {
                throw new IllegalStateException(
                    "Revenue reconciliation failed."
                );
            }

            System.out.println(
                "Total revenue: " + service.totalRevenue()
            );

            System.out.println("All enterprise aggregation checks passed.");

        } catch (RuntimeException exception) {
            System.err.println(
                "Aggregation failure: " + exception.getMessage()
            );
            System.exitCodePlaceholder();
        }
    }
}
