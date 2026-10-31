import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;

public class BusinessAnalytics {

    enum CustomerSegment {
        HIGH_VALUE,
        GROWTH,
        AT_RISK,
        STANDARD
    }

    record SalesRecord(
            String orderId,
            String orderDate,
            String region,
            String salesperson,
            String customer,
            String product,
            int units,
            double unitPrice,
            double discountRate,
            double costPerUnit) {

        SalesRecord {
            Objects.requireNonNull(orderId);
            Objects.requireNonNull(orderDate);
            Objects.requireNonNull(region);
            Objects.requireNonNull(customer);
            Objects.requireNonNull(product);

            if (orderId.isBlank()) {
                throw new ValidationException("Order ID is required.");
            }
            if (units <= 0) {
                throw new ValidationException(orderId + ": units must be positive.");
            }
            if (unitPrice < 0 || costPerUnit < 0) {
                throw new ValidationException(orderId + ": prices cannot be negative.");
            }
            if (discountRate < 0 || discountRate > 1) {
                throw new ValidationException(orderId + ": invalid discount.");
            }
            if (costPerUnit > unitPrice) {
                throw new ValidationException(orderId + ": cost exceeds price.");
            }
        }

        double netSales() {
            return units * unitPrice * (1 - discountRate);
        }

        double profit() {
            return netSales() - units * costPerUnit;
        }

        double margin() {
            return netSales() == 0 ? 0 : profit() / netSales();
        }
    }

    static class ValidationException extends RuntimeException {
        ValidationException(String message) {
            super(message);
        }
    }

    static final class AnalyticsService {
        private final List<SalesRecord> records;

        AnalyticsService(List<SalesRecord> records) {
            if (records.isEmpty()) {
                throw new ValidationException("Dataset cannot be empty.");
            }

            long uniqueOrders = records.stream()
                    .map(SalesRecord::orderId)
                    .distinct()
                    .count();

            if (uniqueOrders != records.size()) {
                throw new ValidationException("Duplicate order ID detected.");
            }

            this.records = List.copyOf(records);
        }

        double totalSales() {
            return records.stream()
                    .mapToDouble(SalesRecord::netSales)
                    .sum();
        }

        double totalProfit() {
            return records.stream()
                    .mapToDouble(SalesRecord::profit)
                    .sum();
        }

        Map<String, Double> aggregate(
                Function<SalesRecord, String> key,
                Function<SalesRecord, Double> value) {

            return records.stream()
                    .collect(Collectors.groupingBy(
                            key,
                            LinkedHashMap::new,
                            Collectors.summingDouble(value::apply)));
        }

        Map<String, CustomerSegment> classifyCustomers() {
            Map<String, List<SalesRecord>> groups = records.stream()
                    .collect(Collectors.groupingBy(SalesRecord::customer));

            Map<String, CustomerSegment> result = new LinkedHashMap<>();

            for (Map.Entry<String, List<SalesRecord>> entry : groups.entrySet()) {
                double revenue = entry.getValue().stream()
                        .mapToDouble(SalesRecord::netSales)
                        .sum();

                double profit = entry.getValue().stream()
                        .mapToDouble(SalesRecord::profit)
                        .sum();

                double margin = revenue == 0 ? 0 : profit / revenue;

                CustomerSegment segment;
                if (revenue >= 15000 && margin >= 0.30) {
                    segment = CustomerSegment.HIGH_VALUE;
                } else if (revenue >= 10000) {
                    segment = CustomerSegment.GROWTH;
                } else if (margin < 0.25) {
                    segment = CustomerSegment.AT_RISK;
                } else {
                    segment = CustomerSegment.STANDARD;
                }

                result.put(entry.getKey(), segment);
            }

            return Collections.unmodifiableMap(result);
        }

        void validateFinancialInvariants() {
            records.forEach(record -> {
                if (record.netSales() < 0) {
                    throw new ValidationException(
                            record.orderId() + ": negative net sales."
                    );
                }

                if (record.margin() > 1) {
                    throw new ValidationException(
                            record.orderId() + ": invalid margin."
                    );
                }
            });
        }
    }

    private static List<SalesRecord> sampleData() {
        List<SalesRecord> records = new ArrayList<>();

        records.add(new SalesRecord("O1001", "2026-01-05", "North", "Asha",
                "Acme", "Analytics", 12, 850, .05, 510));
        records.add(new SalesRecord("O1002", "2026-01-09", "South", "Ravi",
                "Beta", "Automation", 8, 1200, .10, 720));
        records.add(new SalesRecord("O1003", "2026-01-15", "North", "Asha",
                "Delta", "Analytics", 5, 850, 0, 510));
        records.add(new SalesRecord("O1004", "2026-02-03", "West", "Neha",
                "Acme", "Security", 15, 700, .08, 420));
        records.add(new SalesRecord("O1005", "2026-02-11", "South", "Ravi",
                "Gamma", "Analytics", 20, 850, .12, 510));
        records.add(new SalesRecord("O1006", "2026-02-19", "West", "Neha",
                "Delta", "Automation", 7, 1200, .05, 720));
        records.add(new SalesRecord("O1007", "2026-03-02", "North", "Asha",
                "Beta", "Security", 10, 700, .03, 420));
        records.add(new SalesRecord("O1008", "2026-03-12", "South", "Ravi",
                "Acme", "Analytics", 16, 850, .07, 510));
        records.add(new SalesRecord("O1009", "2026-03-20", "West", "Neha",
                "Gamma", "Security", 6, 700, .15, 420));
        records.add(new SalesRecord("O1010", "2026-03-25", "North", "Asha",
                "Delta", "Automation", 11, 1200, .06, 720));

        return records;
    }

    public static void main(String[] args) {
        try {
            AnalyticsService service = new AnalyticsService(sampleData());
            service.validateFinancialInvariants();

            double sales = service.totalSales();
            double profit = service.totalProfit();

            System.out.println("BUSINESS ANALYTICS REPORT");
            System.out.println("=========================");
            System.out.printf("Orders:       %d%n", sampleData().size());
            System.out.printf("Net sales:    $%,.2f%n", sales);
            System.out.printf("Profit:       $%,.2f%n", profit);
            System.out.printf("Margin:       %.2f%%%n", 100 * profit / sales);

            System.out.println("\nSales by region");
            service.aggregate(
                    SalesRecord::region,
                    SalesRecord::netSales
            ).forEach((region, value) ->
                    System.out.printf("  %s: $%,.2f%n", region, value));

            System.out.println("\nProfit by product");
            service.aggregate(
                    SalesRecord::product,
                    SalesRecord::profit
            ).forEach((product, value) ->
                    System.out.printf("  %s: $%,.2f%n", product, value));

            System.out.println("\nCustomer segments");
            service.classifyCustomers().forEach((customer, segment) ->
                    System.out.printf("  %s: %s%n", customer, segment));

            System.out.println("\nValidation: passed");
        } catch (ValidationException error) {
            System.err.println("Analytics validation failed: " + error.getMessage());
            System.exit(1);
        }
    }
}
