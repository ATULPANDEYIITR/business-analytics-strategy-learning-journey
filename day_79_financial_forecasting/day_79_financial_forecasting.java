import java.time.YearMonth;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/*
 * Enterprise Financial Forecasting System.
 *
 * Java 17
 * Standard library only.
 *
 * Includes:
 * - Immutable financial domain records
 * - Historical financial data repository
 * - Forecasting services
 * - Revenue and expense growth models
 * - Scenario policies
 * - Cash-flow projections
 * - Budget variance analysis
 * - Cash runway calculations
 * - Financial controls and audit events
 * - Enterprise approval and policy evaluation
 * - Automated validation
 */

public class FinancialForecasting {

    enum Scenario {
        BASE,
        OPTIMISTIC,
        PESSIMISTIC
    }

    enum CashStatus {
        HEALTHY,
        LOW_CASH,
        NEGATIVE_CASH
    }

    enum ReviewState {
        APPROVED,
        CHANGES_REQUESTED,
        COMMENTED,
        DISMISSED
    }

    static class FinancialException extends RuntimeException {
        FinancialException(String message) {
            super(message);
        }
    }

    static class ValidationException extends FinancialException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class InsufficientDataException extends FinancialException {
        InsufficientDataException(String message) {
            super(message);
        }
    }

    static class PolicyViolationException extends FinancialException {
        PolicyViolationException(String message) {
            super(message);
        }
    }

    static void validateFinite(double value, String field) {
        if (!Double.isFinite(value)) {
            throw new ValidationException(
                field + " must be finite."
            );
        }
    }

    static void validateNonnegative(double value, String field) {
        validateFinite(value, field);

        if (value < 0) {
            throw new ValidationException(
                field + " cannot be negative."
            );
        }
    }

    record FinancialPeriod(
        YearMonth period,
        double revenue,
        double operatingExpenses,
        double investingExpenses,
        double financingCashFlow,
        double openingCash
    ) {
        FinancialPeriod {
            Objects.requireNonNull(period, "Period is required.");

            validateNonnegative(revenue, "Revenue");
            validateNonnegative(
                operatingExpenses,
                "Operating expenses"
            );
            validateNonnegative(
                investingExpenses,
                "Investing expenses"
            );
            validateFinite(financingCashFlow, "Financing cash flow");
            validateNonnegative(openingCash, "Opening cash");
        }

        double operatingProfit() {
            return revenue - operatingExpenses;
        }

        double netCashFlow() {
            return operatingProfit()
                - investingExpenses
                + financingCashFlow;
        }

        double closingCash() {
            return openingCash + netCashFlow();
        }
    }

    record ForecastPolicy(
        int horizon,
        int movingAverageWindow,
        double optimisticAdjustment,
        double pessimisticAdjustment,
        double expenseAdjustment
    ) {
        ForecastPolicy {
            if (horizon < 1 || horizon > 120) {
                throw new ValidationException(
                    "Horizon must be between 1 and 120."
                );
            }

            if (movingAverageWindow < 1) {
                throw new ValidationException(
                    "Moving-average window must be positive."
                );
            }

            validateFinite(
                optimisticAdjustment,
                "Optimistic adjustment"
            );

            validateFinite(
                pessimisticAdjustment,
                "Pessimistic adjustment"
            );

            validateFinite(
                expenseAdjustment,
                "Expense adjustment"
            );
        }

        static ForecastPolicy defaults() {
            return new ForecastPolicy(
                6,
                3,
                0.05,
                -0.05,
                0.02
            );
        }
    }

    record ForecastResult(
        YearMonth period,
        Scenario scenario,
        double revenue,
        double operatingExpenses,
        double investingExpenses,
        double operatingProfit,
        double netCashFlow,
        double openingCash,
        double closingCash,
        double profitMargin,
        CashStatus cashStatus
    ) {}

    record ForecastBatch(
        UUID forecastId,
        long sourceRevision,
        Scenario scenario,
        List<ForecastResult> results
    ) {
        ForecastBatch {
            Objects.requireNonNull(forecastId);
            Objects.requireNonNull(scenario);
            results = List.copyOf(results);
        }
    }

    static class FinancialRepository {
        private final Map<YearMonth, FinancialPeriod> records =
            new java.util.TreeMap<>();

        private long revision = 0;

        synchronized void add(FinancialPeriod record) {
            Objects.requireNonNull(record);

            if (records.containsKey(record.period())) {
                throw new ValidationException(
                    "Duplicate financial period: " + record.period()
                );
            }

            records.put(record.period(), record);
            revision++;
        }

        synchronized List<FinancialPeriod> snapshot() {
            return List.copyOf(records.values());
        }

        synchronized long revision() {
            return revision;
        }

        synchronized FinancialPeriod latest() {
            if (records.isEmpty()) {
                throw new InsufficientDataException(
                    "No financial observations available."
                );
            }

            return ((java.util.TreeMap<YearMonth, FinancialPeriod>)
                records).lastEntry().getValue();
        }
    }

    interface GrowthModel {
        double calculate(List<Double> values);
    }

    static class CompoundGrowthModel implements GrowthModel {

        @Override
        public double calculate(List<Double> values) {
            if (values.size() < 2) {
                return 0;
            }

            values.forEach(
                value -> validateNonnegative(value, "Growth observation")
            );

            double first = values.get(0);
            double last = values.get(values.size() - 1);

            if (first > 0) {
                return Math.pow(
                    last / first,
                    1.0 / (values.size() - 1)
                ) - 1;
            }

            double total = 0;

            for (int i = 1; i < values.size(); i++) {
                total += (
                    values.get(i) - values.get(i - 1)
                ) / Math.max(Math.abs(values.get(i - 1)), 1.0);
            }

            return total / (values.size() - 1);
        }
    }

    static class ScenarioPolicy {
        private final ForecastPolicy policy;

        ScenarioPolicy(ForecastPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        double revenueAdjustment(Scenario scenario) {
            return switch (scenario) {
                case BASE -> 0;
                case OPTIMISTIC -> policy.optimisticAdjustment();
                case PESSIMISTIC -> policy.pessimisticAdjustment();
            };
        }

        double expenseAdjustment(Scenario scenario) {
            return scenario == Scenario.PESSIMISTIC
                ? policy.expenseAdjustment()
                : 0;
        }
    }

    static class ForecastService {
        private final FinancialRepository repository;
        private final ForecastPolicy policy;
        private final ScenarioPolicy scenarioPolicy;
        private final GrowthModel growthModel;

        ForecastService(
            FinancialRepository repository,
            ForecastPolicy policy
        ) {
            this.repository = Objects.requireNonNull(repository);
            this.policy = Objects.requireNonNull(policy);
            this.scenarioPolicy = new ScenarioPolicy(policy);
            this.growthModel = new CompoundGrowthModel();
        }

        private double movingAverage(
            List<Double> values,
            int window
        ) {
            if (values.isEmpty()) {
                throw new InsufficientDataException(
                    "No observations available."
                );
            }

            int start = Math.max(0, values.size() - window);

            return values.subList(start, values.size())
                .stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElseThrow();
        }

        ForecastBatch forecast(Scenario scenario) {
            Objects.requireNonNull(scenario);

            // Snapshot prevents concurrent inserts from changing this run.
            List<FinancialPeriod> records = repository.snapshot();

            if (records.size() < policy.movingAverageWindow()) {
                throw new InsufficientDataException(
                    "Insufficient historical records."
                );
            }

            List<Double> revenues = records.stream()
                .map(FinancialPeriod::revenue)
                .toList();

            List<Double> expenses = records.stream()
                .map(FinancialPeriod::operatingExpenses)
                .toList();

            List<Double> investments = records.stream()
                .map(FinancialPeriod::investingExpenses)
                .toList();

            double revenueGrowth =
                growthModel.calculate(revenues)
                + scenarioPolicy.revenueAdjustment(scenario);

            double expenseGrowth =
                growthModel.calculate(expenses)
                + scenarioPolicy.expenseAdjustment(scenario);

            revenueGrowth = Math.max(
                -0.95,
                Math.min(1.0, revenueGrowth)
            );

            expenseGrowth = Math.max(
                -0.95,
                Math.min(1.0, expenseGrowth)
            );

            double revenue = movingAverage(
                revenues,
                policy.movingAverageWindow()
            );

            double operatingExpenses = movingAverage(
                expenses,
                policy.movingAverageWindow()
            );

            double investingExpenses = movingAverage(
                investments,
                policy.movingAverageWindow()
            );

            FinancialPeriod latest = records.get(records.size() - 1);

            double cash = latest.closingCash();
            YearMonth period = latest.period().plusMonths(1);

            List<ForecastResult> results = new ArrayList<>();

            for (int i = 0; i < policy.horizon(); i++) {
                revenue *= 1 + revenueGrowth;
                operatingExpenses *= 1 + expenseGrowth;

                double profit = revenue - operatingExpenses;
                double netCashFlow = profit - investingExpenses;

                double openingCash = cash;
                double closingCash = openingCash + netCashFlow;

                double margin = revenue > 0
                    ? profit / revenue
                    : 0;

                CashStatus status;

                if (closingCash < 0) {
                    status = CashStatus.NEGATIVE_CASH;
                } else if (closingCash < operatingExpenses) {
                    status = CashStatus.LOW_CASH;
                } else {
                    status = CashStatus.HEALTHY;
                }

                results.add(new ForecastResult(
                    period,
                    scenario,
                    round(revenue),
                    round(operatingExpenses),
                    round(investingExpenses),
                    round(profit),
                    round(netCashFlow),
                    round(openingCash),
                    round(closingCash),
                    round(margin),
                    status
                ));

                cash = closingCash;
                period = period.plusMonths(1);
            }

            return new ForecastBatch(
                UUID.randomUUID(),
                repository.revision(),
                scenario,
                results
            );
        }
    }

    record BudgetVariance(
        double actual,
        double budget,
        double variance,
        Double percentage,
        boolean favorable
    ) {}

    static class FinancialAnalytics {

        static BudgetVariance compareBudget(
            double actual,
            double budget
        ) {
            validateNonnegative(actual, "Actual");
            validateNonnegative(budget, "Budget");

            double variance = actual - budget;

            Double percentage = budget == 0
                ? null
                : variance / Math.abs(budget) * 100;

            return new BudgetVariance(
                actual,
                budget,
                round(variance),
                percentage == null ? null : round(percentage),
                variance >= 0
            );
        }

        static double totalRevenue(ForecastBatch batch) {
            return batch.results().stream()
                .mapToDouble(ForecastResult::revenue)
                .sum();
        }

        static double totalOperatingProfit(ForecastBatch batch) {
            return batch.results().stream()
                .mapToDouble(ForecastResult::operatingProfit)
                .sum();
        }

        static double averageProfitMargin(ForecastBatch batch) {
            return batch.results().stream()
                .mapToDouble(ForecastResult::profitMargin)
                .average()
                .orElse(0);
        }

        static Double cashRunway(
            double cash,
            double monthlyBurn
        ) {
            validateNonnegative(cash, "Cash");
            validateNonnegative(monthlyBurn, "Monthly burn");

            return monthlyBurn == 0
                ? null
                : round(cash / monthlyBurn);
        }
    }

    record Review(
        String reviewerId,
        boolean eligibleReviewer,
        ReviewState state,
        boolean stale,
        boolean dismissed
    ) {
        Review {
            if (reviewerId == null || reviewerId.isBlank()) {
                throw new ValidationException(
                    "Reviewer identifier is required."
                );
            }

            Objects.requireNonNull(state);
        }

        boolean isValidApproval() {
            return eligibleReviewer
                && state == ReviewState.APPROVED
                && !stale
                && !dismissed;
        }
    }

    record RepositoryPolicy(
        int requiredApprovals,
        boolean requirePassingChecks,
        boolean requireResolvedConversations,
        boolean prohibitDirectPush,
        boolean prohibitForcePush
    ) {
        RepositoryPolicy {
            if (requiredApprovals < 0) {
                throw new ValidationException(
                    "Approval requirement cannot be negative."
                );
            }
        }
    }

    record PullRequestState(
        boolean open,
        boolean draft,
        boolean mergeConflict,
        boolean checksPassing,
        boolean conversationsResolved,
        boolean protectedBranch,
        boolean directPush,
        boolean forcePush,
        List<Review> reviews
    ) {
        PullRequestState {
            reviews = List.copyOf(reviews);
        }
    }

    record MergeDecision(
        boolean eligible,
        List<String> blockers,
        int validApprovals
    ) {
        MergeDecision {
            blockers = List.copyOf(blockers);
        }
    }

    static class MergeEligibilityService {

        MergeDecision evaluate(
            PullRequestState pullRequest,
            RepositoryPolicy policy
        ) {
            List<String> blockers = new ArrayList<>();

            if (!pullRequest.open()) {
                blockers.add("Pull Request is closed.");
            }

            if (pullRequest.draft()) {
                blockers.add("Draft Pull Request cannot be merged.");
            }

            if (pullRequest.mergeConflict()) {
                blockers.add("Merge conflict must be resolved.");
            }

            if (
                policy.requirePassingChecks() &&
                !pullRequest.checksPassing()
            ) {
                blockers.add("Required status checks are failing.");
            }

            if (
                policy.requireResolvedConversations() &&
                !pullRequest.conversationsResolved()
            ) {
                blockers.add("Review conversations remain unresolved.");
            }

            if (
                pullRequest.protectedBranch() &&
                policy.prohibitDirectPush() &&
                pullRequest.directPush()
            ) {
                blockers.add("Direct push violates branch policy.");
            }

            if (
                pullRequest.protectedBranch() &&
                policy.prohibitForcePush() &&
                pullRequest.forcePush()
            ) {
                blockers.add("Force push violates branch policy.");
            }

            Set<String> approvedReviewers = pullRequest.reviews()
                .stream()
                .filter(Review::isValidApproval)
                .map(Review::reviewerId)
                .collect(Collectors.toCollection(HashSet::new));

            int approvals = approvedReviewers.size();

            if (
                pullRequest.protectedBranch() &&
                approvals < policy.requiredApprovals()
            ) {
                blockers.add(
                    "Required independent approvals are missing."
                );
            }

            return new MergeDecision(
                blockers.isEmpty(),
                blockers,
                approvals
            );
        }
    }

    record AuditEvent(
        UUID eventId,
        String action,
        String details,
        java.time.Instant timestamp
    ) {}

    static class AuditService {
        private final List<AuditEvent> events =
            new ArrayList<>();

        void record(String action, String details) {
            events.add(new AuditEvent(
                UUID.randomUUID(),
                action,
                details,
                java.time.Instant.now()
            ));
        }

        List<AuditEvent> events() {
            return Collections.unmodifiableList(events);
        }
    }

    static double round(double value) {
        return Math.round(value * 100.0) / 100.0;
    }

    static FinancialRepository createSampleRepository() {
        FinancialRepository repository = new FinancialRepository();

        repository.add(new FinancialPeriod(
            YearMonth.parse("2026-01"),
            850000, 520000, 65000, 20000, 300000
        ));

        repository.add(new FinancialPeriod(
            YearMonth.parse("2026-02"),
            875000, 530000, 70000, 0, 595000
        ));

        repository.add(new FinancialPeriod(
            YearMonth.parse("2026-03"),
            900000, 540000, 60000, -10000, 870000
        ));

        repository.add(new FinancialPeriod(
            YearMonth.parse("2026-04"),
            925000, 555000, 75000, 15000, 1155000
        ));

        repository.add(new FinancialPeriod(
            YearMonth.parse("2026-05"),
            960000, 565000, 80000, 0, 1465000
        ));

        repository.add(new FinancialPeriod(
            YearMonth.parse("2026-06"),
            990000, 580000, 70000, 10000, 1780000
        ));

        return repository;
    }

    static void runTests(
        ForecastService service
    ) {
        ForecastBatch base = service.forecast(Scenario.BASE);
        ForecastBatch optimistic =
            service.forecast(Scenario.OPTIMISTIC);
        ForecastBatch pessimistic =
            service.forecast(Scenario.PESSIMISTIC);

        if (base.results().size() != 6) {
            throw new AssertionError("Horizon test failed.");
        }

        if (
            optimistic.results().get(0).revenue()
            <= base.results().get(0).revenue()
        ) {
            throw new AssertionError("Optimistic scenario failed.");
        }

        if (
            pessimistic.results().get(0).revenue()
            >= base.results().get(0).revenue()
        ) {
            throw new AssertionError("Pessimistic scenario failed.");
        }

        BudgetVariance variance =
            FinancialAnalytics.compareBudget(950, 1000);

        if (variance.variance() != -50) {
            throw new AssertionError("Budget variance failed.");
        }

        if (FinancialAnalytics.cashRunway(10000, 2000) != 5.0) {
            throw new AssertionError("Cash runway failed.");
        }

        MergeEligibilityService mergeService =
            new MergeEligibilityService();

        RepositoryPolicy policy = new RepositoryPolicy(
            2, true, true, true, true
        );

        PullRequestState pullRequest = new PullRequestState(
            true,
            false,
            false,
            true,
            true,
            true,
            false,
            false,
            List.of(
                new Review(
                    "reviewer-1",
                    true,
                    ReviewState.APPROVED,
                    false,
                    false
                ),
                new Review(
                    "reviewer-2",
                    true,
                    ReviewState.APPROVED,
                    false,
                    false
                )
            )
        );

        MergeDecision decision = mergeService.evaluate(
            pullRequest,
            policy
        );

        if (!decision.eligible()) {
            throw new AssertionError("Merge policy test failed.");
        }

        try {
            YearMonth.parse("2026-13");
            throw new AssertionError("Invalid date accepted.");
        } catch (DateTimeParseException expected) {
            // Expected validation failure.
        }
    }

    public static void main(String[] args) {
        try {
            FinancialRepository repository =
                createSampleRepository();

            ForecastPolicy policy =
                ForecastPolicy.defaults();

            ForecastService service =
                new ForecastService(repository, policy);

            AuditService audit = new AuditService();

            audit.record(
                "FORECAST_STARTED",
                "Historical records: " + repository.snapshot().size()
            );

            runTests(service);

            System.out.println(
                "ENTERPRISE FINANCIAL FORECASTING SYSTEM"
            );

            System.out.println("=".repeat(100));

            Map<Scenario, ForecastBatch> forecasts =
                new EnumMap<>(Scenario.class);

            for (Scenario scenario : Scenario.values()) {
                ForecastBatch batch = service.forecast(scenario);
                forecasts.put(scenario, batch);

                System.out.println(
                    "\nSCENARIO: " + scenario
                );

                for (ForecastResult result : batch.results()) {
                    System.out.printf(
                        "%s | Revenue: %12.2f | Expenses: %12.2f "
                        + "| Profit: %12.2f | Closing cash: %12.2f "
                        + "| %s%n",
                        result.period(),
                        result.revenue(),
                        result.operatingExpenses(),
                        result.operatingProfit(),
                        result.closingCash(),
                        result.cashStatus()
                    );
                }

                System.out.printf(
                    "Total revenue: %.2f%n",
                    FinancialAnalytics.totalRevenue(batch)
                );

                System.out.printf(
                    "Total operating profit: %.2f%n",
                    FinancialAnalytics.totalOperatingProfit(batch)
                );

                System.out.printf(
                    "Average profit margin: %.2f%%%n",
                    FinancialAnalytics.averageProfitMargin(batch) * 100
                );

                System.out.printf(
                    "Ending cash: %.2f%n",
                    batch.results().get(
                        batch.results().size() - 1
                    ).closingCash()
                );
            }

            BudgetVariance variance =
                FinancialAnalytics.compareBudget(
                    950000,
                    1000000
                );

            System.out.println("\nBUDGET ANALYSIS");
            System.out.println("Variance: " + variance.variance());
            System.out.println(
                "Variance percentage: " + variance.percentage()
            );

            System.out.println("\nAUDIT EVENTS");

            for (AuditEvent event : audit.events()) {
                System.out.println(
                    event.timestamp() + " | "
                    + event.action() + " | "
                    + event.details()
                );
            }

            System.out.println("\nAll validation tests passed.");

        } catch (FinancialException exception) {
            System.err.println(
                "FINANCIAL ERROR: " + exception.getMessage()
            );

            System.exit(1);
        } catch (Exception exception) {
            System.err.println(
                "SYSTEM ERROR: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
