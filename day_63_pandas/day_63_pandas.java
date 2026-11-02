import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Predicate;
import java.util.stream.Collectors;

public class PandasConceptsEnterprise {

    enum Category {
        ELECTRONICS,
        FURNITURE,
        ACCESSORIES
    }

    enum DataState {
        RAW,
        VALIDATED,
        ENRICHED,
        AGGREGATED
    }

    record SalesRecord(
        int orderId,
        String orderDate,
        String region,
        String product,
        Category category,
        int units,
        double unitPrice,
        double discount,
        String customer
    ) {}

    record EnrichedRecord(
        SalesRecord source,
        double grossSales,
        double discountAmount,
        double netSales,
        String month,
        boolean highValue
    ) {}

    record CustomerProfile(
        String segment,
        String accountManager
    ) {}

    record GroupKey(
        String region,
        Category category
    ) {}

    record Aggregate(
        GroupKey key,
        long orders,
        int units,
        double netSales
    ) {}

    static final class DataValidationException extends RuntimeException {
        DataValidationException(String message) {
            super(message);
        }
    }

    interface DataTransformer<I, O> {
        O transform(I input);
    }

    static final class SalesValidator implements DataTransformer<List<SalesRecord>, List<SalesRecord>> {
        @Override
        public List<SalesRecord> transform(List<SalesRecord> records) {
            if (records == null || records.isEmpty()) {
                throw new DataValidationException("Sales records cannot be empty");
            }

            Set<Integer> orderIds = new HashSet<>();

            for (SalesRecord record : records) {
                Objects.requireNonNull(record, "Record cannot be null");

                if (!orderIds.add(record.orderId())) {
                    throw new DataValidationException(
                        "Duplicate order ID: " + record.orderId()
                    );
                }

                if (record.units() <= 0) {
                    throw new DataValidationException("Units must be positive");
                }

                if (!Double.isFinite(record.unitPrice()) ||
                    record.unitPrice() <= 0) {
                    throw new DataValidationException("Unit price must be positive");
                }

                if (!Double.isFinite(record.discount()) ||
                    record.discount() < 0 ||
                    record.discount() >= 1) {
                    throw new DataValidationException(
                        "Discount must be in [0, 1)"
                    );
                }

                if (record.orderDate() == null ||
                    !record.orderDate().matches("\\d{4}-\\d{2}-\\d{2}")) {
                    throw new DataValidationException("Invalid date");
                }
            }

            return List.copyOf(records);
        }
    }

    static final class EnrichmentService
        implements DataTransformer<List<SalesRecord>, List<EnrichedRecord>> {

        @Override
        public List<EnrichedRecord> transform(List<SalesRecord> records) {
            return records.stream()
                .map(record -> {
                    double gross = record.units() * record.unitPrice();
                    double discountAmount = gross * record.discount();
                    double net = gross - discountAmount;

                    return new EnrichedRecord(
                        record,
                        gross,
                        discountAmount,
                        net,
                        record.orderDate().substring(0, 7),
                        net >= 100000
                    );
                })
                .toList();
        }
    }

    static final class CustomerMergeService {
        private final Map<String, CustomerProfile> profiles;

        CustomerMergeService(Map<String, CustomerProfile> profiles) {
            this.profiles = Map.copyOf(profiles);
        }

        List<String> customerSegments(List<EnrichedRecord> records) {
            return records.stream()
                .map(record -> {
                    CustomerProfile profile =
                        profiles.get(record.source().customer());

                    String segment = profile == null
                        ? "Unknown"
                        : profile.segment();

                    return record.source().orderId()
                        + " -> "
                        + record.source().customer()
                        + " -> "
                        + segment;
                })
                .toList();
        }
    }

    static final class AggregationService {

        List<Aggregate> groupByRegionAndCategory(
            List<EnrichedRecord> records
        ) {
            Map<GroupKey, List<EnrichedRecord>> groups =
                records.stream().collect(
                    Collectors.groupingBy(
                        record -> new GroupKey(
                            record.source().region(),
                            record.source().category()
                        ),
                        LinkedHashMap::new,
                        Collectors.toList()
                    )
                );

            return groups.entrySet().stream()
                .map(entry -> {
                    List<EnrichedRecord> rows = entry.getValue();

                    return new Aggregate(
                        entry.getKey(),
                        rows.size(),
                        rows.stream()
                            .mapToInt(row -> row.source().units())
                            .sum(),
                        rows.stream()
                            .mapToDouble(EnrichedRecord::netSales)
                            .sum()
                    );
                })
                .sorted(
                    Comparator.comparingDouble(Aggregate::netSales)
                        .reversed()
                )
                .toList();
        }

        Map<String, Double> monthlyTotals(
            List<EnrichedRecord> records
        ) {
            return records.stream().collect(
                Collectors.groupingBy(
                    EnrichedRecord::month,
                    java.util.TreeMap::new,
                    Collectors.summingDouble(
                        EnrichedRecord::netSales
                    )
                )
            );
        }
    }

    static final class QueryService {
        List<EnrichedRecord> filter(
            List<EnrichedRecord> records,
            Predicate<EnrichedRecord> predicate
        ) {
            return records.stream()
                .filter(predicate)
                .sorted(
                    Comparator.comparingDouble(
                        EnrichedRecord::netSales
                    ).reversed()
                )
                .toList();
        }
    }

    static final class DataWorkflow {
        private DataState state = DataState.RAW;

        List<EnrichedRecord> execute(List<SalesRecord> source) {
            List<SalesRecord> validated =
                new SalesValidator().transform(source);

            state = DataState.VALIDATED;

            List<EnrichedRecord> enriched =
                new EnrichmentService().transform(validated);

            state = DataState.ENRICHED;

            if (enriched.isEmpty()) {
                throw new DataValidationException(
                    "Enrichment produced no records"
                );
            }

            return enriched;
        }

        DataState state() {
            return state;
        }
    }

    static List<SalesRecord> sampleData() {
        return List.of(
            new SalesRecord(1001, "2026-01-03", "North", "Laptop",
                Category.ELECTRONICS, 2, 75000, 0.05, "Apex Ltd"),
            new SalesRecord(1002, "2026-01-05", "South", "Monitor",
                Category.ELECTRONICS, 4, 18000, 0.10, "Beta Corp"),
            new SalesRecord(1003, "2026-01-08", "West", "Desk",
                Category.FURNITURE, 3, 12000, 0.00, "Gamma Pvt"),
            new SalesRecord(1004, "2026-01-11", "North", "Chair",
                Category.FURNITURE, 10, 6500, 0.08, "Apex Ltd"),
            new SalesRecord(1005, "2026-01-13", "East", "Laptop",
                Category.ELECTRONICS, 1, 82000, 0.05, "Delta Inc"),
            new SalesRecord(1006, "2026-01-18", "South", "Desk",
                Category.FURNITURE, 2, 13500, 0.03, "Beta Corp"),
            new SalesRecord(1007, "2026-01-20", "West", "Keyboard",
                Category.ACCESSORIES, 15, 2200, 0.00, "Gamma Pvt"),
            new SalesRecord(1008, "2026-01-23", "East", "Monitor",
                Category.ELECTRONICS, 5, 19500, 0.12, "Delta Inc"),
            new SalesRecord(1009, "2026-02-02", "North", "Laptop",
                Category.ELECTRONICS, 3, 76000, 0.04, "Apex Ltd"),
            new SalesRecord(1010, "2026-02-04", "South", "Chair",
                Category.FURNITURE, 8, 6200, 0.06, "Beta Corp"),
            new SalesRecord(1011, "2026-02-09", "West", "Monitor",
                Category.ELECTRONICS, 2, 18500, 0.02, "Gamma Pvt"),
            new SalesRecord(1012, "2026-02-15", "East", "Keyboard",
                Category.ACCESSORIES, 20, 2100, 0.05, "Delta Inc")
        );
    }

    public static void main(String[] args) {
        try {
            List<SalesRecord> source = sampleData();

            DataWorkflow workflow = new DataWorkflow();
            List<EnrichedRecord> enriched = workflow.execute(source);

            System.out.println("STATE: " + workflow.state());
            System.out.println("ROWS: " + enriched.size());

            QueryService queryService = new QueryService();

            List<EnrichedRecord> electronics =
                queryService.filter(
                    enriched,
                    row -> row.source().category() == Category.ELECTRONICS
                        && row.netSales() >= 50000
                );

            System.out.println("\nHIGH-VALUE ELECTRONICS");
            electronics.forEach(row ->
                System.out.printf(
                    "%d %s %.2f%n",
                    row.source().orderId(),
                    row.source().product(),
                    row.netSales()
                )
            );

            AggregationService aggregation =
                new AggregationService();

            System.out.println("\nREGION/CATEGORY AGGREGATION");
            aggregation.groupByRegionAndCategory(enriched)
                .forEach(group ->
                    System.out.printf(
                        "%s | %s | orders=%d | units=%d | net=%.2f%n",
                        group.key().region(),
                        group.key().category(),
                        group.orders(),
                        group.units(),
                        group.netSales()
                    )
                );

            System.out.println("\nMONTHLY TOTALS");
            aggregation.monthlyTotals(enriched)
                .forEach((month, total) ->
                    System.out.printf(
                        "%s = %.2f%n",
                        month,
                        total
                    )
                );

            Map<String, CustomerProfile> profiles =
                new HashMap<>();

            profiles.put(
                "Apex Ltd",
                new CustomerProfile("Enterprise", "Neha")
            );
            profiles.put(
                "Beta Corp",
                new CustomerProfile("Enterprise", "Ravi")
            );
            profiles.put(
                "Gamma Pvt",
                new CustomerProfile("Mid-Market", "Meera")
            );
            profiles.put(
                "Delta Inc",
                new CustomerProfile("Enterprise", "Arjun")
            );

            System.out.println("\nCUSTOMER MERGE");
            new CustomerMergeService(profiles)
                .customerSegments(enriched)
                .forEach(System.out::println);

            assert enriched.stream()
                .allMatch(row -> row.netSales() >= 0);

            List<SalesRecord> duplicate =
                new ArrayList<>(source);
            duplicate.add(source.get(0));

            try {
                new SalesValidator().transform(duplicate);
                throw new AssertionError(
                    "Duplicate data should have failed"
                );
            } catch (DataValidationException expected) {
                System.out.println("\nDuplicate validation: REJECTED");
            }

            List<SalesRecord> invalid =
                List.of(
                    new SalesRecord(
                        9000,
                        "2026-01-01",
                        "North",
                        "Invalid",
                        Category.ELECTRONICS,
                        1,
                        1000,
                        1.0,
                        "Test"
                    )
                );

            try {
                new SalesValidator().transform(invalid);
                throw new AssertionError(
                    "Invalid discount should have failed"
                );
            } catch (DataValidationException expected) {
                System.out.println("Discount validation: REJECTED");
            }

            System.out.println("Data quality: VALID");
        } catch (RuntimeException error) {
            System.err.println(
                "Processing failure: " + error.getMessage()
            );
            System.exit(1);
        }
    }
}
