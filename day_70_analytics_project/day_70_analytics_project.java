/*
 * ENTERPRISE BUSINESS ANALYTICS PLATFORM
 *
 * Java version: 17
 * Scenario: Retail business intelligence and financial performance.
 *
 * Features:
 * - Immutable transaction records
 * - Domain-level validation
 * - Transaction processing service
 * - Financial KPI calculation
 * - Customer segmentation
 * - Regional and product performance
 * - Monthly forecasting
 * - Business policy evaluation
 * - Exception-based failure handling
 *
 * Compile:
 * javac BusinessAnalytics.java
 *
 * Run:
 * java BusinessAnalytics
 */

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Collectors;

public class BusinessAnalytics {

    enum Segment {
        HIGH_VALUE,
        REGULAR,
        OCCASIONAL,
        AT_RISK
    }

    enum Severity {
        LOW,
        MEDIUM,
        HIGH
    }

    enum TransactionState {
        RECEIVED,
        VALIDATED,
        PROCESSED,
        REJECTED
    }

    record Transaction(
        String id,
        LocalDate date,
        String customerId,
        String productId,
        String category,
        String region,
        int quantity,
        double unitPrice,
        double unitCost
    ) {
        Transaction {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException(
                    "Transaction ID is required."
                );
            }

            if (date == null ||
                customerId == null || customerId.isBlank() ||
                productId == null || productId.isBlank()) {
                throw new IllegalArgumentException(
                    "Transaction identity and date are required."
                );
            }

            if (category == null || category.isBlank() ||
                region == null || region.isBlank()) {
                throw new IllegalArgumentException(
                    "Category and region are required."
                );
            }

            if (quantity <= 0 ||
                !Double.isFinite(unitPrice) ||
                !Double.isFinite(unitCost) ||
                unitPrice <= 0 ||
                unitCost < 0 ||
                unitCost > unitPrice) {
                throw new IllegalArgumentException(
                    "Invalid quantity or financial values."
                );
            }
        }

        double revenue() {
            return quantity * unitPrice;
        }

        double cost() {
            return quantity * unitCost;
        }

        double profit() {
            return revenue() - cost();
        }
    }

    record BusinessMetrics(
        int transactionCount,
        double revenue,
        double cost,
        double profit,
        double marginPercent,
        double averageOrderValue,
        int customerCount,
        int repeatCustomers,
        double repeatRate
    ) {}

    record Policy(
        double minimumMargin,
        double minimumRepeatRate,
        int minimumRequiredTransactions
    ) {
        Policy {
            if (!Double.isFinite(minimumMargin) ||
                !Double.isFinite(minimumRepeatRate) ||
                minimumMargin < 0 ||
                minimumRepeatRate < 0 ||
                minimumRepeatRate > 100 ||
                minimumRequiredTransactions < 1) {
                throw new IllegalArgumentException(
                    "Invalid business policy configuration."
                );
            }
        }
    }

    record Finding(
        Severity severity,
        String code,
        String description
    ) {}

    record CustomerProfile(
        String customerId,
        int frequency,
        double monetaryValue,
        int recencyDays,
        Segment segment
    ) {}

    static class Aggregate {
        double revenue;
        double profit;
        int units;
        int transactions;

        void add(Transaction transaction) {
            revenue += transaction.revenue();
            profit += transaction.profit();
            units += transaction.quantity();
            transactions++;
        }
    }

    static class CustomerState {
        int frequency;
        double monetaryValue;
        LocalDate lastPurchase;
    }

    static class AnalyticsException extends RuntimeException {
        AnalyticsException(String message) {
            super(message);
        }
    }

    interface Reportable {
        Map<String, Object> generateReport();
    }

    static class AnalyticsService implements Reportable {

        private final Map<String, Transaction> transactions =
            new HashMap<>();

        private final Map<String, Aggregate> categories =
            new HashMap<>();

        private final Map<String, Aggregate> regions =
            new HashMap<>();

        private final Map<String, Aggregate> products =
            new HashMap<>();

        private final Map<String, CustomerState> customers =
            new HashMap<>();

        private final Map<String, Aggregate> monthly =
            new TreeMap<>();

        private final Policy policy;

        AnalyticsService(Policy policy) {
            this.policy = policy;
        }

        void process(Transaction transaction) {
            if (transactions.containsKey(transaction.id())) {
                throw new AnalyticsException(
                    "Duplicate transaction: " + transaction.id()
                );
            }

            // Validate before mutating the analytical state.
            transactions.put(transaction.id(), transaction);

            categories.computeIfAbsent(
                transaction.category(),
                key -> new Aggregate()
            ).add(transaction);

            regions.computeIfAbsent(
                transaction.region(),
                key -> new Aggregate()
            ).add(transaction);

            products.computeIfAbsent(
                transaction.productId(),
                key -> new Aggregate()
            ).add(transaction);

            String month = transaction.date()
                .toString().substring(0, 7);

            monthly.computeIfAbsent(
                month,
                key -> new Aggregate()
            ).add(transaction);

            CustomerState customer = customers.computeIfAbsent(
                transaction.customerId(),
                key -> new CustomerState()
            );

            customer.frequency++;
            customer.monetaryValue += transaction.revenue();

            if (customer.lastPurchase == null ||
                transaction.date().isAfter(customer.lastPurchase)) {
                customer.lastPurchase = transaction.date();
            }
        }

        BusinessMetrics calculateMetrics() {
            double revenue = transactions.values().stream()
                .mapToDouble(Transaction::revenue)
                .sum();

            double cost = transactions.values().stream()
                .mapToDouble(Transaction::cost)
                .sum();

            double profit = revenue - cost;

            int repeat = (int) customers.values().stream()
                .filter(customer -> customer.frequency > 1)
                .count();

            int customerCount = customers.size();

            return new BusinessMetrics(
                transactions.size(),
                revenue,
                cost,
                profit,
                revenue > 0 ? profit / revenue * 100 : 0,
                transactions.isEmpty()
                    ? 0
                    : revenue / transactions.size(),
                customerCount,
                repeat,
                customerCount > 0
                    ? repeat * 100.0 / customerCount
                    : 0
            );
        }

        List<CustomerProfile> segmentCustomers() {
            if (customers.isEmpty()) {
                return List.of();
            }

            LocalDate referenceDate = customers.values().stream()
                .map(customer -> customer.lastPurchase)
                .max(LocalDate::compareTo)
                .orElseThrow();

            return customers.entrySet().stream()
                .map(entry -> {
                    CustomerState state = entry.getValue();

                    int recency = (int) ChronoUnit.DAYS.between(
                        state.lastPurchase,
                        referenceDate
                    );

                    Segment segment;

                    if (state.frequency >= 5 &&
                        state.monetaryValue >= 50000 &&
                        recency <= 90) {
                        segment = Segment.HIGH_VALUE;
                    } else if (
                        state.frequency >= 3 && recency <= 180
                    ) {
                        segment = Segment.REGULAR;
                    } else if (recency > 180) {
                        segment = Segment.AT_RISK;
                    } else {
                        segment = Segment.OCCASIONAL;
                    }

                    return new CustomerProfile(
                        entry.getKey(),
                        state.frequency,
                        state.monetaryValue,
                        recency,
                        segment
                    );
                })
                .sorted(
                    Comparator.comparing(
                        CustomerProfile::monetaryValue
                    ).reversed()
                )
                .toList();
        }

        Map<String, Double> forecastRevenue() {
            List<Double> values = monthly.values().stream()
                .map(aggregate -> aggregate.revenue)
                .toList();

            if (values.isEmpty()) {
                return Map.of(
                    "slope", 0.0,
                    "nextPeriodRevenue", 0.0
                );
            }

            if (values.size() == 1) {
                return Map.of(
                    "slope", 0.0,
                    "nextPeriodRevenue", values.get(0)
                );
            }

            int n = values.size();

            double xMean = (n - 1) / 2.0;
            double yMean = values.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElse(0);

            double numerator = 0;
            double denominator = 0;

            for (int i = 0; i < n; i++) {
                numerator += (i - xMean) * (values.get(i) - yMean);
                denominator += Math.pow(i - xMean, 2);
            }

            double slope = denominator > 0
                ? numerator / denominator
                : 0;

            double forecast = Math.max(
                0,
                yMean + slope * (n - xMean)
            );

            return Map.of(
                "slope", slope,
                "nextPeriodRevenue", forecast
            );
        }

        List<Finding> evaluatePolicy(BusinessMetrics metrics) {
            List<Finding> findings = new ArrayList<>();

            if (metrics.transactionCount() <
                policy.minimumRequiredTransactions()) {
                findings.add(new Finding(
                    Severity.HIGH,
                    "INSUFFICIENT_DATA",
                    "Transaction volume is below the reporting threshold."
                ));
            }

            if (metrics.marginPercent() < policy.minimumMargin()) {
                findings.add(new Finding(
                    Severity.HIGH,
                    "LOW_MARGIN",
                    "Gross margin is below the configured target."
                ));
            }

            if (metrics.repeatRate() < policy.minimumRepeatRate()) {
                findings.add(new Finding(
                    Severity.MEDIUM,
                    "LOW_RETENTION",
                    "Customer repeat rate is below the configured target."
                ));
            }

            return List.copyOf(findings);
        }

        private Map<String, Map<String, Object>> summarize(
            Map<String, Aggregate> source
        ) {
            return source.entrySet().stream()
                .sorted(
                    Map.Entry.<String, Aggregate>comparingByValue(
                        Comparator.comparingDouble(
                            aggregate -> aggregate.revenue
                        )
                    ).reversed()
                )
                .collect(Collectors.toMap(
                    Map.Entry::getKey,
                    entry -> {
                        Aggregate aggregate = entry.getValue();

                        return Map.of(
                            "revenue", aggregate.revenue,
                            "profit", aggregate.profit,
                            "units", aggregate.units,
                            "transactions", aggregate.transactions
                        );
                    },
                    (first, second) -> first,
                    java.util.LinkedHashMap::new
                ));
        }

        @Override
        public Map<String, Object> generateReport() {
            if (transactions.isEmpty()) {
                throw new AnalyticsException(
                    "No transactions available for reporting."
                );
            }

            BusinessMetrics metrics = calculateMetrics();

            Map<String, Object> report = new java.util.LinkedHashMap<>();

            report.put("currency", "INR");
            report.put("metrics", metrics);
            report.put("categoryPerformance", summarize(categories));
            report.put("regionalPerformance", summarize(regions));
            report.put("productPerformance", summarize(products));
            report.put("customerSegments", segmentCustomers());
            report.put("monthlyPerformance", summarize(monthly));
            report.put("revenueForecast", forecastRevenue());
            report.put("policyFindings", evaluatePolicy(metrics));

            return report;
        }
    }

    static List<Transaction> sampleData() {
        List<Transaction> transactions = new ArrayList<>();

        String[] categories = {
            "Electronics", "Furniture", "Clothing", "Groceries"
        };

        String[] regions = {
            "North", "South", "East", "West", "Central"
        };

        double[] prices = {25000, 18000, 2500, 900};
        double[] costs = {18000, 12000, 1200, 650};

        for (int i = 1; i <= 300; i++) {
            int productIndex = i % 4;
            int month = ((i - 1) / 25) % 12 + 1;
            int day = (i % 28) + 1;

            LocalDate date = LocalDate.of(2025, month, day);

            transactions.add(new Transaction(
                String.format("TXN%05d", i),
                date,
                String.format("C%04d", (i % 80) + 1),
                "P00" + (productIndex + 1),
                categories[productIndex],
                regions[i % regions.length],
                (i % 5) + 1,
                prices[productIndex],
                costs[productIndex]
            ));
        }

        return transactions;
    }

    static void runTests() {
        Policy policy = new Policy(20, 30, 1);
        AnalyticsService service = new AnalyticsService(policy);

        Transaction transaction = new Transaction(
            "TEST001",
            LocalDate.of(2025, 1, 1),
            "C001",
            "P001",
            "Electronics",
            "North",
            2,
            1000,
            600
        );

        service.process(transaction);

        BusinessMetrics metrics = service.calculateMetrics();

        if (metrics.revenue() != 2000 ||
            metrics.profit() != 800) {
            throw new AnalyticsException(
                "Financial calculation test failed."
            );
        }

        boolean duplicateRejected = false;

        try {
            service.process(transaction);
        } catch (AnalyticsException exception) {
            duplicateRejected = true;
        }

        if (!duplicateRejected) {
            throw new AnalyticsException(
                "Duplicate transaction test failed."
            );
        }

        System.out.println("All Java validation tests passed.");
    }

    public static void main(String[] args) {
        try {
            runTests();

            Policy policy = new Policy(
                20.0,
                30.0,
                10
            );

            AnalyticsService service = new AnalyticsService(policy);

            sampleData().forEach(service::process);

            Map<String, Object> report = service.generateReport();

            BusinessMetrics metrics =
                (BusinessMetrics) report.get("metrics");

            System.out.println("\nENTERPRISE BUSINESS ANALYTICS");
            System.out.println("================================");

            System.out.printf(
                "Transactions: %d%n",
                metrics.transactionCount()
            );

            System.out.printf(
                "Revenue: INR %.2f%n",
                metrics.revenue()
            );

            System.out.printf(
                "Gross Profit: INR %.2f%n",
                metrics.profit()
            );

            System.out.printf(
                "Gross Margin: %.2f%%%n",
                metrics.marginPercent()
            );

            System.out.printf(
                "Average Order Value: INR %.2f%n",
                metrics.averageOrderValue()
            );

            System.out.printf(
                "Unique Customers: %d%n",
                metrics.customerCount()
            );

            System.out.printf(
                "Repeat Customer Rate: %.2f%%%n",
                metrics.repeatRate()
            );

            System.out.println("\nCATEGORY PERFORMANCE");
            System.out.println(report.get("categoryPerformance"));

            System.out.println("\nREGIONAL PERFORMANCE");
            System.out.println(report.get("regionalPerformance"));

            System.out.println("\nCUSTOMER SEGMENTATION");
            System.out.println(report.get("customerSegments"));

            System.out.println("\nREVENUE FORECAST");
            System.out.println(report.get("revenueForecast"));

            System.out.println("\nPOLICY FINDINGS");
            System.out.println(report.get("policyFindings"));

        } catch (RuntimeException exception) {
            System.err.println(
                "Business analytics failure: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
