import java.util.*;
import java.util.stream.Collectors;

/**
 * Revenue Analytics: Enterprise Revenue Decomposition and Growth
 *
 * Java 17.
 *
 * Domain architecture:
 * - Immutable revenue records
 * - Explicit analytical periods
 * - Revenue calculation services
 * - Growth and decomposition policies
 * - Customer concentration evaluation
 * - Product and regional performance
 * - Forecast service
 * - Validation exceptions
 * - Reconciliation controls
 */

public class RevenueAnalytics {

    private static final double EPSILON = 0.000001;

    enum BusinessDimension {
        PRODUCT,
        REGION,
        CUSTOMER
    }

    enum ForecastMethod {
        AVERAGE_GROWTH,
        LINEAR_TREND
    }

    enum PerformanceStatus {
        GROWING,
        DECLINING,
        STABLE
    }

    static class AnalyticsException extends RuntimeException {
        AnalyticsException(String message) {
            super(message);
        }
    }

    static class ValidationException extends AnalyticsException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class PeriodException extends AnalyticsException {
        PeriodException(String message) {
            super(message);
        }
    }

    record RevenueRecord(
            String period,
            String product,
            String region,
            String customer,
            long units,
            double listPrice,
            double discountRate,
            double unitCost
    ) {
        RevenueRecord {
            Objects.requireNonNull(period);
            Objects.requireNonNull(product);
            Objects.requireNonNull(region);
            Objects.requireNonNull(customer);

            if (!period.matches("\\d{4}-(0[1-9]|1[0-2])")) {
                throw new ValidationException(
                        "Invalid period: " + period
                );
            }

            if (product.isBlank() ||
                    region.isBlank() ||
                    customer.isBlank()) {
                throw new ValidationException(
                        "Business dimensions cannot be empty."
                );
            }

            if (units < 0) {
                throw new ValidationException(
                        "Units cannot be negative."
                );
            }

            if (!Double.isFinite(listPrice) ||
                    !Double.isFinite(discountRate) ||
                    !Double.isFinite(unitCost)) {
                throw new ValidationException(
                        "Financial values must be finite."
                );
            }

            if (listPrice < 0 ||
                    unitCost < 0 ||
                    discountRate < 0 ||
                    discountRate > 1) {
                throw new ValidationException(
                        "Invalid price, discount or cost."
                );
            }
        }

        double netPrice() {
            return listPrice * (1.0 - discountRate);
        }

        double revenue() {
            return units * netPrice();
        }

        double cost() {
            return units * unitCost;
        }

        double grossProfit() {
            return revenue() - cost();
        }

        String uniqueKey() {
            return String.join(
                    "|", period, product, region, customer
            );
        }
    }

    record Metrics(
            long units,
            double revenue,
            double variableCost,
            double grossProfit,
            double averageSellingPrice,
            double grossMargin
    ) {}

    record GrowthResult(
            String previousPeriod,
            String currentPeriod,
            double previousRevenue,
            double currentRevenue,
            double revenueChange,
            Double growthRate,
            long unitChange,
            double averagePriceChange,
            double grossMarginChange,
            PerformanceStatus status
    ) {}

    record DecompositionResult(
            double previousRevenue,
            double currentRevenue,
            double revenueChange,
            double volumeEffect,
            double mixEffect,
            double priceEffect,
            double reconciliationDifference
    ) {}

    record ProductMetric(
            String product,
            long units,
            double revenue,
            double averagePrice,
            double grossProfit,
            double margin,
            double revenueShare
    ) {}

    record DimensionResult(
            String dimension,
            String name,
            Metrics metrics,
            double revenueShare
    ) {}

    record ForecastResult(
            int step,
            double forecastRevenue,
            ForecastMethod method
    ) {}

    record ConcentrationResult(
            int customerCount,
            double largestCustomerShare,
            double topFiveShare,
            double hhi
    ) {}

    interface RevenuePolicy {
        void validate(RevenueRecord record);
    }

    static class StandardRevenuePolicy implements RevenuePolicy {

        @Override
        public void validate(RevenueRecord record) {
            if (record.units() < 0) {
                throw new ValidationException(
                        "Policy violation: negative volume."
                );
            }

            if (record.netPrice() < 0) {
                throw new ValidationException(
                        "Policy violation: negative realized price."
                );
            }
        }
    }

    static class RevenueRepository {

        private final List<RevenueRecord> records =
                new ArrayList<>();

        private final Set<String> uniqueKeys =
                new HashSet<>();

        private final RevenuePolicy policy;

        RevenueRepository(RevenuePolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        public synchronized void add(RevenueRecord record) {
            policy.validate(record);

            if (!uniqueKeys.add(record.uniqueKey())) {
                throw new ValidationException(
                        "Duplicate analytical observation."
                );
            }

            records.add(record);
        }

        public List<RevenueRecord> findByPeriod(String period) {
            List<RevenueRecord> result = records.stream()
                    .filter(r -> r.period().equals(period))
                    .toList();

            if (result.isEmpty()) {
                throw new PeriodException(
                        "No revenue records for " + period
                );
            }

            return result;
        }

        public List<RevenueRecord> findAll() {
            return List.copyOf(records);
        }

        public List<String> periods() {
            return records.stream()
                    .map(RevenueRecord::period)
                    .distinct()
                    .sorted()
                    .toList();
        }
    }

    static class RevenueCalculationService {

        Metrics aggregate(List<RevenueRecord> records) {
            long units = 0;
            double revenue = 0;
            double cost = 0;

            for (RevenueRecord record : records) {
                units += record.units();
                revenue += record.revenue();
                cost += record.cost();
            }

            double profit = revenue - cost;

            return new Metrics(
                    units,
                    revenue,
                    cost,
                    profit,
                    units > 0 ? revenue / units : 0,
                    revenue > 0 ? profit / revenue : 0
            );
        }

        Map<String, ProductMetric> productMetrics(
                List<RevenueRecord> records
        ) {
            Map<String, List<RevenueRecord>> grouped =
                    records.stream().collect(
                            Collectors.groupingBy(
                                    RevenueRecord::product
                            )
                    );

            double totalRevenue = records.stream()
                    .mapToDouble(RevenueRecord::revenue)
                    .sum();

            Map<String, ProductMetric> results =
                    new TreeMap<>();

            for (var entry : grouped.entrySet()) {
                String product = entry.getKey();
                Metrics metrics = aggregate(entry.getValue());

                results.put(
                        product,
                        new ProductMetric(
                                product,
                                metrics.units(),
                                metrics.revenue(),
                                metrics.averageSellingPrice(),
                                metrics.grossProfit(),
                                metrics.grossMargin(),
                                totalRevenue > 0
                                        ? metrics.revenue() / totalRevenue
                                        : 0
                        )
                );
            }

            return Collections.unmodifiableMap(results);
        }
    }

    static class GrowthAnalysisService {

        private final RevenueRepository repository;
        private final RevenueCalculationService calculations;

        GrowthAnalysisService(
                RevenueRepository repository,
                RevenueCalculationService calculations
        ) {
            this.repository = repository;
            this.calculations = calculations;
        }

        GrowthResult compare(String previous, String current) {
            if (previous.compareTo(current) >= 0) {
                throw new PeriodException(
                        "Current period must follow previous period."
                );
            }

            Metrics old = calculations.aggregate(
                    repository.findByPeriod(previous)
            );

            Metrics latest = calculations.aggregate(
                    repository.findByPeriod(current)
            );

            double change = latest.revenue() - old.revenue();

            PerformanceStatus status;

            if (change > EPSILON) {
                status = PerformanceStatus.GROWING;
            } else if (change < -EPSILON) {
                status = PerformanceStatus.DECLINING;
            } else {
                status = PerformanceStatus.STABLE;
            }

            return new GrowthResult(
                    previous,
                    current,
                    old.revenue(),
                    latest.revenue(),
                    change,
                    old.revenue() > 0
                            ? change / old.revenue()
                            : null,
                    latest.units() - old.units(),
                    latest.averageSellingPrice()
                            - old.averageSellingPrice(),
                    latest.grossMargin() - old.grossMargin(),
                    status
            );
        }
    }

    static class DecompositionService {

        private final RevenueRepository repository;
        private final RevenueCalculationService calculations;

        DecompositionService(
                RevenueRepository repository,
                RevenueCalculationService calculations
        ) {
            this.repository = repository;
            this.calculations = calculations;
        }

        DecompositionResult calculate(
                String previous,
                String current
        ) {
            List<RevenueRecord> oldRecords =
                    repository.findByPeriod(previous);

            List<RevenueRecord> newRecords =
                    repository.findByPeriod(current);

            Metrics oldTotal = calculations.aggregate(oldRecords);
            Metrics newTotal = calculations.aggregate(newRecords);

            if (oldTotal.units() <= 0 || newTotal.units() <= 0) {
                throw new PeriodException(
                        "Both periods must have positive volume."
                );
            }

            Map<String, ProductMetric> old =
                    calculations.productMetrics(oldRecords);

            Map<String, ProductMetric> latest =
                    calculations.productMetrics(newRecords);

            Set<String> products = new HashSet<>();
            products.addAll(old.keySet());
            products.addAll(latest.keySet());

            double q0 = oldTotal.units();
            double q1 = newTotal.units();

            double baselineWeightedPrice = 0;
            double mixEffect = 0;
            double priceEffect = 0;

            for (String product : products) {
                ProductMetric a = old.getOrDefault(
                        product,
                        new ProductMetric(
                                product, 0, 0, 0, 0, 0, 0
                        )
                );

                ProductMetric b = latest.getOrDefault(
                        product,
                        new ProductMetric(
                                product, 0, 0, 0, 0, 0, 0
                        )
                );

                double oldShare = a.units() / q0;
                double newShare = b.units() / q1;

                baselineWeightedPrice +=
                        oldShare * a.averagePrice();

                mixEffect += q1 *
                        (newShare - oldShare) *
                        a.averagePrice();

                priceEffect += q1 *
                        newShare *
                        (b.averagePrice() - a.averagePrice());
            }

            double volumeEffect =
                    (q1 - q0) * baselineWeightedPrice;

            double revenueChange =
                    newTotal.revenue() - oldTotal.revenue();

            double reconciliation =
                    revenueChange -
                            (volumeEffect + mixEffect + priceEffect);

            if (Math.abs(reconciliation) > EPSILON) {
                throw new AnalyticsException(
                        "Revenue decomposition failed reconciliation."
                );
            }

            return new DecompositionResult(
                    oldTotal.revenue(),
                    newTotal.revenue(),
                    revenueChange,
                    volumeEffect,
                    mixEffect,
                    priceEffect,
                    reconciliation
            );
        }
    }

    static class DimensionAnalysisService {

        private final RevenueRepository repository;
        private final RevenueCalculationService calculations;

        DimensionAnalysisService(
                RevenueRepository repository,
                RevenueCalculationService calculations
        ) {
            this.repository = repository;
            this.calculations = calculations;
        }

        List<DimensionResult> analyze(
                String period,
                BusinessDimension dimension
        ) {
            List<RevenueRecord> records =
                    repository.findByPeriod(period);

            Map<String, List<RevenueRecord>> groups =
                    new TreeMap<>();

            for (RevenueRecord record : records) {
                String key = switch (dimension) {
                    case PRODUCT -> record.product();
                    case REGION -> record.region();
                    case CUSTOMER -> record.customer();
                };

                groups.computeIfAbsent(
                        key,
                        ignored -> new ArrayList<>()
                ).add(record);
            }

            double totalRevenue =
                    calculations.aggregate(records).revenue();

            return groups.entrySet().stream()
                    .map(entry -> {
                        Metrics metrics =
                                calculations.aggregate(entry.getValue());

                        return new DimensionResult(
                                dimension.name(),
                                entry.getKey(),
                                metrics,
                                totalRevenue > 0
                                        ? metrics.revenue() / totalRevenue
                                        : 0
                        );
                    })
                    .sorted(
                            Comparator.comparingDouble(
                                    (DimensionResult result) ->
                                            result.metrics().revenue()
                            ).reversed()
                    )
                    .toList();
        }
    }

    static class ConcentrationService {

        private final DimensionAnalysisService dimensions;

        ConcentrationService(DimensionAnalysisService dimensions) {
            this.dimensions = dimensions;
        }

        ConcentrationResult evaluate(String period) {
            List<DimensionResult> customers = dimensions.analyze(
                    period,
                    BusinessDimension.CUSTOMER
            );

            double hhi = customers.stream()
                    .mapToDouble(
                            customer ->
                                    Math.pow(customer.revenueShare(), 2)
                    )
                    .sum();

            double largest = customers.stream()
                    .mapToDouble(DimensionResult::revenueShare)
                    .max()
                    .orElse(0);

            double topFive = customers.stream()
                    .limit(5)
                    .mapToDouble(DimensionResult::revenueShare)
                    .sum();

            return new ConcentrationResult(
                    customers.size(),
                    largest,
                    topFive,
                    hhi
            );
        }
    }

    static class ForecastService {

        private final RevenueRepository repository;
        private final RevenueCalculationService calculations;

        ForecastService(
                RevenueRepository repository,
                RevenueCalculationService calculations
        ) {
            this.repository = repository;
            this.calculations = calculations;
        }

        List<ForecastResult> forecast(
                int horizon,
                ForecastMethod method
        ) {
            if (horizon < 1 || horizon > 36) {
                throw new ValidationException(
                        "Horizon must be between 1 and 36."
                );
            }

            List<String> periods = repository.periods();

            if (periods.size() < 2) {
                throw new PeriodException(
                        "Two historical periods are required."
                );
            }

            List<Double> values = periods.stream()
                    .map(period -> calculations.aggregate(
                            repository.findByPeriod(period)
                    ).revenue())
                    .toList();

            double growthRate = 0;
            double last = values.get(values.size() - 1);

            if (method == ForecastMethod.AVERAGE_GROWTH) {
                for (int i = 1; i < values.size(); i++) {
                    if (values.get(i - 1) <= 0) {
                        throw new AnalyticsException(
                                "Forecast requires positive revenue."
                        );
                    }

                    growthRate +=
                            values.get(i) / values.get(i - 1) - 1;
                }

                growthRate /= values.size() - 1;
            }

            if (method == ForecastMethod.LINEAR_TREND) {
                int n = values.size();

                double xMean = (n - 1) / 2.0;
                double yMean = values.stream()
                        .mapToDouble(Double::doubleValue)
                        .average()
                        .orElse(0);

                double numerator = 0;
                double denominator = 0;

                for (int i = 0; i < n; i++) {
                    numerator += (i - xMean) *
                            (values.get(i) - yMean);

                    denominator += Math.pow(i - xMean, 2);
                }

                double slope = numerator / denominator;

                List<ForecastResult> results =
                        new ArrayList<>();

                for (int i = 1; i <= horizon; i++) {
                    double predicted = Math.max(
                            0,
                            yMean + slope * (n + i - 1 - xMean)
                    );

                    results.add(new ForecastResult(
                            i,
                            predicted,
                            method
                    ));
                }

                return List.copyOf(results);
            }

            List<ForecastResult> results = new ArrayList<>();

            for (int i = 1; i <= horizon; i++) {
                last = Math.max(0, last * (1 + growthRate));

                results.add(new ForecastResult(
                        i,
                        last,
                        method
                ));
            }

            return List.copyOf(results);
        }
    }

    static RevenueRepository createRepository() {
        RevenueRepository repository =
                new RevenueRepository(
                        new StandardRevenuePolicy()
                );

        Object[][] rows = {
                {"2026-01","Cloud","North","Customer A",100,1200.0,.05,600.0},
                {"2026-01","Software","South","Customer B",180,500.0,.10,180.0},
                {"2026-01","Hardware","East","Customer C",250,300.0,.08,190.0},
                {"2026-01","Services","West","Customer D",90,900.0,.05,400.0},

                {"2026-02","Cloud","North","Customer A",115,1250.0,.04,600.0},
                {"2026-02","Software","South","Customer B",200,520.0,.08,180.0},
                {"2026-02","Hardware","East","Customer C",230,310.0,.05,190.0},
                {"2026-02","Services","West","Customer D",105,920.0,.04,400.0},

                {"2026-03","Cloud","North","Customer A",130,1300.0,.03,600.0},
                {"2026-03","Software","South","Customer B",220,540.0,.07,180.0},
                {"2026-03","Hardware","East","Customer C",245,320.0,.05,190.0},
                {"2026-03","Services","West","Customer D",115,950.0,.03,400.0},

                {"2026-04","Cloud","North","Customer A",145,1350.0,.03,600.0},
                {"2026-04","Software","South","Customer B",240,550.0,.06,180.0},
                {"2026-04","Hardware","East","Customer C",260,330.0,.06,190.0},
                {"2026-04","Services","West","Customer D",130,970.0,.04,400.0}
        };

        for (Object[] row : rows) {
            repository.add(new RevenueRecord(
                    (String) row[0],
                    (String) row[1],
                    (String) row[2],
                    (String) row[3],
                    ((Number) row[4]).longValue(),
                    ((Number) row[5]).doubleValue(),
                    ((Number) row[6]).doubleValue(),
                    ((Number) row[7]).doubleValue()
            ));
        }

        return repository;
    }

    static void runTests(
            RevenueRepository repository,
            GrowthAnalysisService growth,
            DecompositionService decomposition
    ) {
        GrowthResult result = growth.compare(
                "2026-03",
                "2026-04"
        );

        if (result.revenueChange() <= 0) {
            throw new AnalyticsException(
                    "Expected positive revenue growth."
            );
        }

        DecompositionResult decompositionResult =
                decomposition.calculate(
                        "2026-03",
                        "2026-04"
                );

        if (Math.abs(
                decompositionResult.reconciliationDifference()
        ) > EPSILON) {
            throw new AnalyticsException(
                    "Decomposition test failed."
            );
        }

        try {
            repository.add(repository.findAll().get(0));
            throw new AnalyticsException(
                    "Duplicate validation did not execute."
            );
        } catch (ValidationException expected) {
            System.out.println("Duplicate-record validation passed.");
        }

        System.out.println("All enterprise analytics tests passed.");
    }

    public static void main(String[] args) {

        try {
            RevenueRepository repository = createRepository();

            RevenueCalculationService calculations =
                    new RevenueCalculationService();

            GrowthAnalysisService growth =
                    new GrowthAnalysisService(
                            repository,
                            calculations
                    );

            DecompositionService decomposition =
                    new DecompositionService(
                            repository,
                            calculations
                    );

            DimensionAnalysisService dimensions =
                    new DimensionAnalysisService(
                            repository,
                            calculations
                    );

            ConcentrationService concentration =
                    new ConcentrationService(dimensions);

            ForecastService forecasting =
                    new ForecastService(
                            repository,
                            calculations
                    );

            runTests(repository, growth, decomposition);

            System.out.println("\nREVENUE GROWTH");
            System.out.println(
                    growth.compare("2026-03", "2026-04")
            );

            System.out.println("\nREVENUE DECOMPOSITION");
            System.out.println(
                    decomposition.calculate(
                            "2026-03",
                            "2026-04"
                    )
            );

            System.out.println("\nPRODUCT PERFORMANCE");

            dimensions.analyze(
                    "2026-04",
                    BusinessDimension.PRODUCT
            ).forEach(System.out::println);

            System.out.println("\nREGIONAL PERFORMANCE");

            dimensions.analyze(
                    "2026-04",
                    BusinessDimension.REGION
            ).forEach(System.out::println);

            System.out.println("\nCUSTOMER CONCENTRATION");
            System.out.println(
                    concentration.evaluate("2026-04")
            );

            System.out.println("\nREVENUE FORECAST");

            forecasting.forecast(
                    3,
                    ForecastMethod.AVERAGE_GROWTH
            ).forEach(System.out::println);

            System.out.println("\nLINEAR TREND FORECAST");

            forecasting.forecast(
                    3,
                    ForecastMethod.LINEAR_TREND
            ).forEach(System.out::println);

        } catch (AnalyticsException exception) {
            System.err.println(
                    "Analytics failure: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
