import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

public class AdvancedPowerBIAnalytics {

    enum Channel {
        ONLINE, RETAIL, PARTNER
    }

    enum ReviewState {
        CURRENT,
        STALE
    }

    record Sale(
            int id,
            LocalDate date,
            String region,
            String product,
            Channel channel,
            int customerId,
            int quantity,
            BigDecimal unitPrice,
            BigDecimal unitCost
    ) {
        Sale {
            if (id <= 0) {
                throw new IllegalArgumentException("Sale id must be positive.");
            }
            if (date == null || region == null || product == null || channel == null) {
                throw new IllegalArgumentException("Sale dimensions are required.");
            }
            if (quantity <= 0) {
                throw new IllegalArgumentException("Quantity must be positive.");
            }
            if (unitPrice.signum() < 0 || unitCost.signum() < 0) {
                throw new IllegalArgumentException("Prices cannot be negative.");
            }
        }

        BigDecimal revenue() {
            return unitPrice.multiply(BigDecimal.valueOf(quantity));
        }

        BigDecimal cost() {
            return unitCost.multiply(BigDecimal.valueOf(quantity));
        }

        BigDecimal margin() {
            return revenue().subtract(cost());
        }
    }

    record InventorySnapshot(
            LocalDate date,
            String region,
            String product,
            int units
    ) {
        InventorySnapshot {
            if (date == null || region == null || product == null) {
                throw new IllegalArgumentException("Inventory dimensions are required.");
            }
            if (units < 0) {
                throw new IllegalArgumentException("Inventory cannot be negative.");
            }
        }
    }

    record FilterContext(
            Set<LocalDate> dates,
            Set<String> regions,
            Set<String> products,
            Set<Channel> channels,
            Set<Integer> customers
    ) {
        FilterContext {
            dates = immutableCopy(dates);
            regions = immutableCopy(regions);
            products = immutableCopy(products);
            channels = immutableCopy(channels);
            customers = immutableCopy(customers);
        }

        static <T> Set<T> immutableCopy(Set<T> input) {
            return input == null ? Set.of() : Set.copyOf(input);
        }

        FilterContext withDates(Set<LocalDate> newDates) {
            return new FilterContext(
                    newDates,
                    regions,
                    products,
                    channels,
                    customers
            );
        }

        FilterContext withProduct(String product) {
            return new FilterContext(
                    dates,
                    regions,
                    Set.of(product),
                    channels,
                    customers
            );
        }

        boolean matches(Sale sale) {
            return
                    (dates.isEmpty() || dates.contains(sale.date())) &&
                    (regions.isEmpty() || regions.contains(sale.region())) &&
                    (products.isEmpty() || products.contains(sale.product())) &&
                    (channels.isEmpty() || channels.contains(sale.channel())) &&
                    (customers.isEmpty() || customers.contains(sale.customerId()));
        }

        boolean matches(InventorySnapshot snapshot) {
            return
                    (dates.isEmpty() || dates.contains(snapshot.date())) &&
                    (regions.isEmpty() || regions.contains(snapshot.region())) &&
                    (products.isEmpty() || products.contains(snapshot.product()));
        }
    }

    record RankedProduct(
            String product,
            int rank,
            BigDecimal revenue
    ) {}

    record MeasureResult(
            BigDecimal revenue,
            BigDecimal cost,
            BigDecimal margin,
            BigDecimal marginPercent,
            long distinctCustomers,
            BigDecimal averageOrderValue,
            BigDecimal previousMonthRevenue,
            BigDecimal monthOverMonthPercent,
            BigDecimal ytdRevenue,
            BigDecimal rolling7DayRevenue,
            BigDecimal percentOfTotal,
            int latestInventory,
            List<RankedProduct> productRanking
    ) {}

    interface MeasurePolicy {
        void validate(FilterContext context);
    }

    static final class StandardMeasurePolicy implements MeasurePolicy {
        @Override
        public void validate(FilterContext context) {
            if (context == null) {
                throw new IllegalArgumentException("Filter context cannot be null.");
            }
        }
    }

    static final class AnalyticsService {
        private final List<Sale> sales;
        private final List<InventorySnapshot> inventory;
        private final MeasurePolicy policy;

        AnalyticsService(
                List<Sale> sales,
                List<InventorySnapshot> inventory,
                MeasurePolicy policy
        ) {
            this.sales = List.copyOf(sales);
            this.inventory = List.copyOf(inventory);
            this.policy = policy;
        }

        private static BigDecimal money(BigDecimal value) {
            return value.setScale(2, RoundingMode.HALF_UP);
        }

        private List<Sale> filterSales(FilterContext context) {
            policy.validate(context);

            return sales.stream()
                    .filter(context::matches)
                    .toList();
        }

        private List<InventorySnapshot> filterInventory(FilterContext context) {
            policy.validate(context);

            return inventory.stream()
                    .filter(context::matches)
                    .toList();
        }

        BigDecimal revenue(FilterContext context) {
            return money(
                    filterSales(context).stream()
                            .map(Sale::revenue)
                            .reduce(BigDecimal.ZERO, BigDecimal::add)
            );
        }

        BigDecimal cost(FilterContext context) {
            return money(
                    filterSales(context).stream()
                            .map(Sale::cost)
                            .reduce(BigDecimal.ZERO, BigDecimal::add)
            );
        }

        BigDecimal margin(FilterContext context) {
            return money(revenue(context).subtract(cost(context)));
        }

        BigDecimal marginPercent(FilterContext context) {
            BigDecimal revenue = revenue(context);

            if (revenue.signum() == 0) {
                return BigDecimal.ZERO.setScale(2);
            }

            return money(
                    margin(context)
                            .multiply(BigDecimal.valueOf(100))
                            .divide(revenue, 4, RoundingMode.HALF_UP)
            );
        }

        long distinctCustomers(FilterContext context) {
            return filterSales(context).stream()
                    .map(Sale::customerId)
                    .distinct()
                    .count();
        }

        BigDecimal averageOrderValue(FilterContext context) {
            Map<Integer, BigDecimal> orders = new HashMap<>();

            for (Sale sale : filterSales(context)) {
                orders.merge(sale.id(), sale.revenue(), BigDecimal::add);
            }

            if (orders.isEmpty()) {
                return BigDecimal.ZERO.setScale(2);
            }

            BigDecimal total = orders.values().stream()
                    .reduce(BigDecimal.ZERO, BigDecimal::add);

            return money(
                    total.divide(
                            BigDecimal.valueOf(orders.size()),
                            4,
                            RoundingMode.HALF_UP
                    )
            );
        }

        BigDecimal previousMonthRevenue(FilterContext context) {
            if (context.dates().isEmpty()) {
                return BigDecimal.ZERO.setScale(2);
            }

            LocalDate first = context.dates().stream()
                    .min(LocalDate::compareTo)
                    .orElseThrow();

            LocalDate previousStart = first.withDayOfMonth(1).minusMonths(1);
            LocalDate previousEnd = previousStart.withDayOfMonth(
                    previousStart.lengthOfMonth()
            );

            Set<LocalDate> dates = new HashSet<>();

            for (
                    LocalDate current = previousStart;
                    !current.isAfter(previousEnd);
                    current = current.plusDays(1)
            ) {
                dates.add(current);
            }

            return revenue(context.withDates(dates));
        }

        BigDecimal monthOverMonthPercent(FilterContext context) {
            BigDecimal current = revenue(context);
            BigDecimal previous = previousMonthRevenue(context);

            if (previous.signum() == 0) {
                return BigDecimal.ZERO.setScale(2);
            }

            return money(
                    current.subtract(previous)
                            .multiply(BigDecimal.valueOf(100))
                            .divide(previous, 4, RoundingMode.HALF_UP)
            );
        }

        BigDecimal ytdRevenue(
                LocalDate anchorDate,
                FilterContext context
        ) {
            LocalDate start = LocalDate.of(anchorDate.getYear(), 1, 1);
            Set<LocalDate> dates = new HashSet<>();

            for (
                    LocalDate current = start;
                    !current.isAfter(anchorDate);
                    current = current.plusDays(1)
            ) {
                dates.add(current);
            }

            return revenue(context.withDates(dates));
        }

        BigDecimal rollingRevenue(
                LocalDate anchorDate,
                int days,
                FilterContext context
        ) {
            if (days <= 0) {
                throw new IllegalArgumentException(
                        "Rolling period must be positive."
                );
            }

            LocalDate start = anchorDate.minusDays(days - 1L);
            Set<LocalDate> dates = new HashSet<>();

            for (
                    LocalDate current = start;
                    !current.isAfter(anchorDate);
                    current = current.plusDays(1)
            ) {
                dates.add(current);
            }

            return revenue(context.withDates(dates));
        }

        BigDecimal percentOfTotal(FilterContext context) {
            BigDecimal numerator = revenue(context);

            FilterContext totalContext = new FilterContext(
                    context.dates(),
                    Set.of(),
                    Set.of(),
                    Set.of(),
                    Set.of()
            );

            BigDecimal denominator = revenue(totalContext);

            if (denominator.signum() == 0) {
                return BigDecimal.ZERO.setScale(2);
            }

            return money(
                    numerator.multiply(BigDecimal.valueOf(100))
                            .divide(denominator, 4, RoundingMode.HALF_UP)
            );
        }

        int latestInventory(FilterContext context) {
            List<InventorySnapshot> rows = filterInventory(context);

            if (rows.isEmpty()) {
                return 0;
            }

            LocalDate latest = rows.stream()
                    .map(InventorySnapshot::date)
                    .max(LocalDate::compareTo)
                    .orElseThrow();

            return rows.stream()
                    .filter(row -> row.date().equals(latest))
                    .mapToInt(InventorySnapshot::units)
                    .sum();
        }

        List<RankedProduct> productRanking(FilterContext context) {
            Set<String> products = new TreeSet<>(
                    filterSales(
                            new FilterContext(
                                    context.dates(),
                                    context.regions(),
                                    Set.of(),
                                    context.channels(),
                                    context.customers()
                            )
                    ).stream()
                            .map(Sale::product)
                            .toList()
            );

            List<Map.Entry<String, BigDecimal>> scores = products.stream()
                    .map(product ->
                            Map.entry(
                                    product,
                                    revenue(context.withProduct(product))
                            )
                    )
                    .sorted(
                            Comparator
                                    .<Map.Entry<String, BigDecimal>>comparingValue()
                                    .reversed()
                                    .thenComparing(Map.Entry::getKey)
                    )
                    .toList();

            List<RankedProduct> result = new ArrayList<>();
            BigDecimal previous = null;
            int rank = 0;

            for (int index = 0; index < scores.size(); index++) {
                Map.Entry<String, BigDecimal> row = scores.get(index);

                if (!row.getValue().equals(previous)) {
                    rank = index + 1;
                }

                result.add(
                        new RankedProduct(
                                row.getKey(),
                                rank,
                                row.getValue()
                        )
                );

                previous = row.getValue();
            }

            return List.copyOf(result);
        }

        MeasureResult evaluate(
                FilterContext context,
                LocalDate anchorDate
        ) {
            return new MeasureResult(
                    revenue(context),
                    cost(context),
                    margin(context),
                    marginPercent(context),
                    distinctCustomers(context),
                    averageOrderValue(context),
                    previousMonthRevenue(context),
                    monthOverMonthPercent(context),
                    ytdRevenue(anchorDate, context),
                    rollingRevenue(anchorDate, 7, context),
                    percentOfTotal(context),
                    latestInventory(context),
                    productRanking(context)
            );
        }
    }

    static Set<LocalDate> datesForMonth(int year, int month) {
        LocalDate start = LocalDate.of(year, month, 1);
        LocalDate end = start.withDayOfMonth(start.lengthOfMonth());
        Set<LocalDate> dates = new HashSet<>();

        for (
                LocalDate current = start;
                !current.isAfter(end);
                current = current.plusDays(1)
        ) {
            dates.add(current);
        }

        return dates;
    }

    static List<Sale> sampleSales() {
        return List.of(
                new Sale(1001, LocalDate.of(2026, 1, 2), "North", "Laptop", Channel.ONLINE, 501, 2, new BigDecimal("1200"), new BigDecimal("800")),
                new Sale(1002, LocalDate.of(2026, 1, 4), "North", "Monitor", Channel.RETAIL, 502, 4, new BigDecimal("300"), new BigDecimal("180")),
                new Sale(1003, LocalDate.of(2026, 1, 8), "South", "Laptop", Channel.PARTNER, 503, 1, new BigDecimal("1250"), new BigDecimal("800")),
                new Sale(1004, LocalDate.of(2026, 1, 12), "North", "Keyboard", Channel.ONLINE, 501, 5, new BigDecimal("80"), new BigDecimal("35")),
                new Sale(1005, LocalDate.of(2026, 1, 18), "South", "Monitor", Channel.RETAIL, 504, 3, new BigDecimal("310"), new BigDecimal("180")),
                new Sale(1006, LocalDate.of(2026, 1, 23), "West", "Laptop", Channel.ONLINE, 505, 1, new BigDecimal("1190"), new BigDecimal("800")),
                new Sale(1007, LocalDate.of(2026, 1, 28), "North", "Laptop", Channel.ONLINE, 506, 1, new BigDecimal("1210"), new BigDecimal("800")),
                new Sale(1008, LocalDate.of(2026, 2, 2), "North", "Monitor", Channel.RETAIL, 507, 5, new BigDecimal("305"), new BigDecimal("180")),
                new Sale(1009, LocalDate.of(2026, 2, 7), "South", "Laptop", Channel.ONLINE, 503, 2, new BigDecimal("1240"), new BigDecimal("800")),
                new Sale(1010, LocalDate.of(2026, 2, 11), "West", "Keyboard", Channel.PARTNER, 508, 8, new BigDecimal("82"), new BigDecimal("35")),
                new Sale(1011, LocalDate.of(2026, 2, 16), "North", "Laptop", Channel.ONLINE, 509, 1, new BigDecimal("1230"), new BigDecimal("800")),
                new Sale(1012, LocalDate.of(2026, 2, 20), "South", "Monitor", Channel.RETAIL, 510, 4, new BigDecimal("315"), new BigDecimal("180")),
                new Sale(1013, LocalDate.of(2026, 2, 24), "West", "Laptop", Channel.PARTNER, 511, 2, new BigDecimal("1180"), new BigDecimal("800")),
                new Sale(1014, LocalDate.of(2026, 2, 27), "North", "Keyboard", Channel.ONLINE, 512, 10, new BigDecimal("78"), new BigDecimal("35")),
                new Sale(1015, LocalDate.of(2026, 3, 2), "South", "Laptop", Channel.ONLINE, 513, 2, new BigDecimal("1260"), new BigDecimal("800")),
                new Sale(1016, LocalDate.of(2026, 3, 5), "North", "Monitor", Channel.RETAIL, 514, 6, new BigDecimal("310"), new BigDecimal("180")),
                new Sale(1017, LocalDate.of(2026, 3, 10), "West", "Keyboard", Channel.PARTNER, 515, 7, new BigDecimal("85"), new BigDecimal("35")),
                new Sale(1018, LocalDate.of(2026, 3, 14), "South", "Laptop", Channel.ONLINE, 516, 1, new BigDecimal("1270"), new BigDecimal("800"))
        );
    }

    static List<InventorySnapshot> sampleInventory() {
        return List.of(
                new InventorySnapshot(LocalDate.of(2026, 1, 31), "North", "Laptop", 42),
                new InventorySnapshot(LocalDate.of(2026, 1, 31), "North", "Monitor", 70),
                new InventorySnapshot(LocalDate.of(2026, 1, 31), "South", "Laptop", 31),
                new InventorySnapshot(LocalDate.of(2026, 2, 28), "North", "Laptop", 37),
                new InventorySnapshot(LocalDate.of(2026, 2, 28), "North", "Monitor", 64),
                new InventorySnapshot(LocalDate.of(2026, 2, 28), "South", "Laptop", 26),
                new InventorySnapshot(LocalDate.of(2026, 2, 28), "West", "Keyboard", 90),
                new InventorySnapshot(LocalDate.of(2026, 3, 15), "North", "Laptop", 34),
                new InventorySnapshot(LocalDate.of(2026, 3, 15), "North", "Monitor", 58),
                new InventorySnapshot(LocalDate.of(2026, 3, 15), "South", "Laptop", 24),
                new InventorySnapshot(LocalDate.of(2026, 3, 15), "West", "Keyboard", 82)
        );
    }

    public static void main(String[] args) {
        AnalyticsService service = new AnalyticsService(
                sampleSales(),
                sampleInventory(),
                new StandardMeasurePolicy()
        );

        FilterContext februaryNorthSouth = new FilterContext(
                datesForMonth(2026, 2),
                Set.of("North", "South"),
                Set.of(),
                EnumSet.noneOf(Channel.class),
                Set.of()
        );

        MeasureResult result = service.evaluate(
                februaryNorthSouth,
                LocalDate.of(2026, 2, 28)
        );

        if (result.revenue().signum() <= 0) {
            throw new IllegalStateException("Revenue must be positive.");
        }

        System.out.println("Advanced Power BI Analytical Measures");
        System.out.println("======================================");
        System.out.println("Revenue: " + result.revenue());
        System.out.println("Cost: " + result.cost());
        System.out.println("Margin: " + result.margin());
        System.out.println("Margin %: " + result.marginPercent());
        System.out.println("Distinct customers: " + result.distinctCustomers());
        System.out.println("Average order value: " + result.averageOrderValue());
        System.out.println("Previous month revenue: " + result.previousMonthRevenue());
        System.out.println("Month-over-month %: " + result.monthOverMonthPercent());
        System.out.println("YTD revenue: " + result.ytdRevenue());
        System.out.println("Rolling 7-day revenue: " + result.rolling7DayRevenue());
        System.out.println("Percent of total: " + result.percentOfTotal());
        System.out.println("Latest inventory: " + result.latestInventory());

        System.out.println("\nProduct ranking:");
        result.productRanking().forEach(row ->
                System.out.printf(
                        "Rank %d | %-10s | %s%n",
                        row.rank(),
                        row.product(),
                        row.revenue()
                )
        );

        FilterContext empty = new FilterContext(
                Set.of(),
                Set.of(),
                Set.of("Unknown"),
                Set.of(),
                Set.of()
        );

        if (service.revenue(empty).signum() != 0) {
            throw new IllegalStateException("Empty context validation failed.");
        }

        System.out.println("\nValidation: passed.");
        System.out.println(
                "The immutable domain records separate data state from measure evaluation."
        );
        System.out.println(
                "Policy validation occurs before analytical operations, while "
                + "BigDecimal avoids binary floating-point currency errors."
        );
        System.out.println(
                "Product ranking sorts product-level measure results and applies "
                + "competition ranking when revenues tie."
        );
    }
}
