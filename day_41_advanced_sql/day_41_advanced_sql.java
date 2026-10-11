import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Collectors;

/**
 * Enterprise order analytics using advanced SQL concepts represented as
 * explicit Java domain operations.
 *
 * Compile and run:
 *   javac AdvancedSqlEnterprise.java
 *   java AdvancedSqlEnterprise
 *
 * The model distinguishes row ranking, tie-aware ranking, cumulative totals,
 * latest-record selection, and query-shape validation.
 */
public class AdvancedSqlEnterprise {

    enum OrderStatus {
        PENDING, PAID, SHIPPED, DELIVERED, CANCELLED
    }

    record Customer(int id, String name, String region) {
        Customer {
            if (id <= 0) throw new IllegalArgumentException("Customer ID must be positive.");
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Customer name is required.");
            }
            if (region == null || region.isBlank()) {
                throw new IllegalArgumentException("Customer region is required.");
            }
        }
    }

    record Order(
            int id,
            int customerId,
            LocalDate orderDate,
            OrderStatus status,
            BigDecimal amount
    ) {
        Order {
            if (id <= 0 || customerId <= 0) {
                throw new IllegalArgumentException("Identifiers must be positive.");
            }
            Objects.requireNonNull(orderDate, "Order date is required.");
            Objects.requireNonNull(status, "Order status is required.");
            Objects.requireNonNull(amount, "Order amount is required.");
            if (amount.signum() < 0) {
                throw new IllegalArgumentException("Order amount cannot be negative.");
            }
            amount = amount.setScale(2, RoundingMode.HALF_UP);
        }
    }

    record RevenueRow(
            Customer customer,
            BigDecimal revenue,
            long orderCount,
            int rowNumber,
            int rank
    ) {}

    record DailyRevenue(
            LocalDate date,
            BigDecimal dailyRevenue,
            BigDecimal runningRevenue
    ) {}

    static final class OrderRepository {
        private final Map<Integer, Customer> customers = new LinkedHashMap<>();
        private final Map<Integer, Order> orders = new LinkedHashMap<>();

        void addCustomer(Customer customer) {
            Objects.requireNonNull(customer);
            if (customers.putIfAbsent(customer.id(), customer) != null) {
                throw new IllegalArgumentException("Duplicate customer ID.");
            }
        }

        void addOrder(Order order) {
            Objects.requireNonNull(order);
            if (!customers.containsKey(order.customerId())) {
                throw new IllegalArgumentException("Order references an unknown customer.");
            }
            if (orders.putIfAbsent(order.id(), order) != null) {
                throw new IllegalArgumentException("Duplicate order ID.");
            }
        }

        List<Customer> customers() {
            return List.copyOf(customers.values());
        }

        List<Order> orders() {
            return List.copyOf(orders.values());
        }
    }

    static final class AnalyticsService {
        private final OrderRepository repository;

        AnalyticsService(OrderRepository repository) {
            this.repository = Objects.requireNonNull(repository);
        }

        List<RevenueRow> regionalRanking() {
            Map<Integer, BigDecimal> revenueByCustomer = new HashMap<>();
            Map<Integer, Long> countByCustomer = new HashMap<>();

            for (Order order : repository.orders()) {
                if (order.status() == OrderStatus.CANCELLED) continue;

                revenueByCustomer.merge(
                        order.customerId(),
                        order.amount(),
                        BigDecimal::add
                );
                countByCustomer.merge(order.customerId(), 1L, Long::sum);
            }

            // Starting with the customer table preserves customers without
            // orders, matching the result semantics of a LEFT JOIN.
            List<Customer> sorted = repository.customers().stream()
                    .sorted(
                            Comparator.comparing(Customer::region)
                                    .thenComparing(
                                            (Customer c) -> revenueByCustomer.getOrDefault(
                                                    c.id(), BigDecimal.ZERO
                                            ),
                                            Comparator.reverseOrder()
                                    )
                                    .thenComparingInt(Customer::id)
                    )
                    .toList();

            List<RevenueRow> result = new ArrayList<>();
            String previousRegion = null;
            BigDecimal previousRevenue = null;
            int rowNumber = 0;
            int rank = 0;

            for (Customer customer : sorted) {
                BigDecimal revenue = revenueByCustomer.getOrDefault(
                        customer.id(), BigDecimal.ZERO
                );
                long count = countByCustomer.getOrDefault(customer.id(), 0L);

                if (!customer.region().equals(previousRegion)) {
                    previousRegion = customer.region();
                    previousRevenue = revenue;
                    rowNumber = 1;
                    rank = 1;
                } else {
                    rowNumber++;
                    // SQL RANK leaves gaps after ties; ROW_NUMBER never does.
                    if (revenue.compareTo(previousRevenue) != 0) {
                        rank = rowNumber;
                    }
                    previousRevenue = revenue;
                }

                result.add(new RevenueRow(customer, revenue, count, rowNumber, rank));
            }

            return List.copyOf(result);
        }

        List<DailyRevenue> cumulativeDailyRevenue() {
            Map<LocalDate, BigDecimal> byDate = new TreeMap<>();

            for (Order order : repository.orders()) {
                if (order.status() != OrderStatus.DELIVERED) continue;
                byDate.merge(order.orderDate(), order.amount(), BigDecimal::add);
            }

            BigDecimal running = BigDecimal.ZERO;
            List<DailyRevenue> result = new ArrayList<>();

            for (Map.Entry<LocalDate, BigDecimal> entry : byDate.entrySet()) {
                running = running.add(entry.getValue());
                result.add(new DailyRevenue(entry.getKey(), entry.getValue(), running));
            }

            return List.copyOf(result);
        }

        Optional<Order> latestOrder(int customerId) {
            if (!repository.customers().stream()
                    .anyMatch(customer -> customer.id() == customerId)) {
                throw new IllegalArgumentException("Unknown customer.");
            }

            return repository.orders().stream()
                    .filter(order -> order.customerId() == customerId)
                    .max(
                            Comparator.comparing(Order::orderDate)
                                    .thenComparingInt(Order::id)
                    );
        }

        Map<OrderStatus, BigDecimal> revenueByStatus() {
            Map<OrderStatus, BigDecimal> result = new LinkedHashMap<>();

            for (OrderStatus status : EnumSet.allOf(OrderStatus.class)) {
                BigDecimal total = repository.orders().stream()
                        .filter(order -> order.status() == status)
                        .map(Order::amount)
                        .reduce(BigDecimal.ZERO, BigDecimal::add);
                result.put(status, total);
            }

            return Map.copyOf(result);
        }
    }

    static final class QueryPolicy {
        private final Set<String> indexedColumns;

        QueryPolicy(Set<String> indexedColumns) {
            this.indexedColumns = Set.copyOf(indexedColumns);
        }

        void requireIndexForHighVolumeFilter(String column, boolean highVolume) {
            if (highVolume && !indexedColumns.contains(column)) {
                throw new IllegalStateException(
                        "High-volume filter lacks a configured index: " + column
                );
            }
        }

        void validateDateRange(LocalDate fromInclusive, LocalDate toExclusive) {
            if (fromInclusive == null || toExclusive == null) {
                throw new IllegalArgumentException("Date boundaries are required.");
            }
            if (!fromInclusive.isBefore(toExclusive)) {
                throw new IllegalArgumentException(
                        "Date range must be non-empty and half-open."
                );
            }
        }
    }

    private static Order order(
            int id, int customerId, String date, OrderStatus status, String amount
    ) {
        return new Order(
                id,
                customerId,
                LocalDate.parse(date),
                status,
                new BigDecimal(amount)
        );
    }

    public static void main(String[] args) {
        OrderRepository repository = new OrderRepository();

        repository.addCustomer(new Customer(201, "Riya Mehta", "North"));
        repository.addCustomer(new Customer(202, "Arjun Das", "South"));
        repository.addCustomer(new Customer(203, "Sara Khan", "West"));
        repository.addCustomer(new Customer(204, "Dev Patel", "North"));
        repository.addCustomer(new Customer(205, "Maya Iyer", "East"));
        repository.addCustomer(new Customer(206, "Noah Roy", "East"));

        repository.addOrder(order(
                7001, 201, "2026-01-05", OrderStatus.DELIVERED, "42000.00"
        ));
        repository.addOrder(order(
                7002, 201, "2026-01-18", OrderStatus.DELIVERED, "18000.00"
        ));
        repository.addOrder(order(
                7003, 202, "2026-01-19", OrderStatus.SHIPPED, "27000.00"
        ));
        repository.addOrder(order(
                7004, 202, "2026-02-02", OrderStatus.CANCELLED, "12000.00"
        ));
        repository.addOrder(order(
                7005, 203, "2026-02-12", OrderStatus.DELIVERED, "72000.00"
        ));
        repository.addOrder(order(
                7006, 204, "2026-02-21", OrderStatus.DELIVERED, "18000.00"
        ));
        repository.addOrder(order(
                7007, 201, "2026-03-07", OrderStatus.DELIVERED, "35000.00"
        ));
        repository.addOrder(order(
                7008, 205, "2026-03-14", OrderStatus.PENDING, "8000.00"
        ));
        repository.addOrder(order(
                7009, 203, "2026-03-19", OrderStatus.DELIVERED, "72000.00"
        ));

        AnalyticsService service = new AnalyticsService(repository);

        System.out.println("Regional revenue ranking");
        for (RevenueRow row : service.regionalRanking()) {
            System.out.printf(
                    "%-8s %-16s revenue=%10s count=%d rank=%d row=%d%n",
                    row.customer().region(),
                    row.customer().name(),
                    row.revenue().toPlainString(),
                    row.orderCount(),
                    row.rank(),
                    row.rowNumber()
            );
        }

        System.out.println("\nCumulative daily revenue");
        for (DailyRevenue row : service.cumulativeDailyRevenue()) {
            System.out.printf(
                    "%s daily=%s running=%s%n",
                    row.date(),
                    row.dailyRevenue().toPlainString(),
                    row.runningRevenue().toPlainString()
            );
        }

        System.out.println("\nLatest order for customer 201");
        service.latestOrder(201).ifPresentOrElse(
                order -> System.out.println(order.id() + " on " + order.orderDate()),
                () -> System.out.println("No order found")
        );

        System.out.println("\nRevenue by lifecycle state");
        service.revenueByStatus().forEach(
                (status, amount) -> System.out.println(status + ": " + amount)
        );

        QueryPolicy policy = new QueryPolicy(
                Set.of("orders.customer_id", "orders.order_date")
        );

        policy.requireIndexForHighVolumeFilter("orders.customer_id", true);
        policy.validateDateRange(
                LocalDate.parse("2026-01-01"),
                LocalDate.parse("2026-04-01")
        );

        try {
            policy.requireIndexForHighVolumeFilter("orders.status", true);
        } catch (IllegalStateException exception) {
            System.out.println("\nRejected query configuration: " + exception.getMessage());
        }

        try {
            policy.validateDateRange(
                    LocalDate.parse("2026-04-01"),
                    LocalDate.parse("2026-01-01")
            );
        } catch (IllegalArgumentException exception) {
            System.out.println("Rejected date range: " + exception.getMessage());
        }

        // BigDecimal prevents binary floating-point rounding errors in monetary
        // aggregation. A database still needs indexes, statistics, and plans
        // because this Java model does not reproduce a relational optimizer.
    }
}
