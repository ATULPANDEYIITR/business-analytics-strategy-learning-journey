import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class CohortGovernanceApplication {

    enum ReviewState {
        COMMENTED,
        CHANGES_REQUESTED,
        APPROVED,
        DISMISSED
    }

    enum MergeStrategy {
        MERGE_COMMIT,
        SQUASH,
        REBASE
    }

    record Customer(
        String id,
        String cohort,
        String channel,
        String plan
    ) {}

    record CustomerEvent(
        String customerId,
        int period,
        String eventType,
        double revenue
    ) {
        CustomerEvent {
            if (customerId == null || customerId.isBlank()) {
                throw new IllegalArgumentException("customerId is required");
            }

            if (period < 0) {
                throw new IllegalArgumentException("period cannot be negative");
            }

            if (revenue < 0) {
                throw new IllegalArgumentException("revenue cannot be negative");
            }
        }
    }

    record Review(
        String reviewer,
        ReviewState state,
        boolean eligible,
        boolean unresolvedConversation
    ) {}

    record StatusCheck(
        String name,
        boolean passed
    ) {}

    record BranchProtectionPolicy(
        String branchName,
        boolean protectedBranch,
        boolean directPushRestricted,
        boolean forcePushRestricted,
        boolean deletionRestricted,
        boolean requireLinearHistory,
        boolean requireConversationResolution,
        int requiredApprovals,
        Set<String> requiredChecks,
        Set<String> allowedMergeStrategies
    ) {
        BranchProtectionPolicy {
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                    "requiredApprovals cannot be negative"
                );
            }

            requiredChecks = Set.copyOf(requiredChecks);
            allowedMergeStrategies = Set.copyOf(allowedMergeStrategies);
        }
    }

    static final class PullRequest {
        private final int id;
        private final String sourceBranch;
        private final String targetBranch;
        private final Set<String> commits;
        private final List<Review> reviews;
        private final List<StatusCheck> checks;

        private boolean draft;
        private boolean conflicts;
        private boolean open;
        private boolean baseChangedAfterApproval;

        PullRequest(
            int id,
            String sourceBranch,
            String targetBranch,
            Set<String> commits
        ) {
            if (id <= 0) {
                throw new IllegalArgumentException("Pull Request ID must be positive");
            }

            if (sourceBranch == null || targetBranch == null
                || sourceBranch.isBlank() || targetBranch.isBlank()) {
                throw new IllegalArgumentException(
                    "Source and target branches are required"
                );
            }

            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException(
                    "Source and target branches cannot be identical"
                );
            }

            this.id = id;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.commits = new HashSet<>(commits);
            this.reviews = new ArrayList<>();
            this.checks = new ArrayList<>();
            this.open = true;
        }

        void setDraft(boolean draft) {
            this.draft = draft;
        }

        void setConflicts(boolean conflicts) {
            this.conflicts = conflicts;
        }

        void setBaseChangedAfterApproval(boolean changed) {
            this.baseChangedAfterApproval = changed;
        }

        void addReview(Review review) {
            reviews.add(review);
        }

        void addCheck(StatusCheck check) {
            checks.add(check);
        }

        int id() {
            return id;
        }

        String targetBranch() {
            return targetBranch;
        }

        Set<String> commits() {
            return Set.copyOf(commits);
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        List<StatusCheck> checks() {
            return List.copyOf(checks);
        }

        boolean isDraft() {
            return draft;
        }

        boolean hasConflicts() {
            return conflicts;
        }

        boolean isOpen() {
            return open;
        }

        boolean baseChangedAfterApproval() {
            return baseChangedAfterApproval;
        }
    }

    record MergeDecision(
        boolean eligible,
        List<String> blockers
    ) {}

    static final class MergeEligibilityService {

        MergeDecision evaluate(
            PullRequest pullRequest,
            BranchProtectionPolicy policy,
            MergeStrategy strategy
        ) {
            List<String> blockers = new ArrayList<>();

            if (!pullRequest.isOpen()) {
                blockers.add("Pull Request is closed");
            }

            if (pullRequest.isDraft()) {
                blockers.add("Pull Request is still a draft");
            }

            if (pullRequest.commits().isEmpty()) {
                blockers.add("Pull Request contains no commits");
            }

            if (pullRequest.hasConflicts()) {
                blockers.add("Merge conflicts are unresolved");
            }

            if (!policy.protectedBranch()) {
                return new MergeDecision(blockers.isEmpty(), List.copyOf(blockers));
            }

            if (!policy.allowedMergeStrategies()
                .contains(strategy.name().toLowerCase())) {
                blockers.add("Selected merge strategy is not allowed");
            }

            if (pullRequest.baseChangedAfterApproval()) {
                blockers.add(
                    "Base branch changed after approval and requires revalidation"
                );
            }

            Set<String> approvedReviewers = new HashSet<>();
            boolean changesRequested = false;
            boolean unresolvedConversation = false;

            for (Review review : pullRequest.reviews()) {
                if (review.unresolvedConversation()) {
                    unresolvedConversation = true;
                }

                if (!review.eligible()) {
                    continue;
                }

                if (review.state() == ReviewState.CHANGES_REQUESTED) {
                    changesRequested = true;
                }

                if (review.state() == ReviewState.APPROVED) {
                    approvedReviewers.add(review.reviewer());
                }
            }

            if (changesRequested) {
                blockers.add("An eligible reviewer requested changes");
            }

            if (policy.requireConversationResolution()
                && unresolvedConversation) {
                blockers.add("Review conversations remain unresolved");
            }

            if (approvedReviewers.size() < policy.requiredApprovals()) {
                blockers.add(
                    "Required number of eligible approvals has not been reached"
                );
            }

            Map<String, Boolean> checks = new HashMap<>();

            for (StatusCheck check : pullRequest.checks()) {
                checks.put(check.name(), check.passed());
            }

            for (String required : policy.requiredChecks()) {
                if (!checks.containsKey(required)) {
                    blockers.add("Required status check is missing: " + required);
                } else if (!checks.get(required)) {
                    blockers.add("Required status check failed: " + required);
                }
            }

            return new MergeDecision(
                blockers.isEmpty(),
                List.copyOf(blockers)
            );
        }
    }

    static final class CohortService {

        private final List<Customer> customers;
        private final List<CustomerEvent> events;

        CohortService(
            List<Customer> customers,
            List<CustomerEvent> events
        ) {
            this.customers = List.copyOf(customers);
            this.events = List.copyOf(events);
        }

        Map<String, Set<String>> activeCustomers() {
            Map<String, Set<String>> activity = new HashMap<>();
            Map<String, Customer> index = new HashMap<>();

            for (Customer customer : customers) {
                if (index.put(customer.id(), customer) != null) {
                    throw new IllegalStateException(
                        "Duplicate customer: " + customer.id()
                    );
                }
            }

            for (CustomerEvent event : events) {
                Customer customer = index.get(event.customerId());

                if (customer == null) {
                    throw new IllegalStateException(
                        "Unknown customer: " + event.customerId()
                    );
                }

                String key = customer.cohort() + "|M" + event.period();

                activity
                    .computeIfAbsent(key, ignored -> new HashSet<>())
                    .add(customer.id());
            }

            return activity;
        }

        Map<String, Double> retention() {
            Map<String, Integer> cohortSizes = new HashMap<>();

            for (Customer customer : customers) {
                cohortSizes.merge(customer.cohort(), 1, Integer::sum);
            }

            Map<String, Set<String>> active = activeCustomers();
            Map<String, Double> result = new HashMap<>();

            for (Map.Entry<String, Set<String>> entry : active.entrySet()) {
                String cohort = entry.getKey().split("\\|")[0];
                int size = cohortSizes.get(cohort);

                result.put(
                    entry.getKey(),
                    (double) entry.getValue().size() / size
                );
            }

            return result;
        }

        Map<String, Double> retentionByPlan(String plan) {
            Map<String, Set<String>> cohortMembers = new HashMap<>();
            Map<String, Set<String>> active = new HashMap<>();

            Map<String, Customer> index = new HashMap<>();

            for (Customer customer : customers) {
                index.put(customer.id(), customer);

                if (customer.plan().equals(plan)) {
                    String key = customer.cohort() + "|" + customer.plan();
                    cohortMembers
                        .computeIfAbsent(key, ignored -> new HashSet<>())
                        .add(customer.id());
                }
            }

            for (CustomerEvent event : events) {
                Customer customer = index.get(event.customerId());

                if (customer != null && customer.plan().equals(plan)) {
                    String key =
                        customer.cohort()
                        + "|"
                        + customer.plan()
                        + "|M"
                        + event.period();

                    active
                        .computeIfAbsent(key, ignored -> new HashSet<>())
                        .add(customer.id());
                }
            }

            Map<String, Double> result = new HashMap<>();

            for (Map.Entry<String, Set<String>> entry : active.entrySet()) {
                String[] parts = entry.getKey().split("\\|");
                String memberKey = parts[0] + "|" + parts[1];

                result.put(
                    entry.getKey(),
                    (double) entry.getValue().size()
                        / cohortMembers.get(memberKey).size()
                );
            }

            return result;
        }
    }

    private static void demonstrateCohorts() {
        List<Customer> customers = List.of(
            new Customer("C001", "2026-01", "organic", "pro"),
            new Customer("C002", "2026-01", "paid", "basic"),
            new Customer("C003", "2026-02", "referral", "pro"),
            new Customer("C004", "2026-02", "organic", "basic"),
            new Customer("C005", "2026-03", "paid", "pro")
        );

        List<CustomerEvent> events = List.of(
            new CustomerEvent("C001", 0, "signup", 0),
            new CustomerEvent("C001", 0, "purchase", 49),
            new CustomerEvent("C001", 1, "login", 0),
            new CustomerEvent("C001", 2, "purchase", 49),
            new CustomerEvent("C002", 0, "signup", 0),
            new CustomerEvent("C002", 1, "login", 0),
            new CustomerEvent("C003", 0, "signup", 0),
            new CustomerEvent("C003", 1, "purchase", 49),
            new CustomerEvent("C004", 0, "signup", 0),
            new CustomerEvent("C005", 0, "signup", 0),
            new CustomerEvent("C005", 1, "purchase", 49)
        );

        CohortService service = new CohortService(customers, events);

        System.out.println("COHORT RETENTION");

        service.retention()
            .entrySet()
            .stream()
            .sorted(Map.Entry.comparingByKey())
            .forEach(entry ->
                System.out.printf(
                    "%s = %.1f%%%n",
                    entry.getKey(),
                    entry.getValue() * 100
                )
            );

        System.out.println("\nPRO PLAN RETENTION");

        service.retentionByPlan("pro")
            .entrySet()
            .stream()
            .sorted(Map.Entry.comparingByKey())
            .forEach(entry ->
                System.out.printf(
                    "%s = %.1f%%%n",
                    entry.getKey(),
                    entry.getValue() * 100
                )
            );
    }

    private static void demonstrateGovernance() {
        BranchProtectionPolicy policy =
            new BranchProtectionPolicy(
                "main",
                true,
                true,
                true,
                true,
                true,
                true,
                2,
                Set.of("unit-tests", "security-scan"),
                Set.of("squash", "rebase")
            );

        PullRequest pullRequest =
            new PullRequest(
                42,
                "feature/cohort-dashboard",
                "main",
                Set.of("a1b2c3", "d4e5f6")
            );

        pullRequest.addReview(
            new Review("alice", ReviewState.APPROVED, true, false)
        );

        pullRequest.addReview(
            new Review("bob", ReviewState.APPROVED, true, false)
        );

        pullRequest.addReview(
            new Review("contractor", ReviewState.APPROVED, false, false)
        );

        pullRequest.addCheck(new StatusCheck("unit-tests", true));
        pullRequest.addCheck(new StatusCheck("security-scan", true));

        MergeEligibilityService service = new MergeEligibilityService();

        MergeDecision decision =
            service.evaluate(
                pullRequest,
                policy,
                MergeStrategy.SQUASH
            );

        System.out.println("\nENTERPRISE MERGE GOVERNANCE");
        System.out.println("Pull Request #" + pullRequest.id());
        System.out.println("Merge eligible: " + decision.eligible());

        for (String blocker : decision.blockers()) {
            System.out.println("Blocker: " + blocker);
        }

        pullRequest.setBaseChangedAfterApproval(true);

        MergeDecision staleDecision =
            service.evaluate(
                pullRequest,
                policy,
                MergeStrategy.SQUASH
            );

        System.out.println(
            "After base-branch change: "
            + (staleDecision.eligible() ? "eligible" : "requires revalidation")
        );
    }

    public static void main(String[] args) {
        demonstrateCohorts();
        demonstrateGovernance();
    }
}
