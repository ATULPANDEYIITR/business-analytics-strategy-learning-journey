import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;

/*
 * Enterprise executive dashboard service.
 *
 * The model separates:
 * - monthly business performance,
 * - user access scope,
 * - dashboard query filters,
 * - KPI calculations,
 * - management alert policies.
 *
 * Java 17 records provide immutable domain data. The service applies
 * access restrictions before calculating any dashboard metrics.
 */

public class ExecutiveDashboard {

    private static final BigDecimal ZERO = BigDecimal.ZERO;
    private static final BigDecimal ONE_HUNDRED = new BigDecimal("100");

    enum Role {
        EXECUTIVE,
        REGIONAL_MANAGER,
        BUSINESS_UNIT_MANAGER,
        ANALYST
    }

    enum Severity {
        CRITICAL,
        WARNING
    }

    record MonthlyPerformance(
        YearMonth month,
        String businessUnit,
        String region,
        BigDecimal revenue,
        BigDecimal revenueTarget,
        BigDecimal cogs,
        BigDecimal operatingExpense,
        long orders,
        long deliveredOrders,
        long onTimeOrders,
        BigDecimal csatScoreSum,
        long csatResponses
    ) {
        MonthlyPerformance {
            if (month == null) {
                throw new IllegalArgumentException("month is required");
            }

            businessUnit = requireText(businessUnit, "businessUnit");
            region = requireText(region, "region");

            revenue = requireNonNegative(revenue, "revenue");
            revenueTarget = requirePositive(revenueTarget, "revenueTarget");
            cogs = requireNonNegative(cogs, "cogs");
            operatingExpense = requireNonNegative(
                operatingExpense,
                "operatingExpense"
            );
            csatScoreSum = requireNonNegative(
                csatScoreSum,
                "csatScoreSum"
            );

            if (orders < 0 || deliveredOrders < 0 ||
                onTimeOrders < 0 || csatResponses < 0) {
                throw new IllegalArgumentException(
                    "Counts cannot be negative"
                );
            }

            if (deliveredOrders > orders ||
                onTimeOrders > deliveredOrders) {
                throw new IllegalArgumentException(
                    "Delivery counts are inconsistent"
                );
            }

            if (csatResponses == 0) {
                if (csatScoreSum.compareTo(ZERO) != 0) {
                    throw new IllegalArgumentException(
                        "CSAT total must be zero without responses"
                    );
                }
            } else {
                BigDecimal minimum = BigDecimal.valueOf(csatResponses);
                BigDecimal maximum = minimum.multiply(new BigDecimal("5"));

                if (csatScoreSum.compareTo(minimum) < 0 ||
                    csatScoreSum.compareTo(maximum) > 0) {
                    throw new IllegalArgumentException(
                        "CSAT total violates the 1-to-5 response scale"
                    );
                }
            }
        }
    }

    record AccessScope(
        Role role,
        Set<String> allowedRegions,
        Set<String> allowedBusinessUnits
    ) {
        AccessScope {
            if (role == null) {
                throw new IllegalArgumentException("role is required");
            }

            allowedRegions = immutableSet(allowedRegions);
            allowedBusinessUnits = immutableSet(allowedBusinessUnits);

            switch (role) {
                case EXECUTIVE -> {
                    // An executive scope is unrestricted in this model.
                }
                case REGIONAL_MANAGER -> {
                    if (allowedRegions.isEmpty() ||
                        !allowedBusinessUnits.isEmpty()) {
                        throw new IllegalArgumentException(
                            "Regional managers require region scope only"
                        );
                    }
                }
                case BUSINESS_UNIT_MANAGER -> {
                    if (allowedBusinessUnits.isEmpty() ||
                        !allowedRegions.isEmpty()) {
                        throw new IllegalArgumentException(
                            "Business-unit managers require unit scope only"
                        );
                    }
                }
                case ANALYST -> {
                    if (allowedRegions.isEmpty() ||
                        allowedBusinessUnits.isEmpty()) {
                        throw new IllegalArgumentException(
                            "Analysts require explicit region and unit scopes"
                        );
                    }
                }
            }
        }

        boolean permits(MonthlyPerformance row) {
            if (role == Role.EXECUTIVE) {
                return true;
            }

            boolean regionAllowed = allowedRegions.isEmpty() ||
                allowedRegions.contains(row.region());

            boolean unitAllowed = allowedBusinessUnits.isEmpty() ||
                allowedBusinessUnits.contains(row.businessUnit());

            return regionAllowed && unitAllowed;
        }

        void validateRequestedFilters(DashboardRequest request) {
            if (role == Role.EXECUTIVE) {
                return;
            }

            if (request.region() != null &&
                !allowedRegions.isEmpty() &&
                !allowedRegions.contains(request.region())) {
                throw new AccessDeniedException(
                    "Requested region is outside the user's access scope"
                );
            }

            if (request.businessUnit() != null &&
                !allowedBusinessUnits.isEmpty() &&
                !allowedBusinessUnits.contains(request.businessUnit())) {
                throw new AccessDeniedException(
                    "Requested business unit is outside the user's access scope"
                );
            }
        }
    }

    record DashboardRequest(
        YearMonth fromMonth,
        YearMonth toMonth,
        String region,
        String businessUnit
    ) {
        DashboardRequest {
            if (fromMonth == null || toMonth == null) {
                throw new IllegalArgumentException(
                    "Both reporting-period boundaries are required"
                );
            }

            if (fromMonth.isAfter(toMonth)) {
                throw new IllegalArgumentException(
                    "fromMonth cannot be later than toMonth"
                );
            }

            region = optionalText(region);
            businessUnit = optionalText(businessUnit);
        }
    }

    record KpiSnapshot(
        int recordCount,
        BigDecimal revenue,
        BigDecimal revenueTarget,
        BigDecimal grossProfit,
        BigDecimal operatingProfit,
        Optional<BigDecimal> revenueAttainmentPct,
        Optional<BigDecimal> grossMarginPct,
        Optional<BigDecimal> operatingMarginPct,
        Optional<BigDecimal> fulfillmentPct,
        Optional<BigDecimal> onTimeDeliveryPct,
        Optional<BigDecimal> averageCsat,
        long orders,
        long deliveredOrders,
        long onTimeOrders,
        long csatResponses
    ) {
        KpiSnapshot {
            revenueAttainmentPct = safeOptional(revenueAttainmentPct);
            grossMarginPct = safeOptional(grossMarginPct);
            operatingMarginPct = safeOptional(operatingMarginPct);
            fulfillmentPct = safeOptional(fulfillmentPct);
            onTimeDeliveryPct = safeOptional(onTimeDeliveryPct);
            averageCsat = safeOptional(averageCsat);
        }
    }

    record Alert(
        String code,
        Severity severity,
        String message
    ) {
        Alert {
            code = requireText(code, "alert code");
            message = requireText(message, "alert message");
            if (severity == null) {
                throw new IllegalArgumentException("alert severity is required");
            }
        }
    }

    record DashboardSnapshot(
        DashboardRequest request,
        Role role,
        KpiSnapshot kpis,
        List<Alert> alerts,
        int visibleRecordCount
    ) {
        DashboardSnapshot {
            alerts = List.copyOf(alerts);
        }
    }

    interface MetricPolicy {
        Optional<Alert> evaluate(KpiSnapshot metrics);
    }

    record RevenueAttainmentPolicy(
        BigDecimal minimumAttainmentPct
    ) implements MetricPolicy {
        @Override
        public Optional<Alert> evaluate(KpiSnapshot metrics) {
            return metrics.revenueAttainmentPct()
                .filter(value -> value.compareTo(minimumAttainmentPct) < 0)
                .map(value -> new Alert(
                    "REVENUE_BELOW_PLAN",
                    value.compareTo(new BigDecimal("95")) < 0
                        ? Severity.CRITICAL
                        : Severity.WARNING,
                    "Revenue attainment is " + value + "%."
                ));
        }
    }

    record GrossMarginPolicy(
        BigDecimal minimumGrossMarginPct
    ) implements MetricPolicy {
        @Override
        public Optional<Alert> evaluate(KpiSnapshot metrics) {
            return metrics.grossMarginPct()
                .filter(value -> value.compareTo(minimumGrossMarginPct) < 0)
                .map(value -> new Alert(
                    "LOW_GROSS_MARGIN",
                    Severity.CRITICAL,
                    "Gross margin is below the configured threshold."
                ));
        }
    }

    record DeliveryPolicy(
        BigDecimal minimumOnTimeDeliveryPct
    ) implements MetricPolicy {
        @Override
        public Optional<Alert> evaluate(KpiSnapshot metrics) {
            return metrics.onTimeDeliveryPct()
                .filter(value ->
                    value.compareTo(minimumOnTimeDeliveryPct) < 0
                )
                .map(value -> new Alert(
                    "DELIVERY_PERFORMANCE",
                    Severity.CRITICAL,
                    "On-time delivery is below the configured threshold."
                ));
        }
    }

    record CustomerSatisfactionPolicy(
        BigDecimal minimumCsat
    ) implements MetricPolicy {
        @Override
        public Optional<Alert> evaluate(KpiSnapshot metrics) {
            return metrics.averageCsat()
                .filter(value -> value.compareTo(minimumCsat) < 0)
                .map(value -> new Alert(
                    "CUSTOMER_SATISFACTION",
                    Severity.WARNING,
                    "Average customer satisfaction is below the threshold."
                ));
        }
    }

    static final class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String message) {
            super(message);
        }
    }

    static final class DashboardService {
        private final List<MonthlyPerformance> data;
        private final List<MetricPolicy> policies;

        DashboardService(
            List<MonthlyPerformance> data,
            List<MetricPolicy> policies
        ) {
            if (data == null || data.isEmpty()) {
                throw new IllegalArgumentException(
                    "Dashboard data cannot be empty"
                );
            }

            this.data = List.copyOf(data);
            this.policies = List.copyOf(policies);
            validateUniqueKeys(this.data);
        }

        DashboardSnapshot build(
            DashboardRequest request,
            AccessScope scope
        ) {
            if (request == null || scope == null) {
                throw new IllegalArgumentException(
                    "Request and access scope are required"
                );
            }

            scope.validateRequestedFilters(request);

            // Apply access control before user-selected report filters.
            List<MonthlyPerformance> visibleRows = data.stream()
                .filter(scope::permits)
                .filter(row ->
                    !row.month().isBefore(request.fromMonth()) &&
                    !row.month().isAfter(request.toMonth())
                )
                .filter(row ->
                    request.region() == null ||
                    row.region().equals(request.region())
                )
                .filter(row ->
                    request.businessUnit() == null ||
                    row.businessUnit().equals(request.businessUnit())
                )
                .collect(Collectors.toUnmodifiableList());

            KpiSnapshot metrics = KpiCalculator.calculate(visibleRows);

            List<Alert> alerts = new ArrayList<>();

            if (visibleRows.isEmpty()) {
                alerts.add(new Alert(
                    "NO_DATA",
                    Severity.WARNING,
                    "No records match the authorized dashboard filters."
                ));
            } else {
                for (MetricPolicy policy : policies) {
                    policy.evaluate(metrics).ifPresent(alerts::add);
                }
            }

            return new DashboardSnapshot(
                request,
                scope.role(),
                metrics,
                alerts,
                visibleRows.size()
            );
        }

        private static void validateUniqueKeys(
            List<MonthlyPerformance> records
        ) {
            Set<String> keys = records.stream()
                .map(row -> row.month() + "|" +
                    row.businessUnit() + "|" + row.region())
                .collect(Collectors.toSet());

            if (keys.size() != records.size()) {
                throw new IllegalArgumentException(
                    "Duplicate monthly business-unit and region record"
                );
            }
        }
    }

    static final class KpiCalculator {
        private KpiCalculator() {}

        static KpiSnapshot calculate(List<MonthlyPerformance> rows) {
            BigDecimal revenue = ZERO;
            BigDecimal target = ZERO;
            BigDecimal cogs = ZERO;
            BigDecimal operatingExpense = ZERO;
            BigDecimal csatScoreSum = ZERO;

            long orders = 0;
            long delivered = 0;
            long onTime = 0;
            long responses = 0;

            for (MonthlyPerformance row : rows) {
                revenue = revenue.add(row.revenue());
                target = target.add(row.revenueTarget());
                cogs = cogs.add(row.cogs());
                operatingExpense = operatingExpense.add(
                    row.operatingExpense()
                );
                csatScoreSum = csatScoreSum.add(row.csatScoreSum());

                orders = Math.addExact(orders, row.orders());
                delivered = Math.addExact(delivered, row.deliveredOrders());
                onTime = Math.addExact(onTime, row.onTimeOrders());
                responses = Math.addExact(responses, row.csatResponses());
            }

            BigDecimal grossProfit = revenue.subtract(cogs);
            BigDecimal operatingProfit = grossProfit.subtract(
                operatingExpense
            );

            return new KpiSnapshot(
                rows.size(),
                revenue,
                target,
                grossProfit,
                operatingProfit,
                divideAsPercentage(revenue, target),
                divideAsPercentage(grossProfit, revenue),
                divideAsPercentage(operatingProfit, revenue),
                divideAsPercentage(
                    BigDecimal.valueOf(delivered),
                    BigDecimal.valueOf(orders)
                ),
                divideAsPercentage(
                    BigDecimal.valueOf(onTime),
                    BigDecimal.valueOf(delivered)
                ),
                divide(csatScoreSum, responses),
                orders,
                delivered,
                onTime,
                responses
            );
        }

        private static Optional<BigDecimal> divideAsPercentage(
            BigDecimal numerator,
            BigDecimal denominator
        ) {
            return divide(numerator.multiply(ONE_HUNDRED), denominator);
        }

        private static Optional<BigDecimal> divide(
            BigDecimal numerator,
            long denominator
        ) {
            if (denominator == 0) {
                return Optional.empty();
            }

            return Optional.of(
                numerator.divide(
                    BigDecimal.valueOf(denominator),
                    2,
                    RoundingMode.HALF_UP
                )
            );
        }

        private static Optional<BigDecimal> divide(
            BigDecimal numerator,
            BigDecimal denominator
        ) {
            if (denominator.compareTo(ZERO) == 0) {
                return Optional.empty();
            }

            return Optional.of(
                numerator.divide(denominator, 2, RoundingMode.HALF_UP)
            );
        }
    }

    private static BigDecimal requirePositive(
        BigDecimal value,
        String field
    ) {
        BigDecimal result = requireNonNegative(value, field);

        if (result.compareTo(ZERO) == 0) {
            throw new IllegalArgumentException(
                field + " must be greater than zero"
            );
        }

        return result;
    }

    private static BigDecimal requireNonNegative(
        BigDecimal value,
        String field
    ) {
        if (value == null || value.compareTo(ZERO) < 0) {
            throw new IllegalArgumentException(
                field + " must be non-negative"
            );
        }

        return value;
    }

    private static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(field + " is required");
        }

        return value.trim();
    }

    private static String optionalText(String value) {
        return value == null || value.isBlank() ? null : value.trim();
    }

    private static Set<String> immutableSet(Set<String> source) {
        if (source == null) {
            return Collections.emptySet();
        }

        return source.stream()
            .map(value -> requireText(value, "scope value"))
            .collect(Collectors.toUnmodifiableSet());
    }

    private static Optional<BigDecimal> safeOptional(
        Optional<BigDecimal> value
    ) {
        return value == null ? Optional.empty() : value;
    }

    private static MonthlyPerformance row(
        String month,
        String unit,
        String region,
        String revenue,
        String target,
        String cogs,
        String expenses,
        long orders,
        long delivered,
        long onTime,
        String csatSum,
        long responses
    ) {
        return new MonthlyPerformance(
            YearMonth.parse(month),
            unit,
            region,
            new BigDecimal(revenue),
            new BigDecimal(target),
            new BigDecimal(cogs),
            new BigDecimal(expenses),
            orders,
            delivered,
            onTime,
            new BigDecimal(csatSum),
            responses
        );
    }

    private static List<MonthlyPerformance> sampleData() {
        return List.of(
            row("2026-01", "Consumer", "North", "420000", "400000", "252000", "96000", 1200, 1160, 1080, "792", 180),
            row("2026-01", "Consumer", "South", "360000", "380000", "223200", "80000", 1050, 1000, 910, "615", 150),
            row("2026-01", "Enterprise", "North", "610000", "600000", "335500", "160000", 640, 620, 595, "414", 90),
            row("2026-01", "Enterprise", "South", "490000", "510000", "274400", "128000", 520, 500, 465, "344", 80),

            row("2026-02", "Consumer", "North", "440000", "420000", "264000", "99000", 1240, 1205, 1130, "810", 185),
            row("2026-02", "Consumer", "South", "370000", "385000", "229400", "83000", 1080, 1035, 950, "640", 155),
            row("2026-02", "Enterprise", "North", "635000", "620000", "349250", "165000", 660, 642, 615, "423", 92),
            row("2026-02", "Enterprise", "South", "505000", "520000", "282800", "131000", 535, 516, 480, "356", 82),

            row("2026-03", "Consumer", "North", "455000", "440000", "270725", "101000", 1280, 1250, 1180, "840", 190),
            row("2026-03", "Consumer", "South", "390000", "400000", "241800", "86000", 1120, 1080, 1000, "660", 160),
            row("2026-03", "Enterprise", "North", "660000", "650000", "363000", "170000", 680, 665, 640, "437", 95),
            row("2026-03", "Enterprise", "South", "530000", "535000", "296800", "135000", 550, 535, 500, "374", 85)
        );
    }

    private static String display(Optional<BigDecimal> value, String suffix) {
        return value.map(number -> number.toPlainString() + suffix)
            .orElse("Not available");
    }

    private static void printSnapshot(
        String heading,
        DashboardSnapshot snapshot
    ) {
        KpiSnapshot metrics = snapshot.kpis();

        System.out.println("\n" + heading);
        System.out.println("Role: " + snapshot.role());
        System.out.println("Visible records: " + snapshot.visibleRecordCount());
        System.out.println("Revenue: " + metrics.revenue());
        System.out.println("Revenue target: " + metrics.revenueTarget());
        System.out.println(
            "Revenue attainment: " +
            display(metrics.revenueAttainmentPct(), "%")
        );
        System.out.println("Gross profit: " + metrics.grossProfit());
        System.out.println(
            "Gross margin: " + display(metrics.grossMarginPct(), "%")
        );
        System.out.println("Operating profit: " + metrics.operatingProfit());
        System.out.println(
            "On-time delivery: " +
            display(metrics.onTimeDeliveryPct(), "%")
        );
        System.out.println(
            "Average CSAT: " + display(metrics.averageCsat(), "/5")
        );

        if (snapshot.alerts().isEmpty()) {
            System.out.println("Alerts: none");
        } else {
            snapshot.alerts().forEach(alert ->
                System.out.println(
                    alert.severity() + " " + alert.code() +
                    ": " + alert.message()
                )
            );
        }
    }

    public static void main(String[] args) {
        try {
            List<MetricPolicy> policies = List.of(
                new RevenueAttainmentPolicy(new BigDecimal("100")),
                new GrossMarginPolicy(new BigDecimal("35")),
                new DeliveryPolicy(new BigDecimal("90")),
                new CustomerSatisfactionPolicy(new BigDecimal("4.00"))
            );

            DashboardService service = new DashboardService(
                sampleData(),
                policies
            );

            DashboardRequest allRegions = new DashboardRequest(
                YearMonth.of(2026, 1),
                YearMonth.of(2026, 3),
                null,
                null
            );

            AccessScope executiveScope = new AccessScope(
                Role.EXECUTIVE,
                Set.of(),
                Set.of()
            );

            DashboardSnapshot executiveSnapshot = service.build(
                allRegions,
                executiveScope
            );

            if (executiveSnapshot.visibleRecordCount() != 12) {
                throw new IllegalStateException(
                    "Unexpected executive record count"
                );
            }

            printSnapshot("EXECUTIVE DASHBOARD", executiveSnapshot);

            AccessScope northManagerScope = new AccessScope(
                Role.REGIONAL_MANAGER,
                Set.of("North"),
                Set.of()
            );

            DashboardSnapshot northSnapshot = service.build(
                allRegions,
                northManagerScope
            );

            printSnapshot("NORTH REGIONAL DASHBOARD", northSnapshot);

            DashboardRequest unauthorizedRequest = new DashboardRequest(
                YearMonth.of(2026, 1),
                YearMonth.of(2026, 3),
                "South",
                null
            );

            try {
                service.build(unauthorizedRequest, northManagerScope);
                throw new IllegalStateException(
                    "Unauthorized region request was accepted"
                );
            } catch (AccessDeniedException expected) {
                System.out.println(
                    "\nAccess-control check passed: " + expected.getMessage()
                );
            }

        } catch (RuntimeException error) {
            System.err.println("Dashboard service failed: " + error.getMessage());
            System.exit(1);
        }
    }
}
