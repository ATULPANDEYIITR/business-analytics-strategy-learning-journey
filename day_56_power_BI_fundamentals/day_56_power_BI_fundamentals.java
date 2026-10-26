import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

public class PowerBIFundamentals {

    enum DatasetState {
        CREATED, REFRESHED, FAILED
    }

    enum ReviewDecision {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum VisualType {
        CARD, TABLE, BAR_CHART, LINE_CHART, SLICER
    }

    record Sale(
        long id,
        String region,
        String category,
        String product,
        int quantity,
        double unitPrice
    ) {
        Sale {
            if (id <= 0) throw new IllegalArgumentException("Sale ID must be positive.");
            if (region == null || region.isBlank()) throw new IllegalArgumentException("Region required.");
            if (category == null || category.isBlank()) throw new IllegalArgumentException("Category required.");
            if (product == null || product.isBlank()) throw new IllegalArgumentException("Product required.");
            if (quantity <= 0) throw new IllegalArgumentException("Quantity must be positive.");
            if (unitPrice < 0 || Double.isNaN(unitPrice)) {
                throw new IllegalArgumentException("Invalid unit price.");
            }
        }

        double revenue() {
            return quantity * unitPrice;
        }
    }

    record Review(
        String reviewer,
        ReviewDecision decision,
        boolean stale,
        Instant createdAt
    ) {}

    record StatusCheck(
        String name,
        boolean passed
    ) {}

    record BranchProtectionPolicy(
        int requiredApprovals,
        Set<String> requiredChecks,
        boolean requireResolvedConversations,
        boolean blockDirectPush,
        boolean blockForcePush
    ) {
        BranchProtectionPolicy {
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException("Approval count cannot be negative.");
            }

            requiredChecks = Set.copyOf(requiredChecks);
        }
    }

    static final class Dataset {
        private final String name;
        private final List<Sale> sales;
        private DatasetState state = DatasetState.CREATED;
        private Instant refreshedAt;

        Dataset(String name, List<Sale> sales) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Dataset name is required.");
            }

            this.name = name;
            this.sales = List.copyOf(sales);
        }

        void refresh() {
            Set<Long> ids = new HashSet<>();

            for (Sale sale : sales) {
                if (!ids.add(sale.id())) {
                    state = DatasetState.FAILED;
                    throw new IllegalStateException("Duplicate sale ID: " + sale.id());
                }
            }

            state = DatasetState.REFRESHED;
            refreshedAt = Instant.now();
        }

        double totalRevenue() {
            requireRefreshed();
            return sales.stream()
                    .mapToDouble(Sale::revenue)
                    .sum();
        }

        Map<String, Double> revenueByRegion() {
            requireRefreshed();

            return sales.stream().collect(
                    Collectors.groupingBy(
                            Sale::region,
                            TreeMap::new,
                            Collectors.summingDouble(Sale::revenue)
                    )
            );
        }

        Map<String, Double> revenueByCategory() {
            requireRefreshed();

            return sales.stream().collect(
                    Collectors.groupingBy(
                            Sale::category,
                            TreeMap::new,
                            Collectors.summingDouble(Sale::revenue)
                    )
            );
        }

        private void requireRefreshed() {
            if (state != DatasetState.REFRESHED) {
                throw new IllegalStateException(
                        "Dataset must be refreshed before report evaluation."
                );
            }
        }

        String name() {
            return name;
        }

        DatasetState state() {
            return state;
        }

        Instant refreshedAt() {
            return refreshedAt;
        }
    }

    static final class MergeEligibilityService {
        private final BranchProtectionPolicy policy;

        MergeEligibilityService(BranchProtectionPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        List<String> evaluate(
                List<Review> reviews,
                List<StatusCheck> checks,
                Set<String> eligibleReviewers,
                int unresolvedConversations,
                boolean hasConflict
        ) {
            List<String> failures = new ArrayList<>();

            long approvals = reviews.stream()
                    .filter(review ->
                            review.decision() == ReviewDecision.APPROVED
                            && !review.stale()
                            && eligibleReviewers.contains(review.reviewer()))
                    .map(Review::reviewer)
                    .distinct()
                    .count();

            if (approvals < policy.requiredApprovals()) {
                failures.add("Required current approvals are missing.");
            }

            Map<String, Boolean> checkMap = checks.stream()
                    .collect(Collectors.toMap(
                            StatusCheck::name,
                            StatusCheck::passed,
                            (first, second) -> second
                    ));

            for (String required : policy.requiredChecks()) {
                if (!Boolean.TRUE.equals(checkMap.get(required))) {
                    failures.add("Required status check is missing or failed: " + required);
                }
            }

            if (policy.requireResolvedConversations() &&
                    unresolvedConversations > 0) {
                failures.add("Review conversations are unresolved.");
            }

            if (hasConflict) {
                failures.add("Branch conflict must be resolved.");
            }

            return List.copyOf(failures);
        }
    }

    static void printReport(Dataset dataset) {
        System.out.println("DATASET: " + dataset.name());
        System.out.println("STATE: " + dataset.state());
        System.out.printf("TOTAL REVENUE: %.2f%n", dataset.totalRevenue());

        System.out.println("\nREVENUE BY REGION");
        dataset.revenueByRegion()
                .forEach((region, revenue) ->
                        System.out.printf("%s = %.2f%n", region, revenue));

        System.out.println("\nREVENUE BY CATEGORY");
        dataset.revenueByCategory()
                .forEach((category, revenue) ->
                        System.out.printf("%s = %.2f%n", category, revenue));

        System.out.println("REFRESHED AT: " + dataset.refreshedAt());
    }

    public static void main(String[] args) {
        Dataset dataset = new Dataset(
                "Enterprise Sales Dataset",
                List.of(
                        new Sale(1, "North", "Computers", "Laptop", 2, 85000),
                        new Sale(2, "South", "Accessories", "Monitor", 5, 18000),
                        new Sale(3, "North", "Accessories", "Keyboard", 8, 3500),
                        new Sale(4, "West", "Computers", "Laptop", 1, 92000),
                        new Sale(5, "South", "Computers", "Laptop", 3, 87000),
                        new Sale(6, "East", "Accessories", "Monitor", 7, 17500)
                )
        );

        dataset.refresh();
        printReport(dataset);

        BranchProtectionPolicy policy = new BranchProtectionPolicy(
                2,
                Set.of("build", "unit-tests", "security-scan"),
                true,
                true,
                true
        );

        MergeEligibilityService service =
                new MergeEligibilityService(policy);

        Set<String> eligibleReviewers =
                Set.of("reviewer-a", "reviewer-b", "architect");

        List<Review> reviews = List.of(
                new Review(
                        "reviewer-a",
                        ReviewDecision.APPROVED,
                        false,
                        Instant.now()
                ),
                new Review(
                        "reviewer-b",
                        ReviewDecision.APPROVED,
                        false,
                        Instant.now()
                ),
                new Review(
                        "architect",
                        ReviewDecision.APPROVED,
                        true,
                        Instant.now()
                )
        );

        List<StatusCheck> checks = List.of(
                new StatusCheck("build", true),
                new StatusCheck("unit-tests", true),
                new StatusCheck("security-scan", true)
        );

        List<String> failures = service.evaluate(
                reviews,
                checks,
                eligibleReviewers,
                0,
                false
        );

        System.out.println("\nMERGE ELIGIBILITY");
        if (failures.isEmpty()) {
            System.out.println("ELIGIBLE");
        } else {
            System.out.println("BLOCKED");
            failures.forEach(failure -> System.out.println("- " + failure));
        }

        List<Review> staleScenario = List.of(
                new Review(
                        "reviewer-a",
                        ReviewDecision.APPROVED,
                        true,
                        Instant.now()
                ),
                new Review(
                        "reviewer-b",
                        ReviewDecision.APPROVED,
                        false,
                        Instant.now()
                )
        );

        List<String> staleFailures = service.evaluate(
                staleScenario,
                checks,
                eligibleReviewers,
                1,
                false
        );

        System.out.println("\nSTALE APPROVAL SCENARIO");
        staleFailures.forEach(failure -> System.out.println("- " + failure));
    }
}
