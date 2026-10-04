import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.function.Function;
import java.util.stream.Collectors;

/*
 * GROUP BY: Segmenting and Aggregating Business Data
 *
 * Enterprise scenario:
 * A commercial analytics service receives sales transactions and exposes
 * regional, channel, category, and customer-segment reporting.
 *
 * Compile:
 *   javac GroupByBusinessData.java
 *
 * Run:
 *   java GroupByBusinessData
 */
public class GroupByBusinessData {

    enum Channel {
        ONLINE, RETAIL, PARTNER
    }

    enum CustomerSegment {
        CONSUMER, SMB, ENTERPRISE
    }

    enum Category {
        ELECTRONICS, OFFICE, SOFTWARE
    }

    record Sale(
        int id,
        String date,
        String region,
        Channel channel,
        Category category,
        String product,
        CustomerSegment customerSegment,
        int units,
        double revenue,
        double cost,
        double discount
    ) {
        Sale {
            Objects.requireNonNull(date);
            Objects.requireNonNull(region);
            Objects.requireNonNull(channel);
            Objects.requireNonNull(category);
            Objects.requireNonNull(product);
            Objects.requireNonNull(customerSegment);

            if (units <= 0) {
                throw new IllegalArgumentException("Units must be positive");
            }

            if (!Double.isFinite(revenue) || revenue < 0) {
                throw new IllegalArgumentException("Revenue must be non-negative");
            }

            if (!Double.isFinite(cost) || cost < 0 || cost > revenue) {
                throw new IllegalArgumentException("Cost is outside valid range");
            }

            if (!Double.isFinite(discount) || discount < 0 || discount > 1) {
                throw new IllegalArgumentException("Discount must be between 0 and 1");
            }
        }

        double profit() {
            return revenue - cost;
        }
    }

    record GroupKey(String region, Category category) {}

    record AggregateResult(
        long transactions,
        long units,
        double revenue,
        double profit,
        Set<String> products
    ) {
        double margin() {
            return revenue == 0 ? 0 : profit / revenue;
        }

        double averageOrderValue() {
            return transactions == 0 ? 0 : revenue / transactions;
        }

        long distinctProducts() {
            return products.size();
        }
    }

    /*
     * The service abstraction separates aggregation rules from presentation.
     * This is useful in an enterprise application where the same grouped
     * metrics may feed dashboards, exports, APIs, or scheduled reports.
     */
    static final class SalesAnalyticsService {
        private final List<Sale> sales;

        SalesAnalyticsService(List<Sale> sales) {
            validateUniqueIds(sales);
            this.sales = List.copyOf(sales);
        }

        private static void validateUniqueIds(List<Sale> sales) {
            Set<Integer> ids = new HashSet<>();

            for (Sale sale : sales) {
                if (!ids.add(sale.id())) {
                    throw new IllegalArgumentException(
                        "Duplicate sale ID: " + sale.id()
                    );
                }
            }
        }

        Map<String, AggregateResult> revenueByRegion() {
            return aggregateBy(
                sales,
                Sale::region
            );
        }

        Map<Channel, AggregateResult> revenueByChannel() {
            return aggregateBy(
                sales,
                Sale::channel
            );
        }

        Map<GroupKey, AggregateResult> revenueByRegionAndCategory() {
            return aggregateBy(
                sales,
                sale -> new GroupKey(sale.region(), sale.category())
            );
        }

        private static <K> Map<K, AggregateResult> aggregateBy(
            List<Sale> records,
            Function<Sale, K> keyFunction
        ) {
            /*
             * groupingBy creates one collection per key. The downstream
             * collector then folds each collection into domain metrics.
             */
            return records.stream()
                .collect(
                    Collectors.groupingBy(
                        keyFunction,
                        TreeMap::new,
                        Collectors.collectingAndThen(
                            Collectors.toList(),
                            SalesAnalyticsService::aggregate
                        )
                    )
                );
        }

        private static AggregateResult aggregate(List<Sale> records) {
            long transactions = records.size();

            long units = records.stream()
                .mapToLong(Sale::units)
                .sum();

            double revenue = records.stream()
                .mapToDouble(Sale::revenue)
                .sum();

            double profit = records.stream()
                .mapToDouble(Sale::profit)
                .sum();

            Set<String> products = records.stream()
                .map(Sale::product)
                .collect(Collectors.toUnmodifiableSet());

            return new AggregateResult(
                transactions,
                units,
                revenue,
                profit,
                products
            );
        }

        List<Map<String, Object>> highValueRegions(double minimumRevenue) {
            /*
             * This is a HAVING-style operation because the revenue threshold
             * is applied to a completed regional aggregate rather than to
             * individual transactions.
             */
            return revenueByRegion()
                .entrySet()
                .stream()
                .filter(entry -> entry.getValue().revenue() >= minimumRevenue)
                .map(entry -> Map.of(
                    "region", entry.getKey(),
                    "transactions", entry.getValue().transactions(),
                    "revenue", entry.getValue().revenue()
                ))
                .toList();
        }

        List<Map<String, Object>> conditionalRegionMetrics() {
            /*
             * A single regional grouping can support several conditional
             * measures. The original records are retained for each condition
             * instead of producing separate populations for each metric.
             */
            Map<String, List<Sale>> groups = sales.stream()
                .collect(Collectors.groupingBy(Sale::region));

            List<Map<String, Object>> results = new ArrayList<>();

            for (var entry : new TreeMap<>(groups).entrySet()) {
                List<Sale> rows = entry.getValue();

                double totalRevenue = rows.stream()
                    .mapToDouble(Sale::revenue)
                    .sum();

                double onlineRevenue = rows.stream()
                    .filter(sale -> sale.channel() == Channel.ONLINE)
                    .mapToDouble(Sale::revenue)
                    .sum();

                double softwareRevenue = rows.stream()
                    .filter(sale -> sale.category() == Category.SOFTWARE)
                    .mapToDouble(Sale::revenue)
                    .sum();

                long enterpriseTransactions = rows.stream()
                    .filter(sale ->
                        sale.customerSegment() == CustomerSegment.ENTERPRISE
                    )
                    .count();

                results.add(Map.of(
                    "region", entry.getKey(),
                    "totalRevenue", totalRevenue,
                    "onlineRevenue", onlineRevenue,
                    "softwareRevenue", softwareRevenue,
                    "enterpriseTransactions", enterpriseTransactions
                ));
            }

            return List.copyOf(results);
        }

        List<Map<String, Object>> customerSegmentReport() {
            Map<CustomerSegment, List<Sale>> groups = sales.stream()
                .collect(Collectors.groupingBy(
                    Sale::customerSegment,
                    TreeMap::new,
                    Collectors.toList()
                ));

            double totalRevenue = sales.stream()
                .mapToDouble(Sale::revenue)
                .sum();

            List<Map<String, Object>> result = new ArrayList<>();

            for (var entry : groups.entrySet()) {
                List<Sale> rows = entry.getValue();
                AggregateResult aggregate = aggregate(rows);

                double revenueShare = totalRevenue == 0
                    ? 0
                    : aggregate.revenue() / totalRevenue;

                result.add(Map.of(
                    "segment", entry.getKey(),
                    "transactions", aggregate.transactions(),
                    "distinctProducts", aggregate.distinctProducts(),
                    "revenue", aggregate.revenue(),
                    "revenueShare", revenueShare
                ));
            }

            return List.copyOf(result);
        }

        List<Map<String, Object>> topCategoriesByProfit(int limit) {
            Map<Category, AggregateResult> groups = aggregateBy(
                sales,
                Sale::category
            );

            return groups.entrySet()
                .stream()
                .sorted(
                    Comparator
                        .<Map.Entry<Category, AggregateResult>>
                        comparingDouble(entry -> entry.getValue().profit())
                        .reversed()
                        .thenComparing(entry -> entry.getKey().name())
                )
                .limit(limit)
                .map(entry -> Map.of(
                    "category", entry.getKey(),
                    "revenue", entry.getValue().revenue(),
                    "profit", entry.getValue().profit(),
                    "margin", entry.getValue().margin()
                ))
                .toList();
        }

        List<Map<String, Object>> quarterlyCategoryReport() {
            /*
             * The first seven characters of the ISO date identify the month.
             * The helper converts the month into a business quarter before
             * the category becomes part of the grouping key.
             */
            Map<String, List<Sale>> groups = sales.stream()
                .collect(Collectors.groupingBy(
                    sale -> quarter(sale.date()) + "|" + sale.category(),
                    TreeMap::new,
                    Collectors.toList()
                ));

            List<Map<String, Object>> result = new ArrayList<>();

            for (var entry : groups.entrySet()) {
                AggregateResult aggregate = aggregate(entry.getValue());

                result.add(Map.of(
                    "quarterCategory", entry.getKey(),
                    "transactions", aggregate.transactions(),
                    "revenue", aggregate.revenue(),
                    "profit", aggregate.profit(),
                    "margin", aggregate.margin()
                ));
            }

            return List.copyOf(result);
        }
    }

    static String quarter(String isoDate) {
        int month = Integer.parseInt(isoDate.substring(5, 7));
        int quarter = ((month - 1) / 3) + 1;
        return isoDate.substring(0, 4) + "-Q" + quarter;
    }

    static List<Sale> createSales() {
        return List.of(
            new Sale(1001, "2026-01-05", "North", Channel.ONLINE,
                Category.ELECTRONICS, "Laptop", CustomerSegment.ENTERPRISE,
                4, 4800, 3600, 0.05),
            new Sale(1002, "2026-01-08", "North", Channel.RETAIL,
                Category.OFFICE, "Monitor", CustomerSegment.SMB,
                10, 3000, 2100, 0.00),
            new Sale(1003, "2026-01-12", "South", Channel.ONLINE,
                Category.ELECTRONICS, "Phone", CustomerSegment.CONSUMER,
                15, 9000, 6300, 0.10),
            new Sale(1004, "2026-01-15", "West", Channel.PARTNER,
                Category.SOFTWARE, "Analytics", CustomerSegment.ENTERPRISE,
                3, 7500, 2250, 0.15),
            new Sale(1005, "2026-01-20", "East", Channel.RETAIL,
                Category.OFFICE, "Chair", CustomerSegment.SMB,
                20, 4000, 2600, 0.05),
            new Sale(1006, "2026-02-02", "North", Channel.ONLINE,
                Category.SOFTWARE, "CRM", CustomerSegment.ENTERPRISE,
                5, 10000, 3000, 0.08),
            new Sale(1007, "2026-02-05", "South", Channel.RETAIL,
                Category.ELECTRONICS, "Laptop", CustomerSegment.CONSUMER,
                3, 3600, 2700, 0.03),
            new Sale(1008, "2026-02-11", "West", Channel.ONLINE,
                Category.OFFICE, "Desk", CustomerSegment.SMB,
                12, 4800, 3000, 0.00),
            new Sale(1009, "2026-02-17", "East", Channel.PARTNER,
                Category.SOFTWARE, "Analytics", CustomerSegment.ENTERPRISE,
                4, 10000, 3000, 0.12),
            new Sale(1010, "2026-02-22", "North", Channel.RETAIL,
                Category.ELECTRONICS, "Phone", CustomerSegment.CONSUMER,
                8, 4800, 3360, 0.07),
            new Sale(1011, "2026-03-03", "South", Channel.ONLINE,
                Category.SOFTWARE, "CRM", CustomerSegment.SMB,
                7, 8400, 2800, 0.05),
            new Sale(1012, "2026-03-07", "West", Channel.PARTNER,
                Category.ELECTRONICS, "Laptop", CustomerSegment.ENTERPRISE,
                6, 7200, 5400, 0.10),
            new Sale(1013, "2026-03-10", "East", Channel.RETAIL,
                Category.OFFICE, "Monitor", CustomerSegment.CONSUMER,
                14, 4200, 2940, 0.04),
            new Sale(1014, "2026-03-18", "North", Channel.ONLINE,
                Category.SOFTWARE, "Analytics", CustomerSegment.ENTERPRISE,
                2, 5000, 1500, 0.20),
            new Sale(1015, "2026-03-24", "South", Channel.PARTNER,
                Category.OFFICE, "Chair", CustomerSegment.SMB,
                25, 5000, 3250, 0.06)
        );
    }

    static void printRows(String title, List<?> rows) {
        System.out.println("\n=== " + title + " ===");

        for (Object row : rows) {
            System.out.println(row);
        }
    }

    static void printRegionMetrics(Map<String, AggregateResult> groups) {
        System.out.println("\n=== Regional Aggregation ===");

        for (var entry : groups.entrySet()) {
            AggregateResult result = entry.getValue();

            System.out.printf(
                "%s | transactions=%d | units=%d | revenue=%.2f | " +
                "profit=%.2f | margin=%.2f%% | AOV=%.2f%n",
                entry.getKey(),
                result.transactions(),
                result.units(),
                result.revenue(),
                result.profit(),
                result.margin() * 100,
                result.averageOrderValue()
            );
        }
    }

    static void demonstrateInvalidState() {
        try {
            new Sale(
                9999, "2026-04-01", "North", Channel.ONLINE,
                Category.SOFTWARE, "CRM", CustomerSegment.ENTERPRISE,
                1, 100, 125, 0.05
            );
        } catch (IllegalArgumentException error) {
            System.out.println("\n=== Domain Validation Failure ===");
            System.out.println(error.getMessage());
        }
    }

    public static void main(String[] args) {
        List<Sale> sales = createSales();
        SalesAnalyticsService service = new SalesAnalyticsService(sales);

        System.out.println("GROUP BY: Segmenting and Aggregating Business Data");
        System.out.println("Validated " + sales.size() + " transactions.");

        printRegionMetrics(service.revenueByRegion());

        printRows(
            "Region + Category Aggregation",
            service.revenueByRegionAndCategory()
        );

        printRows(
            "Channel Aggregation",
            service.revenueByChannel()
        );

        printRows(
            "HAVING-Style High-Value Regions",
            service.highValueRegions(15000)
        );

        printRows(
            "Conditional Regional Metrics",
            service.conditionalRegionMetrics()
        );

        printRows(
            "Customer Segment Analysis",
            service.customerSegmentReport()
        );

        printRows(
            "Top Categories by Profit",
            service.topCategoriesByProfit(3)
        );

        printRows(
            "Quarterly Category Performance",
            service.quarterlyCategoryReport()
        );

        demonstrateInvalidState();

        System.out.println("\n=== Enterprise Design Characteristics ===");
        System.out.println(
            "Records provide immutable transaction state; enums constrain " +
            "business dimensions; groupingBy creates segment buckets; " +
            "downstream collectors derive aggregate metrics."
        );
        System.out.println(
            "Group-level filtering is deliberately performed after aggregation, " +
            "which distinguishes HAVING-style logic from row-level filtering."
        );
        System.out.println(
            "Hash-based grouping is generally O(n) expected time; ordered " +
            "TreeMap grouping trades some insertion performance for deterministic keys."
        );
    }
}
