import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/*
 * Enterprise Repository Data Integration
 *
 * This program models four SQL join types through a repository-governance
 * domain. Java's records provide immutable domain values, enums model
 * controlled states, and services keep join and policy logic explicit.
 *
 * Java 17 or later.
 */

public class JoinGovernanceDemo {

    enum JoinType {
        INNER,
        LEFT,
        RIGHT,
        FULL
    }

    enum ReviewState {
        APPROVED,
        CHANGES_REQUESTED,
        COMMENTED
    }

    record Repository(
        int id,
        String name,
        String defaultBranch
    ) {
        Repository {
            if (id <= 0) {
                throw new IllegalArgumentException("Repository id must be positive");
            }

            Objects.requireNonNull(name, "Repository name is required");
            Objects.requireNonNull(defaultBranch, "Default branch is required");
        }
    }

    record PullRequest(
        int id,
        int repositoryId,
        String sourceBranch,
        String targetBranch,
        boolean draft
    ) {
        PullRequest {
            if (id <= 0 || repositoryId <= 0) {
                throw new IllegalArgumentException(
                    "Pull request and repository IDs must be positive"
                );
            }

            Objects.requireNonNull(sourceBranch, "Source branch is required");
            Objects.requireNonNull(targetBranch, "Target branch is required");
        }
    }

    record Review(
        int id,
        int pullRequestId,
        String reviewer,
        ReviewState state
    ) {
        Review {
            if (id <= 0 || pullRequestId <= 0) {
                throw new IllegalArgumentException(
                    "Review and pull request IDs must be positive"
                );
            }

            Objects.requireNonNull(reviewer, "Reviewer is required");
            Objects.requireNonNull(state, "Review state is required");
        }
    }

    record StatusCheck(
        int id,
        int pullRequestId,
        String name,
        boolean passed
    ) {
        StatusCheck {
            if (id <= 0 || pullRequestId <= 0) {
                throw new IllegalArgumentException(
                    "Status-check IDs must be positive"
                );
            }

            Objects.requireNonNull(name, "Status-check name is required");
        }
    }

    record BranchProtectionPolicy(
        int repositoryId,
        int requiredApprovals,
        boolean requireCi,
        boolean requireConversationResolution
    ) {
        BranchProtectionPolicy {
            if (repositoryId <= 0) {
                throw new IllegalArgumentException(
                    "Repository ID must be positive"
                );
            }

            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                    "Required approvals cannot be negative"
                );
            }
        }
    }

    record RepositoryPullRequest(
        Optional<Repository> repository,
        Optional<PullRequest> pullRequest
    ) {}

    record GovernanceRow(
        Optional<Repository> repository,
        Optional<PullRequest> pullRequest,
        Optional<Review> review,
        Optional<StatusCheck> statusCheck,
        Optional<BranchProtectionPolicy> policy
    ) {}

    static final class JoinService {

        /*
         * The right side is indexed by key. Lists are stored for each key
         * because SQL joins preserve one-to-many relationships.
         */
        static List<RepositoryPullRequest> joinRepositoriesToPullRequests(
            List<Repository> repositories,
            List<PullRequest> pullRequests,
            JoinType joinType
        ) {
            Map<Integer, List<Integer>> index = new HashMap<>();

            for (int i = 0; i < pullRequests.size(); i++) {
                PullRequest pullRequest = pullRequests.get(i);

                index.computeIfAbsent(
                    pullRequest.repositoryId(),
                    ignored -> new ArrayList<>()
                ).add(i);
            }

            Set<Integer> matchedRightRows = new HashSet<>();
            List<RepositoryPullRequest> result = new ArrayList<>();

            for (Repository repository : repositories) {
                List<Integer> matches = index.get(repository.id());

                if (matches == null || matches.isEmpty()) {
                    if (joinType == JoinType.LEFT ||
                        joinType == JoinType.FULL) {

                        result.add(
                            new RepositoryPullRequest(
                                Optional.of(repository),
                                Optional.empty()
                            )
                        );
                    }

                    continue;
                }

                for (Integer position : matches) {
                    matchedRightRows.add(position);

                    result.add(
                        new RepositoryPullRequest(
                            Optional.of(repository),
                            Optional.of(pullRequests.get(position))
                        )
                    );
                }
            }

            if (joinType == JoinType.RIGHT ||
                joinType == JoinType.FULL) {

                for (int i = 0; i < pullRequests.size(); i++) {
                    if (!matchedRightRows.contains(i)) {
                        result.add(
                            new RepositoryPullRequest(
                                Optional.empty(),
                                Optional.of(pullRequests.get(i))
                            )
                        );
                    }
                }
            }

            return result;
        }

        static List<GovernanceRow> joinReviews(
            List<RepositoryPullRequest> repositoryPullRequests,
            List<Review> reviews,
            JoinType joinType
        ) {
            Map<Integer, List<Integer>> index = new HashMap<>();

            for (int i = 0; i < reviews.size(); i++) {
                Review review = reviews.get(i);

                index.computeIfAbsent(
                    review.pullRequestId(),
                    ignored -> new ArrayList<>()
                ).add(i);
            }

            Set<Integer> matchedReviews = new HashSet<>();
            List<GovernanceRow> result = new ArrayList<>();

            for (RepositoryPullRequest row : repositoryPullRequests) {
                if (row.pullRequest().isEmpty()) {
                    if (joinType == JoinType.LEFT ||
                        joinType == JoinType.FULL) {

                        result.add(
                            new GovernanceRow(
                                row.repository(),
                                row.pullRequest(),
                                Optional.empty(),
                                Optional.empty(),
                                Optional.empty()
                            )
                        );
                    }

                    continue;
                }

                int pullRequestId = row.pullRequest().get().id();
                List<Integer> matches = index.get(pullRequestId);

                if (matches == null || matches.isEmpty()) {
                    if (joinType == JoinType.LEFT ||
                        joinType == JoinType.FULL) {

                        result.add(
                            new GovernanceRow(
                                row.repository(),
                                row.pullRequest(),
                                Optional.empty(),
                                Optional.empty(),
                                Optional.empty()
                            )
                        );
                    }

                    continue;
                }

                for (Integer position : matches) {
                    matchedReviews.add(position);

                    result.add(
                        new GovernanceRow(
                            row.repository(),
                            row.pullRequest(),
                            Optional.of(reviews.get(position)),
                            Optional.empty(),
                            Optional.empty()
                        )
                    );
                }
            }

            if (joinType == JoinType.RIGHT ||
                joinType == JoinType.FULL) {

                for (int i = 0; i < reviews.size(); i++) {
                    if (!matchedReviews.contains(i)) {
                        result.add(
                            new GovernanceRow(
                                Optional.empty(),
                                Optional.empty(),
                                Optional.of(reviews.get(i)),
                                Optional.empty(),
                                Optional.empty()
                            )
                        );
                    }
                }
            }

            return result;
        }

        static List<GovernanceRow> joinStatusChecks(
            List<GovernanceRow> rows,
            List<StatusCheck> checks,
            JoinType joinType
        ) {
            Map<Integer, List<Integer>> index = new HashMap<>();

            for (int i = 0; i < checks.size(); i++) {
                StatusCheck check = checks.get(i);

                index.computeIfAbsent(
                    check.pullRequestId(),
                    ignored -> new ArrayList<>()
                ).add(i);
            }

            Set<Integer> matchedChecks = new HashSet<>();
            List<GovernanceRow> result = new ArrayList<>();

            for (GovernanceRow row : rows) {
                if (row.pullRequest().isEmpty()) {
                    if (joinType == JoinType.LEFT ||
                        joinType == JoinType.FULL) {

                        result.add(row);
                    }

                    continue;
                }

                List<Integer> matches =
                    index.get(row.pullRequest().get().id());

                if (matches == null || matches.isEmpty()) {
                    if (joinType == JoinType.LEFT ||
                        joinType == JoinType.FULL) {

                        result.add(row);
                    }

                    continue;
                }

                for (Integer position : matches) {
                    matchedChecks.add(position);

                    result.add(
                        new GovernanceRow(
                            row.repository(),
                            row.pullRequest(),
                            row.review(),
                            Optional.of(checks.get(position)),
                            row.policy()
                        )
                    );
                }
            }

            if (joinType == JoinType.RIGHT ||
                joinType == JoinType.FULL) {

                for (int i = 0; i < checks.size(); i++) {
                    if (!matchedChecks.contains(i)) {
                        result.add(
                            new GovernanceRow(
                                Optional.empty(),
                                Optional.empty(),
                                Optional.empty(),
                                Optional.of(checks.get(i)),
                                Optional.empty()
                            )
                        );
                    }
                }
            }

            return result;
        }

        static List<GovernanceRow> joinPolicies(
            List<GovernanceRow> rows,
            List<BranchProtectionPolicy> policies,
            JoinType joinType
        ) {
            Map<Integer, BranchProtectionPolicy> index = new HashMap<>();

            for (BranchProtectionPolicy policy : policies) {
                if (index.put(policy.repositoryId(), policy) != null) {
                    throw new IllegalStateException(
                        "A repository cannot have multiple active policies"
                    );
                }
            }

            Set<Integer> matchedPolicies = new HashSet<>();
            List<GovernanceRow> result = new ArrayList<>();

            for (GovernanceRow row : rows) {
                if (row.repository().isEmpty()) {
                    if (joinType == JoinType.LEFT ||
                        joinType == JoinType.FULL) {

                        result.add(row);
                    }

                    continue;
                }

                int repositoryId = row.repository().get().id();
                BranchProtectionPolicy policy = index.get(repositoryId);

                if (policy == null) {
                    if (joinType == JoinType.LEFT ||
                        joinType == JoinType.FULL) {

                        result.add(row);
                    }

                    continue;
                }

                matchedPolicies.add(repositoryId);

                result.add(
                    new GovernanceRow(
                        row.repository(),
                        row.pullRequest(),
                        row.review(),
                        row.statusCheck(),
                        Optional.of(policy)
                    )
                );
            }

            if (joinType == JoinType.RIGHT ||
                joinType == JoinType.FULL) {

                for (BranchProtectionPolicy policy : policies) {
                    if (!matchedPolicies.contains(policy.repositoryId())) {
                        result.add(
                            new GovernanceRow(
                                Optional.empty(),
                                Optional.empty(),
                                Optional.empty(),
                                Optional.empty(),
                                Optional.of(policy)
                            )
                        );
                    }
                }
            }

            return result;
        }
    }

    static final class MergeEligibilityService {

        private MergeEligibilityService() {}

        static boolean isEligible(
            PullRequest pullRequest,
            List<Review> reviews,
            List<StatusCheck> checks,
            Optional<BranchProtectionPolicy> policy
        ) {
            if (policy.isEmpty()) {
                return false;
            }

            if (pullRequest.draft()) {
                return false;
            }

            BranchProtectionPolicy protection = policy.get();

            Set<String> distinctApprovers = new HashSet<>();

            for (Review review : reviews) {
                if (
                    review.pullRequestId() == pullRequest.id() &&
                    review.state() == ReviewState.APPROVED
                ) {
                    distinctApprovers.add(review.reviewer());
                }
            }

            if (distinctApprovers.size() < protection.requiredApprovals()) {
                return false;
            }

            if (protection.requireCi()) {
                boolean foundCheck = false;

                for (StatusCheck check : checks) {
                    if (check.pullRequestId() != pullRequest.id()) {
                        continue;
                    }

                    foundCheck = true;

                    if (!check.passed()) {
                        return false;
                    }
                }

                if (!foundCheck) {
                    return false;
                }
            }

            return true;
        }
    }

    static void printJoinResults(
        List<RepositoryPullRequest> rows,
        String label
    ) {
        System.out.println("\n" + label);
        System.out.println("Repository\tPull Request");

        for (RepositoryPullRequest row : rows) {
            String repository = row.repository()
                .map(Repository::name)
                .orElse("NULL");

            String pullRequest = row.pullRequest()
                .map(pr -> "#" + pr.id())
                .orElse("NULL");

            System.out.println(repository + "\t" + pullRequest);
        }
    }

    static void printGovernanceResults(List<GovernanceRow> rows) {
        System.out.println("\nGovernance join");
        System.out.println(
            "Repository\tPR\tReview\tCheck\tPolicy"
        );

        for (GovernanceRow row : rows) {
            String repository = row.repository()
                .map(Repository::name)
                .orElse("NULL");

            String pullRequest = row.pullRequest()
                .map(pr -> "#" + pr.id())
                .orElse("NULL");

            String review = row.review()
                .map(r -> r.reviewer() + ":" + r.state())
                .orElse("NULL");

            String check = row.statusCheck()
                .map(c -> c.name() + ":" + (c.passed() ? "PASS" : "FAIL"))
                .orElse("NULL");

            String policy = row.policy()
                .map(p -> "approvals=" + p.requiredApprovals())
                .orElse("NULL");

            System.out.println(
                repository + "\t" +
                pullRequest + "\t" +
                review + "\t" +
                check + "\t" +
                policy
            );
        }
    }

    static void demonstrateJoinSemantics(
        List<Repository> repositories,
        List<PullRequest> pullRequests
    ) {
        for (JoinType type : EnumSet.of(
            JoinType.INNER,
            JoinType.LEFT,
            JoinType.RIGHT,
            JoinType.FULL
        )) {
            List<RepositoryPullRequest> rows =
                JoinService.joinRepositoriesToPullRequests(
                    repositories,
                    pullRequests,
                    type
                );

            printJoinResults(rows, type + " JOIN");
        }
    }

    static void demonstrateEnterpriseWorkflow(
        List<Repository> repositories,
        List<PullRequest> pullRequests,
        List<Review> reviews,
        List<StatusCheck> checks,
        List<BranchProtectionPolicy> policies
    ) {
        /*
         * The enterprise report uses LEFT joins because missing governance
         * records must remain visible. A missing policy is itself a governance
         * finding and should not cause the repository to disappear.
         */
        List<RepositoryPullRequest> repositoryPullRequests =
            JoinService.joinRepositoriesToPullRequests(
                repositories,
                pullRequests,
                JoinType.LEFT
            );

        List<GovernanceRow> withReviews =
            JoinService.joinReviews(
                repositoryPullRequests,
                reviews,
                JoinType.LEFT
            );

        List<GovernanceRow> withChecks =
            JoinService.joinStatusChecks(
                withReviews,
                checks,
                JoinType.LEFT
            );

        List<GovernanceRow> governance =
            JoinService.joinPolicies(
                withChecks,
                policies,
                JoinType.LEFT
            );

        printGovernanceResults(governance);

        System.out.println("\nMerge eligibility");

        for (PullRequest pullRequest : pullRequests) {
            Optional<BranchProtectionPolicy> policy =
                policies.stream()
                    .filter(
                        candidate ->
                            candidate.repositoryId() ==
                            pullRequest.repositoryId()
                    )
                    .findFirst();

            boolean eligible =
                MergeEligibilityService.isEligible(
                    pullRequest,
                    reviews,
                    checks,
                    policy
                );

            System.out.println(
                "PR #" + pullRequest.id() +
                ": " +
                (eligible ? "MERGE ELIGIBLE" : "BLOCKED")
            );
        }

        /*
         * FULL JOIN is useful for reconciliation. An orphan review or policy
         * remains visible even though its parent entity is absent.
         */
        List<GovernanceRow> audit =
            JoinService.joinReviews(
                repositoryPullRequests,
                reviews,
                JoinType.FULL
            );

        System.out.println(
            "\nFULL JOIN audit rows: " + audit.size()
        );
    }

    static void demonstrateFailureCases() {
        System.out.println("\nValidation failures");

        try {
            new BranchProtectionPolicy(10, -1, true, true);
        } catch (IllegalArgumentException exception) {
            System.out.println(
                "Rejected invalid policy: " + exception.getMessage()
            );
        }

        try {
            new Repository(0, "invalid", "main");
        } catch (IllegalArgumentException exception) {
            System.out.println(
                "Rejected invalid repository: " + exception.getMessage()
            );
        }
    }

    static void runAssertions(
        List<Repository> repositories,
        List<PullRequest> pullRequests
    ) {
        Map<JoinType, Integer> expected = Map.of(
            JoinType.INNER, 3,
            JoinType.LEFT, 4,
            JoinType.RIGHT, 4,
            JoinType.FULL, 5
        );

        for (Map.Entry<JoinType, Integer> entry : expected.entrySet()) {
            int actual =
                JoinService.joinRepositoriesToPullRequests(
                    repositories,
                    pullRequests,
                    entry.getKey()
                ).size();

            if (actual != entry.getValue()) {
                throw new AssertionError(
                    entry.getKey() +
                    " expected " +
                    entry.getValue() +
                    " rows but received " +
                    actual
                );
            }

            System.out.println(
                entry.getKey() + ": " + actual + " rows"
            );
        }
    }

    public static void main(String[] args) {
        List<Repository> repositories = List.of(
            new Repository(1, "payments-api", "main"),
            new Repository(2, "identity-service", "main"),
            new Repository(3, "analytics-engine", "main")
        );

        List<PullRequest> pullRequests = List.of(
            new PullRequest(
                101,
                1,
                "feature/cache",
                "main",
                false
            ),
            new PullRequest(
                102,
                1,
                "feature/tracing",
                "main",
                false
            ),
            new PullRequest(
                103,
                2,
                "security/headers",
                "main",
                true
            ),
            new PullRequest(
                104,
                9,
                "external/fix",
                "main",
                false
            )
        );

        List<Review> reviews = List.of(
            new Review(
                201,
                101,
                "reviewer-a",
                ReviewState.APPROVED
            ),
            new Review(
                202,
                101,
                "reviewer-b",
                ReviewState.APPROVED
            ),
            new Review(
                203,
                102,
                "reviewer-a",
                ReviewState.CHANGES_REQUESTED
            ),
            new Review(
                204,
                999,
                "reviewer-c",
                ReviewState.APPROVED
            )
        );

        List<StatusCheck> checks = List.of(
            new StatusCheck(301, 101, "build", true),
            new StatusCheck(302, 101, "test", true),
            new StatusCheck(303, 102, "build", true),
            new StatusCheck(304, 102, "test", false),
            new StatusCheck(305, 103, "build", true)
        );

        List<BranchProtectionPolicy> policies = List.of(
            new BranchProtectionPolicy(1, 2, true, true),
            new BranchProtectionPolicy(2, 1, true, true)
        );

        demonstrateJoinSemantics(repositories, pullRequests);
        demonstrateEnterpriseWorkflow(
            repositories,
            pullRequests,
            reviews,
            checks,
            policies
        );
        demonstrateFailureCases();
        runAssertions(repositories, pullRequests);

        System.out.println(
            "\nEnterprise join demonstration completed."
        );
    }
}
