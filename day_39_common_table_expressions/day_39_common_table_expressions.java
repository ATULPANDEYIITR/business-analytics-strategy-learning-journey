import java.math.BigDecimal;
import java.math.RoundingMode;
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
import java.util.function.Function;
import java.util.stream.Collectors;

/*
 * Enterprise analytical service demonstrating CTE-inspired query stages.
 *
 * Scenario: a finance team evaluates recognized sales, account profitability,
 * revenue concentration, and monthly changes before publishing a report.
 *
 * Compile: javac CteEnterpriseAnalytics.java
 * Run:     java CteEnterpriseAnalytics
 */
public class CteEnterpriseAnalytics {

    enum OrderStatus {
        COMPLETED, CANCELLED, REFUNDED, PENDING
    }

    record Sale(
            long orderId,
            String account,
            String region,
            String month,
            String product,
            int quantity,
            BigDecimal unitPrice,
            BigDecimal unitCost,
            OrderStatus status) {

        Sale {
            if (orderId <= 0) {
                throw new IllegalArgumentException("Order ID must be positive.");
            }
            account = requireText(account, "account");
            region = requireText(region, "region");
            month = requireText(month, "month");
            product = requireText(product, "product");
            if (!month.matches("\\d{4}-\\d{2}")) {
                throw new IllegalArgumentException("Month must use YYYY-MM format.");
            }
            if (quantity <= 0) {
                throw new IllegalArgumentException("Quantity must be positive.");
            }
            Objects.requireNonNull(unitPrice, "unitPrice");
            Objects.requireNonNull(unitCost, "unitCost");
            Objects.requireNonNull(status, "status");
            if (unitPrice.signum() < 0 || unitCost.signum() < 0) {
                throw new IllegalArgumentException("Prices and costs cannot be negative.");
            }
        }

        BigDecimal revenue() {
            return unitPrice.multiply(BigDecimal.valueOf(quantity));
        }

        BigDecimal grossProfit() {
            return unitPrice.subtract(unitCost)
                    .multiply(BigDecimal.valueOf(quantity));
        }
    }

    record MonthlyMetric(
            String month,
            BigDecimal revenue,
            BigDecimal grossProfit,
            int orderCount) {}

    record AccountMetric(
            String account,
            String region,
            BigDecimal revenue,
            BigDecimal grossProfit,
            int distinctOrders) {}

    record GrowthMetric(
            String month,
            BigDecimal revenue,
            BigDecimal previousRevenue,
            BigDecimal absoluteChange,
            BigDecimal percentageChange) {}

    private static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(field + " is required.");
        }
        return value;
    }

    private static BigDecimal money(BigDecimal value) {
        return value.setScale(2, RoundingMode.HALF_UP);
    }

    private static BigDecimal zero() {
        return BigDecimal.ZERO;
    }

    private final List<Sale> source;

    public CteEnterpriseAnalytics(List<Sale> sales) {
        if (sales == null) {
            throw new IllegalArgumentException("Sales collection is required.");
        }
        this.source = List.copyOf(sales);
    }

    /*
     * This named stage is analogous to an eligible_sales CTE. It centralizes
     * the financial recognition rule so every downstream calculation uses it.
     */
    private List<Sale> eligibleSales() {
        return source.stream()
                .filter(sale -> sale.status() == OrderStatus.COMPLETED)
                .toList();
    }

    /*
     * Each month is an independent group. A TreeMap guarantees chronological
     * iteration for the later period comparison.
     */
    private List<MonthlyMetric> monthlyMetrics(List<Sale> eligible) {
        Map<String, List<Sale>> byMonth = eligible.stream()
                .collect(Collectors.groupingBy(
                        Sale::month,
                        TreeMap::new,
                        Collectors.toList()));

        List<MonthlyMetric> result = new ArrayList<>();

        byMonth.forEach((month, rows) -> {
            BigDecimal revenue = rows.stream()
                    .map(Sale::revenue)
                    .reduce(zero(), BigDecimal::add);

            BigDecimal profit = rows.stream()
                    .map(Sale::grossProfit)
                    .reduce(zero(), BigDecimal::add);

            long distinctOrders = rows.stream()
                    .map(Sale::orderId)
                    .distinct()
                    .count();

            result.add(new MonthlyMetric(
                    month, money(revenue), money(profit), Math.toIntExact(distinctOrders)));
        });

        return List.copyOf(result);
    }

    /*
     * This stage groups by account and region. Distinct order IDs prevent
     * multiple products from inflating the order count.
     */
    private List<AccountMetric> accountMetrics(List<Sale> eligible) {
        Map<String, List<Sale>> grouped = eligible.stream()
                .collect(Collectors.groupingBy(
                        Sale::account,
                        LinkedHashMap::new,
                        Collectors.toList()));

        List<AccountMetric> result = new ArrayList<>();

        for (Map.Entry<String, List<Sale>> entry : grouped.entrySet()) {
            List<Sale> rows = entry.getValue();
            String account = entry.getKey();

            Set<String> regions = rows.stream()
                    .map(Sale::region)
                    .collect(Collectors.toSet());

            if (regions.size() != 1) {
                throw new IllegalStateException(
                        "Account has conflicting regions: " + account);
            }

            BigDecimal revenue = rows.stream()
                    .map(Sale::revenue)
                    .reduce(zero(), BigDecimal::add);

            BigDecimal profit = rows.stream()
                    .map(Sale::grossProfit)
                    .reduce(zero(), BigDecimal::add);

            long orders = rows.stream()
                    .map(Sale::orderId)
                    .distinct()
                    .count();

            result.add(new AccountMetric(
                    account,
                    regions.iterator().next(),
                    money(revenue),
                    money(profit),
                    Math.toIntExact(orders)));
        }

        result.sort(Comparator.comparing(AccountMetric::grossProfit)
                .reversed()
                .thenComparing(AccountMetric::account));

        return List.copyOf(result);
    }

    /*
     * This final stage is analogous to applying LAG() over monthly revenue.
     * The first month has no previous observation, so its change is undefined.
     */
    private List<GrowthMetric> growthMetrics(List<MonthlyMetric> months) {
        List<GrowthMetric> result = new ArrayList<>();
        BigDecimal previous = null;

        for (MonthlyMetric current : months) {
            if (previous == null) {
                result.add(new GrowthMetric(
                        current.month(), current.revenue(), null, null, null));
            } else {
                BigDecimal change = current.revenue().subtract(previous);
                BigDecimal percentage = previous.signum() == 0
                        ? null
                        : change.multiply(BigDecimal.valueOf(100))
                                .divide(previous, 2, RoundingMode.HALF_UP);

                result.add(new GrowthMetric(
                        current.month(),
                        current.revenue(),
                        previous,
                        money(change),
                        percentage));
            }

            previous = current.revenue();
        }

        return List.copyOf(result);
    }

    private static void printMonthlyReport(List<MonthlyMetric> rows) {
        System.out.println("\nMonthly financial report");
        System.out.printf("%-10s %14s %14s %10s%n",
                "Month", "Revenue", "Gross profit", "Orders");

        for (MonthlyMetric row : rows) {
            System.out.printf("%-10s %14s %14s %10d%n",
                    row.month(), row.revenue(), row.grossProfit(), row.orderCount());
        }
    }

    private static void printAccountReport(List<AccountMetric> rows) {
        System.out.println("\nAccount profitability");
        System.out.printf("%-14s %-10s %14s %14s %10s%n",
                "Account", "Region", "Revenue", "Gross profit", "Orders");

        for (AccountMetric row : rows) {
            System.out.printf("%-14s %-10s %14s %14s %10d%n",
                    row.account(), row.region(), row.revenue(),
                    row.grossProfit(), row.distinctOrders());
        }
    }

    private static void printGrowthReport(List<GrowthMetric> rows) {
        System.out.println("\nPeriod-over-period analysis");
        System.out.printf("%-10s %14s %14s %14s %12s%n",
                "Month", "Revenue", "Previous", "Change", "Change %");

        for (GrowthMetric row : rows) {
            System.out.printf("%-10s %14s %14s %14s %12s%n",
                    row.month(),
                    row.revenue(),
                    Objects.toString(row.previousRevenue(), "N/A"),
                    Objects.toString(row.absoluteChange(), "N/A"),
                    Objects.toString(row.percentageChange(), "N/A"));
        }
    }

    private static List<Sale> sampleData() {
        return List.of(
                new Sale(701, "Acme", "North", "2025-01", "Sensor", 10,
                        new BigDecimal("180.00"), new BigDecimal("105.00"), OrderStatus.COMPLETED),
                new Sale(702, "Beacon", "South", "2025-01", "Controller", 4,
                        new BigDecimal("420.00"), new BigDecimal("290.00"), OrderStatus.COMPLETED),
                new Sale(703, "Acme", "North", "2025-02", "Sensor", 14,
                        new BigDecimal("180.00"), new BigDecimal("105.00"), OrderStatus.COMPLETED),
                new Sale(704, "Cobalt", "West", "2025-02", "Controller", 3,
                        new BigDecimal("420.00"), new BigDecimal("290.00"), OrderStatus.COMPLETED),
                new Sale(705, "Beacon", "South", "2025-02", "Sensor", 8,
                        new BigDecimal("175.00"), new BigDecimal("105.00"), OrderStatus.CANCELLED),
                new Sale(706, "Acme", "North", "2025-03", "Controller", 6,
                        new BigDecimal("430.00"), new BigDecimal("290.00"), OrderStatus.COMPLETED),
                new Sale(707, "Cobalt", "West", "2025-03", "Sensor", 12,
                        new BigDecimal("185.00"), new BigDecimal("105.00"), OrderStatus.COMPLETED),
                new Sale(708, "Beacon", "South", "2025-03", "Controller", 2,
                        new BigDecimal("420.00"), new BigDecimal("290.00"), OrderStatus.REFUNDED),
                new Sale(709, "Beacon", "South", "2025-04", "Sensor", 16,
                        new BigDecimal("185.00"), new BigDecimal("105.00"), OrderStatus.COMPLETED)
        );
    }

    public static void main(String[] args) {
        try {
            CteEnterpriseAnalytics service = new CteEnterpriseAnalytics(sampleData());

            // These shared intermediate stages feed several independent reports.
            List<Sale> eligible = service.eligibleSales();
            List<MonthlyMetric> monthly = service.monthlyMetrics(eligible);
            List<AccountMetric> accounts = service.accountMetrics(eligible);
            List<GrowthMetric> growth = service.growthMetrics(monthly);

            printMonthlyReport(monthly);
            printAccountReport(accounts);
            printGrowthReport(growth);

            BigDecimal totalRevenue = eligible.stream()
                    .map(Sale::revenue)
                    .reduce(zero(), BigDecimal::add);

            if (totalRevenue.signum() <= 0) {
                throw new IllegalStateException("Recognized revenue must be positive.");
            }

            System.out.println("\nRecognized revenue: " + money(totalRevenue));

            try {
                new Sale(0, "Invalid", "North", "2025-01", "Sensor", 1,
                        new BigDecimal("10"), new BigDecimal("5"), OrderStatus.COMPLETED);
            } catch (IllegalArgumentException expected) {
                System.out.println("Expected validation failure: " + expected.getMessage());
            }
        } catch (RuntimeException exception) {
            System.err.println("Financial report failed: " + exception.getMessage());
            System.exitCode = 1;
        }
    }
}
