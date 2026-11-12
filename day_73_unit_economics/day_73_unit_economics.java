import java.util.*;
import java.time.*;
import java.math.BigDecimal;
import java.math.RoundingMode;

public class UnitEconomicsEnterprise {

    enum Channel {
        ORGANIC,
        PAID_SEARCH,
        SOCIAL,
        REFERRAL,
        PARTNERSHIP
    }

    enum CustomerStatus {
        ACTIVE,
        CHURNED,
        SUSPENDED
    }

    enum ReviewState {
        PENDING,
        APPROVED,
        CHANGES_REQUESTED,
        DISMISSED
    }

    enum PullRequestState {
        DRAFT,
        OPEN,
        CLOSED,
        MERGED
    }

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    static class Validation {

        static double nonNegative(double value, String field) {
            if (!Double.isFinite(value) || value < 0) {
                throw new DomainException(
                    field + " must be finite and non-negative."
                );
            }
            return value;
        }

        static double positive(double value, String field) {
            if (!Double.isFinite(value) || value <= 0) {
                throw new DomainException(
                    field + " must be positive."
                );
            }
            return value;
        }

        static double rate(double value, String field) {
            if (!Double.isFinite(value) || value < 0 || value >= 1) {
                throw new DomainException(
                    field + " must be between 0 inclusive and 1 exclusive."
                );
            }
            return value;
        }
    }

    record Acquisition(
        Channel channel,
        double advertisingCost,
        double salesCost,
        double marketingCost,
        int newCustomers,
        YearMonth period
    ) {
        Acquisition {
            Objects.requireNonNull(channel);
            Objects.requireNonNull(period);

            Validation.nonNegative(advertisingCost, "Advertising cost");
            Validation.nonNegative(salesCost, "Sales cost");
            Validation.nonNegative(marketingCost, "Marketing cost");

            if (newCustomers <= 0) {
                throw new DomainException(
                    "New customer count must be positive."
                );
            }
        }

        double totalCost() {
            return advertisingCost + salesCost + marketingCost;
        }

        double cac() {
            return totalCost() / newCustomers;
        }
    }

    record Customer(
        String id,
        String cohort,
        Channel channel,
        double monthlyRevenue,
        double variableCost,
        double lifetimeMonths,
        double monthlyChurnRate,
        CustomerStatus status
    ) {
        Customer {
            if (id == null || id.isBlank()) {
                throw new DomainException("Customer ID is required.");
            }

            if (cohort == null || cohort.isBlank()) {
                throw new DomainException("Cohort is required.");
            }

            Objects.requireNonNull(channel);
            Objects.requireNonNull(status);

            Validation.nonNegative(monthlyRevenue, "Revenue");
            Validation.nonNegative(variableCost, "Variable cost");
            Validation.positive(lifetimeMonths, "Lifetime");
            Validation.rate(monthlyChurnRate, "Churn rate");

            if (monthlyRevenue == 0 && variableCost > 0) {
                throw new DomainException(
                    "Variable cost cannot exceed zero revenue."
                );
            }
        }

        double contribution() {
            return monthlyRevenue - variableCost;
        }

        double contributionMargin() {
            return monthlyRevenue == 0
                ? 0
                : contribution() / monthlyRevenue;
        }
    }

    record UnitEconomics(
        double cac,
        double monthlyContribution,
        double contributionMarginPercent,
        double grossLtv,
        double contributionLtv,
        double ltvCacRatio,
        Optional<Double> paybackMonths,
        String classification
    ) {}

    interface EconomicsService {
        UnitEconomics calculate(
            Acquisition acquisition,
            Customer customer
        );
    }

    static class DefaultEconomicsService implements EconomicsService {

        @Override
        public UnitEconomics calculate(
            Acquisition acquisition,
            Customer customer
        ) {
            if (acquisition.channel() != customer.channel()) {
                throw new DomainException("Acquisition channel mismatch.");
            }

            double cac = acquisition.cac();
            double contribution = customer.contribution();

            double margin = customer.contributionMargin() * 100;

            double grossLtv =
                customer.monthlyRevenue() * customer.lifetimeMonths();

            double contributionLtv =
                contribution * customer.lifetimeMonths();

            Optional<Double> payback = contribution > 0
                ? Optional.of(cac / contribution)
                : Optional.empty();

            double ratio = cac > 0
                ? contributionLtv / cac
                : contributionLtv > 0
                    ? Double.POSITIVE_INFINITY
                    : 0;

            String classification;

            if (contribution <= 0) {
                classification = "NEGATIVE_CONTRIBUTION";
            } else if (contributionLtv <= cac) {
                classification = "UNPROFITABLE";
            } else if (payback.isPresent() &&
                       payback.get() <= customer.lifetimeMonths()) {
                classification = "LIFETIME_POSITIVE";
            } else {
                classification = "PAYBACK_EXCEEDS_LIFETIME";
            }

            return new UnitEconomics(
                round(cac),
                round(contribution),
                round(margin),
                round(grossLtv),
                round(contributionLtv),
                Double.isFinite(ratio) ? round(ratio) : ratio,
                payback.map(DefaultEconomicsService::round),
                classification
            );
        }

        private static double round(double value) {
            return BigDecimal.valueOf(value)
                .setScale(2, RoundingMode.HALF_UP)
                .doubleValue();
        }
    }

    record Review(
        String reviewerId,
        ReviewState state,
        boolean eligible,
        boolean stale,
        boolean changesResolved
    ) {
        Review {
            if (reviewerId == null || reviewerId.isBlank()) {
                throw new DomainException("Reviewer ID is required.");
            }
            Objects.requireNonNull(state);
        }
    }

    record StatusChecks(
        boolean financialValidation,
        boolean dataQuality,
        boolean securityAudit
    ) {
        boolean passed() {
            return financialValidation && dataQuality && securityAudit;
        }
    }

    record BranchProtectionPolicy(
        int requiredApprovals,
        boolean requireStatusChecks,
        boolean requireResolvedConversations,
        boolean prohibitDirectPush,
        boolean prohibitForcePush,
        boolean requireLinearHistory,
        double minimumLtvCacRatio,
        double maximumPaybackMonths,
        boolean administratorBypassAllowed
    ) {
        BranchProtectionPolicy {
            if (requiredApprovals < 0) {
                throw new DomainException("Invalid approval requirement.");
            }

            Validation.positive(
                minimumLtvCacRatio,
                "Minimum LTV/CAC ratio"
            );

            Validation.positive(
                maximumPaybackMonths,
                "Maximum payback"
            );
        }
    }

    static class PullRequest {

        private final int id;
        private final String sourceBranch;
        private final String targetBranch;

        private String baseCommit;
        private String headCommit;

        private PullRequestState state = PullRequestState.DRAFT;

        private boolean mergeConflict;
        private boolean directPush;
        private boolean forcePush;
        private boolean linearHistory = true;

        private int unresolvedConversations;

        private StatusChecks checks =
            new StatusChecks(false, false, false);

        private UnitEconomics economics;

        private final List<Review> reviews = new ArrayList<>();

        PullRequest(
            int id,
            String sourceBranch,
            String targetBranch,
            String baseCommit,
            String headCommit
        ) {
            if (id <= 0) {
                throw new DomainException("Invalid Pull Request ID.");
            }

            if (sourceBranch == null || sourceBranch.isBlank() ||
                targetBranch == null || targetBranch.isBlank()) {
                throw new DomainException("Branch names are required.");
            }

            if (sourceBranch.equals(targetBranch)) {
                throw new DomainException(
                    "Source and target branches must differ."
                );
            }

            this.id = id;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.baseCommit = Objects.requireNonNull(baseCommit);
            this.headCommit = Objects.requireNonNull(headCommit);
        }

        void open() {
            if (state != PullRequestState.DRAFT &&
                state != PullRequestState.CLOSED) {
                throw new DomainException("Invalid opening transition.");
            }

            state = PullRequestState.OPEN;
        }

        void close() {
            if (state != PullRequestState.OPEN &&
                state != PullRequestState.DRAFT) {
                throw new DomainException("Pull Request cannot be closed.");
            }

            state = PullRequestState.CLOSED;
        }

        void reopen() {
            if (state != PullRequestState.CLOSED) {
                throw new DomainException(
                    "Only closed Pull Requests can be reopened."
                );
            }

            state = PullRequestState.OPEN;
        }

        void synchronizeBase(String newBaseCommit) {
            if (state != PullRequestState.OPEN) {
                throw new DomainException(
                    "Only open Pull Requests can synchronize."
                );
            }

            baseCommit = Objects.requireNonNull(newBaseCommit);

            // Synchronization can invalidate earlier review decisions.
            reviews.replaceAll(review ->
                new Review(
                    review.reviewerId(),
                    review.state(),
                    review.eligible(),
                    true,
                    review.changesResolved()
                )
            );
        }

        void addReview(Review review) {
            if (state != PullRequestState.OPEN) {
                throw new DomainException(
                    "Reviews require an open Pull Request."
                );
            }

            reviews.add(Objects.requireNonNull(review));
        }

        void setChecks(StatusChecks checks) {
            this.checks = Objects.requireNonNull(checks);
        }

        void setEconomics(UnitEconomics economics) {
            this.economics = Objects.requireNonNull(economics);
        }

        void setUnresolvedConversations(int count) {
            if (count < 0) {
                throw new DomainException("Invalid conversation count.");
            }

            unresolvedConversations = count;
        }

        void setMergeConflict(boolean value) {
            mergeConflict = value;
        }

        void setDirectPush(boolean value) {
            directPush = value;
        }

        void setForcePush(boolean value) {
            forcePush = value;
        }

        void setLinearHistory(boolean value) {
            linearHistory = value;
        }

        int id() {
            return id;
        }

        String sourceBranch() {
            return sourceBranch;
        }

        String targetBranch() {
            return targetBranch;
        }

        String baseCommit() {
            return baseCommit;
        }

        String headCommit() {
            return headCommit;
        }

        PullRequestState state() {
            return state;
        }

        boolean hasMergeConflict() {
            return mergeConflict;
        }

        boolean directPush() {
            return directPush;
        }

        boolean forcePush() {
            return forcePush;
        }

        boolean linearHistory() {
            return linearHistory;
        }

        int unresolvedConversations() {
            return unresolvedConversations;
        }

        StatusChecks checks() {
            return checks;
        }

        UnitEconomics economics() {
            return economics;
        }

        List<Review> reviews() {
            return Collections.unmodifiableList(reviews);
        }

        void markMerged() {
            if (state != PullRequestState.OPEN) {
                throw new DomainException("Pull Request is not open.");
            }

            state = PullRequestState.MERGED;
        }
    }

    record EligibilityResult(
        boolean eligible,
        List<String> violations
    ) {
        EligibilityResult {
            violations = List.copyOf(violations);
        }
    }

    static class MergeEligibilityService {

        private final BranchProtectionPolicy policy;

        MergeEligibilityService(BranchProtectionPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        EligibilityResult evaluate(PullRequest pr) {
            List<String> violations = new ArrayList<>();

            if (pr.state() != PullRequestState.OPEN) {
                violations.add("PULL_REQUEST_NOT_OPEN");
            }

            if (pr.hasMergeConflict()) {
                violations.add("MERGE_CONFLICT");
            }

            if (pr.directPush() && policy.prohibitDirectPush()) {
                violations.add("DIRECT_PUSH_PROHIBITED");
            }

            if (pr.forcePush() && policy.prohibitForcePush()) {
                violations.add("FORCE_PUSH_PROHIBITED");
            }

            if (policy.requireLinearHistory() && !pr.linearHistory()) {
                violations.add("LINEAR_HISTORY_REQUIRED");
            }

            if (policy.requireStatusChecks() && !pr.checks().passed()) {
                violations.add("STATUS_CHECKS_FAILED");
            }

            if (policy.requireResolvedConversations() &&
                pr.unresolvedConversations() > 0) {
                violations.add("UNRESOLVED_CONVERSATIONS");
            }

            Set<String> approvals = new HashSet<>();

            for (Review review : pr.reviews()) {
                if (review.eligible() &&
                    !review.stale() &&
                    review.state() == ReviewState.APPROVED) {
                    approvals.add(review.reviewerId());
                }

                if (review.eligible() &&
                    !review.stale() &&
                    review.state() == ReviewState.CHANGES_REQUESTED) {
                    violations.add("CHANGES_REQUESTED");
                }
            }

            if (approvals.size() < policy.requiredApprovals()) {
                violations.add("INSUFFICIENT_APPROVALS");
            }

            if (pr.economics() == null) {
                violations.add("ECONOMICS_NOT_EVALUATED");
            } else {
                UnitEconomics result = pr.economics();

                if (result.monthlyContribution() <= 0) {
                    violations.add("NON_POSITIVE_CONTRIBUTION");
                }

                if (result.ltvCacRatio() < policy.minimumLtvCacRatio()) {
                    violations.add("LTV_CAC_BELOW_POLICY");
                }

                if (result.paybackMonths().isEmpty() ||
                    result.paybackMonths().get() >
                        policy.maximumPaybackMonths()) {
                    violations.add("PAYBACK_EXCEEDS_POLICY");
                }
            }

            return new EligibilityResult(
                violations.isEmpty(),
                violations
            );
        }

        void merge(PullRequest pr) {
            EligibilityResult result = evaluate(pr);

            if (!result.eligible()) {
                throw new DomainException(
                    "Merge rejected: " + String.join(", ", result.violations())
                );
            }

            pr.markMerged();
        }
    }

    static class CohortAnalytics {

        static Map<String, Map<String, Double>> analyze(
            Collection<Customer> customers
        ) {
            Map<String, double[]> aggregates = new TreeMap<>();

            for (Customer customer : customers) {
                double[] values = aggregates.computeIfAbsent(
                    customer.cohort(),
                    key -> new double[3]
                );

                values[0]++;
                values[1] += customer.monthlyRevenue();
                values[2] += customer.variableCost();
            }

            Map<String, Map<String, Double>> results = new TreeMap<>();

            aggregates.forEach((cohort, values) -> {
                double contribution = values[1] - values[2];

                Map<String, Double> metrics = new LinkedHashMap<>();
                metrics.put("customers", values[0]);
                metrics.put("revenue", values[1]);
                metrics.put("variableCost", values[2]);
                metrics.put("contribution", contribution);
                metrics.put(
                    "marginPercent",
                    values[1] > 0 ? contribution / values[1] * 100 : 0
                );

                results.put(cohort, Collections.unmodifiableMap(metrics));
            });

            return Collections.unmodifiableMap(results);
        }
    }

    static void runTests(EconomicsService service) {
        Acquisition acquisition = new Acquisition(
            Channel.PAID_SEARCH,
            30000,
            10000,
            10000,
            100,
            YearMonth.of(2026, 1)
        );

        Customer customer = new Customer(
            "C001",
            "2026-Q1",
            Channel.PAID_SEARCH,
            1000,
            300,
            18,
            0.04,
            CustomerStatus.ACTIVE
        );

        UnitEconomics result = service.calculate(acquisition, customer);

        if (Math.abs(result.cac() - 500) > 0.001 ||
            Math.abs(result.monthlyContribution() - 700) > 0.001) {
            throw new AssertionError("Calculation test failed.");
        }

        if (Math.abs(
            result.paybackMonths().orElseThrow() - 500.0 / 700.0
        ) > 0.001) {
            throw new AssertionError("Payback test failed.");
        }

        System.out.println("Enterprise calculation tests passed.");
    }

    public static void main(String[] args) {

        try {
            EconomicsService service = new DefaultEconomicsService();

            runTests(service);

            Acquisition acquisition = new Acquisition(
                Channel.PAID_SEARCH,
                30000,
                10000,
                10000,
                100,
                YearMonth.of(2026, 1)
            );

            Customer customer = new Customer(
                "C001",
                "2026-Q1",
                Channel.PAID_SEARCH,
                1000,
                300,
                18,
                0.04,
                CustomerStatus.ACTIVE
            );

            UnitEconomics economics =
                service.calculate(acquisition, customer);

            System.out.println("\nUNIT ECONOMICS");
            System.out.println("CAC: INR " + economics.cac());
            System.out.println(
                "Contribution: INR " + economics.monthlyContribution()
            );
            System.out.println(
                "Contribution margin: " +
                economics.contributionMarginPercent() + "%"
            );
            System.out.println(
                "Gross LTV: INR " + economics.grossLtv()
            );
            System.out.println(
                "Contribution LTV: INR " + economics.contributionLtv()
            );
            System.out.println("LTV/CAC: " + economics.ltvCacRatio());
            System.out.println(
                "Payback: " + economics.paybackMonths().orElse(Double.NaN)
            );

            List<Customer> customers = List.of(
                customer,
                new Customer(
                    "C002", "2026-Q1", Channel.SOCIAL,
                    800, 280, 15, 0.05, CustomerStatus.ACTIVE
                ),
                new Customer(
                    "C003", "2026-Q2", Channel.REFERRAL,
                    1200, 350, 24, 0.025, CustomerStatus.ACTIVE
                )
            );

            System.out.println("\nCOHORT ANALYSIS");

            CohortAnalytics.analyze(customers).forEach(
                (cohort, metrics) ->
                    System.out.println(cohort + " -> " + metrics)
            );

            BranchProtectionPolicy policy =
                new BranchProtectionPolicy(
                    2,
                    true,
                    true,
                    true,
                    true,
                    true,
                    3.0,
                    12.0,
                    false
                );

            PullRequest pr = new PullRequest(
                101,
                "feature/unit-economics",
                "main",
                "base-001",
                "head-009"
            );

            pr.open();

            pr.setEconomics(economics);
            pr.setChecks(new StatusChecks(true, true, true));
            pr.setUnresolvedConversations(0);

            pr.addReview(new Review(
                "reviewer-01",
                ReviewState.APPROVED,
                true,
                false,
                true
            ));

            pr.addReview(new Review(
                "reviewer-02",
                ReviewState.APPROVED,
                true,
                false,
                true
            ));

            MergeEligibilityService mergeService =
                new MergeEligibilityService(policy);

            EligibilityResult eligibility =
                mergeService.evaluate(pr);

            System.out.println("\nMERGE ELIGIBILITY");
            System.out.println("Eligible: " + eligibility.eligible());
            System.out.println("Violations: " + eligibility.violations());

            if (eligibility.eligible()) {
                mergeService.merge(pr);
                System.out.println("Pull Request merged successfully.");
            }

        } catch (DomainException exception) {
            System.err.println(
                "Business rule violation: " + exception.getMessage()
            );
            System.exitCode = 1;
        } catch (Exception exception) {
            System.err.println(
                "Execution failure: " + exception.getMessage()
            );
            System.exitCode = 1;
        }
    }
}
