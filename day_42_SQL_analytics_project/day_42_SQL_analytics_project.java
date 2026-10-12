import java.time.LocalDate;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Collectors;

/*
 * Enterprise Retail Analytics
 *
 * Java 17+, standard library only.
 *
 * This implementation emphasizes domain modeling, immutable transaction
 * facts, validation, aggregation services, customer segmentation, product
 * profitability, and month-based forecasting.
 */
public class RetailAnalyticsEnterprise {

    enum PaymentMethod {
        CARD, UPI, CASH, BANK_TRANSFER, WALLET
    }

    enum CustomerSegment {
        HIGH_VALUE, REGULAR, OCCASIONAL
    }

    record Order(
        String orderId,
        LocalDate orderDate,
        String customerId,
        String region,
        String category,
        String product,
        int quantity,
        double unitPrice,
        double unitCost,
        double discount,
        PaymentMethod paymentMethod,
        boolean returned
    ) {
        Order {
            Objects.requireNonNull(orderDate, "orderDate");
            Objects.requireNonNull(paymentMethod, "paymentMethod");

            orderId = requireText(orderId, "orderId");
            customerId = requireText(customerId, "customerId");
            region = requireText(region, "region");
            category = requireText(category, "category");
            product = requireText(product, "product");

            if (quantity <= 0) {
                throw new IllegalArgumentException("quantity must be positive");
            }
            if (!Double.isFinite(unitPrice) || unitPrice < 0) {
                throw new IllegalArgumentException(
                    "unitPrice must be finite and non-negative"
                );
            }
            if (!Double.isFinite(unitCost) || unitCost < 0) {
                throw new IllegalArgumentException(
                    "unitCost must be finite and non-negative"
                );
            }
            if (!Double.isFinite(discount) || discount < 0 || discount > 1) {
                throw new IllegalArgumentException(
                    "discount must be between zero and one"
                );
            }
        }

        double grossSales() {
            return quantity * unitPrice;
        }

        double discountAmount() {
            return grossSales() * discount;
        }

        double revenue() {
            return returned ? 0.0 : grossSales() - discountAmount();
        }

        double cost() {
            return returned ? 0.0 : quantity * unitCost;
        }

        double profit() {
            return revenue() - cost();
        }

        YearMonth month() {
            return YearMonth.from(orderDate);
        }
    }

    record SalesMetrics(
        long transactionCount,
        long returnedCount,
        double grossSales,
        double discountAmount,
        double revenue,
        double cost,
        double profit
    ) {
        double profitMargin() {
            return revenue == 0.0 ? 0.0 : profit / revenue;
        }

        double averageRevenuePerTransaction() {
            return transactionCount == 0 ? 0.0 : revenue / transactionCount;
        }
    }

    record CustomerProfile(
        String customerId,
        LocalDate firstPurchase,
        LocalDate lastPurchase,
        long transactionCount,
        double lifetimeRevenue,
        double lifetimeProfit,
        Set<String> purchasedProducts,
        CustomerSegment segment
    ) {}

    record ProductPerformance(
        String product,
        long unitsSold,
        double revenue,
        double profit,
        double profitMargin
    ) {}

    record ForecastPoint(
        YearMonth month,
        double forecastRevenue,
        String method
    ) {}

    interface AnalyticsPolicy {
        CustomerSegment classify(double lifetimeRevenue);
    }

    static final class DefaultCustomerPolicy implements AnalyticsPolicy {
        @Override
        public CustomerSegment classify(double lifetimeRevenue) {
            if (lifetimeRevenue >= 1500.0) {
                return CustomerSegment.HIGH_VALUE;
            }
            if (lifetimeRevenue >= 400.0) {
                return CustomerSegment.REGULAR;
            }
            return CustomerSegment.OCCASIONAL;
        }
    }

    static final class AnalyticsService {
        private final List<Order> orders;
        private final AnalyticsPolicy customerPolicy;

        AnalyticsService(List<Order> input, AnalyticsPolicy customerPolicy) {
            Objects.requireNonNull(input, "input");
            this.customerPolicy = Objects.requireNonNull(
                customerPolicy, "customerPolicy"
            );

            Set<String> identifiers = new HashSet<>();
            List<Order> validated = new ArrayList<>();

            for (Order order : input) {
                Objects.requireNonNull(order, "order cannot be null");

                // Duplicate business keys are rejected to prevent double counting.
                if (!identifiers.add(order.orderId())) {
                    throw new IllegalArgumentException(
                        "Duplicate order identifier: " + order.orderId()
                    );
                }
                validated.add(order);
            }

            this.orders = List.copyOf(validated);
        }

        SalesMetrics summarize(List<Order> selected) {
            long returned = selected.stream().filter(Order::returned).count();

            double gross = selected.stream()
                .mapToDouble(Order::grossSales)
                .sum();

            double discounts = selected.stream()
                .mapToDouble(Order::discountAmount)
                .sum();

            double revenue = selected.stream()
                .mapToDouble(Order::revenue)
                .sum();

            double cost = selected.stream()
                .mapToDouble(Order::cost)
                .sum();

            return new SalesMetrics(
                selected.size(),
                returned,
                gross,
                discounts,
                revenue,
                cost,
                revenue - cost
            );
        }

        SalesMetrics overall() {
            return summarize(orders);
        }

        Map<String, SalesMetrics> byRegion() {
            Map<String, List<Order>> grouped = orders.stream()
                .collect(Collectors.groupingBy(
                    Order::region,
                    TreeMap::new,
                    Collectors.toList()
                ));

            Map<String, SalesMetrics> results = new LinkedHashMap<>();
            grouped.forEach((region, group) ->
                results.put(region, summarize(group))
            );
            return results;
        }

        Map<YearMonth, SalesMetrics> byMonth() {
            Map<YearMonth, List<Order>> grouped = orders.stream()
                .collect(Collectors.groupingBy(
                    Order::month,
                    TreeMap::new,
                    Collectors.toList()
                ));

            Map<YearMonth, SalesMetrics> results = new TreeMap<>();
            grouped.forEach((month, group) ->
                results.put(month, summarize(group))
            );
            return results;
        }

        List<CustomerProfile> customerProfiles() {
            Map<String, List<Order>> grouped = orders.stream()
                .collect(Collectors.groupingBy(Order::customerId));

            List<CustomerProfile> results = new ArrayList<>();

            grouped.forEach((customerId, customerOrders) -> {
                LocalDate first = customerOrders.stream()
                    .map(Order::orderDate)
                    .min(LocalDate::compareTo)
                    .orElseThrow();

                LocalDate last = customerOrders.stream()
                    .map(Order::orderDate)
                    .max(LocalDate::compareTo)
                    .orElseThrow();

                double revenue = customerOrders.stream()
                    .mapToDouble(Order::revenue)
                    .sum();

                double profit = customerOrders.stream()
                    .mapToDouble(Order::profit)
                    .sum();

                Set<String> products = customerOrders.stream()
                    .filter(order -> !order.returned())
                    .map(Order::product)
                    .collect(Collectors.toUnmodifiableSet());

                results.add(new CustomerProfile(
                    customerId,
                    first,
                    last,
                    customerOrders.size(),
                    revenue,
                    profit,
                    products,
                    customerPolicy.classify(revenue)
                ));
            });

            results.sort(
                Comparator.comparingDouble(CustomerProfile::lifetimeRevenue)
                    .reversed()
                    .thenComparing(CustomerProfile::customerId)
            );

            return List.copyOf(results);
        }

        List<ProductPerformance> productRanking() {
            Map<String, List<Order>> grouped = orders.stream()
                .collect(Collectors.groupingBy(Order::product));

            List<ProductPerformance> results = new ArrayList<>();

            grouped.forEach((product, productOrders) -> {
                long units = productOrders.stream()
                    .filter(order -> !order.returned())
                    .mapToLong(Order::quantity)
                    .sum();

                double revenue = productOrders.stream()
                    .mapToDouble(Order::revenue)
                    .sum();

                double profit = productOrders.stream()
                    .mapToDouble(Order::profit)
                    .sum();

                results.add(new ProductPerformance(
                    product,
                    units,
                    revenue,
                    profit,
                    revenue == 0.0 ? 0.0 : profit / revenue
                ));
            });

            results.sort(
                Comparator.comparingDouble(ProductPerformance::profit)
                    .reversed()
                    .thenComparing(ProductPerformance::product)
            );

            return List.copyOf(results);
        }

        List<ForecastPoint> forecast(int horizon) {
            if (horizon < 1 || horizon > 24) {
                throw new IllegalArgumentException(
                    "Forecast horizon must be between 1 and 24"
                );
            }

            Map<YearMonth, SalesMetrics> monthly = byMonth();
            if (monthly.isEmpty()) return List.of();

            List<Double> history = new ArrayList<>();
            monthly.values().forEach(
                metrics -> history.add(metrics.revenue())
            );

            YearMonth current = monthly.keySet().stream()
                .max(YearMonth::compareTo)
                .orElseThrow();

            List<ForecastPoint> results = new ArrayList<>();

            for (int step = 0; step < horizon; step++) {
                int start = Math.max(0, history.size() - 3);
                double total = 0.0;

                for (int index = start; index < history.size(); index++) {
                    total += history.get(index);
                }

                double prediction = total / (history.size() - start);
                current = current.plusMonths(1);

                results.add(new ForecastPoint(
                    current,
                    prediction,
                    "Three-month moving average"
                ));

                history.add(prediction);
            }

            return List.copyOf(results);
        }

        List<Order> negativeMarginCandidates() {
            return orders.stream()
                .filter(order -> !order.returned())
                .filter(order -> order.profit() < 0.0)
                .sorted(Comparator.comparingDouble(Order::profit))
                .toList();
        }
    }

    private static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(field + " cannot be blank");
        }
        return value.trim();
    }

    private static List<Order> sampleOrders() {
        return List.of(
            new Order("ORD-1001", LocalDate.parse("2025-01-05"),
                "C-101", "North", "Electronics", "Laptop",
                2, 850, 610, 0.05, PaymentMethod.CARD, false),
            new Order("ORD-1002", LocalDate.parse("2025-01-12"),
                "C-102", "South", "Furniture", "Office Chair",
                3, 190, 118, 0.10, PaymentMethod.UPI, false),
            new Order("ORD-1003", LocalDate.parse("2025-02-03"),
                "C-101", "North", "Electronics", "Monitor",
                4, 260, 175, 0.0, PaymentMethod.CARD, false),
            new Order("ORD-1004", LocalDate.parse("2025-02-18"),
                "C-103", "East", "Stationery", "Notebook Pack",
                20, 12, 4, 0.15, PaymentMethod.CASH, false),
            new Order("ORD-1005", LocalDate.parse("2025-03-01"),
                "C-104", "West", "Furniture", "Desk",
                1, 320, 220, 0.05, PaymentMethod.BANK_TRANSFER, true),
            new Order("ORD-1006", LocalDate.parse("2025-03-20"),
                "C-102", "South", "Electronics", "Laptop",
                1, 850, 610, 0.0, PaymentMethod.CARD, false),
            new Order("ORD-1007", LocalDate.parse("2025-04-07"),
                "C-105", "Central", "Accessories", "Backpack",
                5, 55, 24, 0.10, PaymentMethod.WALLET, false),
            new Order("ORD-1008", LocalDate.parse("2025-04-22"),
                "C-106", "North", "Electronics", "Laptop",
                15, 850, 610, 0.0, PaymentMethod.CARD, false),
            new Order("ORD-1009", LocalDate.parse("2025-05-08"),
                "C-107", "East", "Furniture", "Office Chair",
                2, 190, 118, 0.20, PaymentMethod.UPI, false),
            new Order("ORD-1010", LocalDate.parse("2025-06-11"),
                "C-108", "West", "Accessories", "USB Hub",
                10, 28, 11, 0.10, PaymentMethod.CASH, false)
        );
    }

    public static void main(String[] args) {
        try {
            AnalyticsService service = new AnalyticsService(
                sampleOrders(),
                new DefaultCustomerPolicy()
            );

            SalesMetrics overall = service.overall();

            System.out.println("ENTERPRISE RETAIL ANALYTICS");
            System.out.println("Transactions: " + overall.transactionCount());
            System.out.printf("Gross sales: %.2f%n", overall.grossSales());
            System.out.printf("Discounts: %.2f%n", overall.discountAmount());
            System.out.printf("Recognized revenue: %.2f%n", overall.revenue());
            System.out.printf("Recognized cost: %.2f%n", overall.cost());
            System.out.printf("Profit: %.2f%n", overall.profit());
            System.out.printf("Profit margin: %.2f%%%n",
                overall.profitMargin() * 100.0);

            System.out.println("\nREGIONAL PERFORMANCE");
            service.byRegion().forEach((region, metrics) ->
                System.out.printf(
                    "%s | Revenue %.2f | Profit %.2f | Margin %.2f%%%n",
                    region,
                    metrics.revenue(),
                    metrics.profit(),
                    metrics.profitMargin() * 100.0
                )
            );

            System.out.println("\nCUSTOMER SEGMENTS");
            service.customerProfiles().stream()
                .limit(8)
                .forEach(customer -> System.out.printf(
                    "%s | %s | Revenue %.2f | Transactions %d%n",
                    customer.customerId(),
                    customer.segment(),
                    customer.lifetimeRevenue(),
                    customer.transactionCount()
                ));

            System.out.println("\nPRODUCT PROFITABILITY");
            service.productRanking().forEach(product ->
                System.out.printf(
                    "%s | Units %d | Profit %.2f | Margin %.2f%%%n",
                    product.product(),
                    product.unitsSold(),
                    product.profit(),
                    product.profitMargin() * 100.0
                )
            );

            System.out.println("\nMONTHLY FORECAST");
            service.forecast(3).forEach(point ->
                System.out.printf(
                    "%s | Forecast %.2f | %s%n",
                    point.month(),
                    point.forecastRevenue(),
                    point.method()
                )
            );

            // Invalid transitions in the data pipeline fail explicitly.
            try {
                new Order(
                    "BAD-1", LocalDate.parse("2025-01-01"),
                    "C-1", "North", "Electronics", "Laptop",
                    -1, 850, 610, 0.05, PaymentMethod.CARD, false
                );
            } catch (IllegalArgumentException error) {
                System.out.println("\nValidation rejected invalid order: "
                    + error.getMessage());
            }

            try {
                new AnalyticsService(
                    List.of(sampleOrders().get(0), sampleOrders().get(0)),
                    new DefaultCustomerPolicy()
                );
            } catch (IllegalArgumentException error) {
                System.out.println("Duplicate detection: " + error.getMessage());
            }
        } catch (RuntimeException error) {
            System.err.println("Analytics execution failed: " + error.getMessage());
            System.exitCode = 1;
        }
    }
}
