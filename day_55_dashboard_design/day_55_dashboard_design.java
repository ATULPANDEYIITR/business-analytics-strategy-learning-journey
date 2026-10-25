import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class DashboardGovernanceApp {

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum CheckState {
        PASSING, FAILING, PENDING
    }

    enum MergeStrategy {
        MERGE_COMMIT, SQUASH, REBASE
    }

    record Commit(String sha, String message, String author) {}

    record ReviewComment(
        int id,
        String reviewer,
        String body,
        boolean resolved
    ) {}

    record Review(
        String reviewer,
        ReviewState state,
        List<ReviewComment> comments
    ) {
        Review {
            comments = List.copyOf(comments);
        }
    }

    record StatusCheck(
        String name,
        CheckState state,
        boolean required
    ) {}

    record BranchProtectionPolicy(
        int requiredReviews,
        Set<String> requiredChecks,
        boolean requireConversationResolution,
        boolean requireLinearHistory,
        boolean allowForcePush,
        boolean allowDirectPush,
        boolean allowDeletion
    ) {
        BranchProtectionPolicy {
            if (requiredReviews < 0) {
                throw new IllegalArgumentException(
                    "Required reviews cannot be negative."
                );
            }
            requiredChecks = Set.copyOf(requiredChecks);
        }
    }

    record Branch(
        String name,
        boolean protectedBranch,
        List<Commit> commits
    ) {
        Branch {
            commits = List.copyOf(commits);
        }
    }

    static final class PullRequest {
        private final int number;
        private final String sourceBranch;
        private final String targetBranch;
        private final String title;
        private PullRequestState state;
        private final List<Commit> commits;
        private final List<Review> reviews;
        private final List<ReviewComment> comments;
        private final List<StatusCheck> statusChecks;
        private final MergeStrategy mergeStrategy;

        PullRequest(
            int number,
            String sourceBranch,
            String targetBranch,
            String title,
            PullRequestState state,
            List<Commit> commits,
            List<Review> reviews,
            List<ReviewComment> comments,
            List<StatusCheck> statusChecks,
            MergeStrategy mergeStrategy
        ) {
            this.number = number;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.title = title;
            this.state = state;
            this.commits = List.copyOf(commits);
            this.reviews = List.copyOf(reviews);
            this.comments = List.copyOf(comments);
            this.statusChecks = List.copyOf(statusChecks);
            this.mergeStrategy = mergeStrategy;
        }

        int number() {
            return number;
        }

        String sourceBranch() {
            return sourceBranch;
        }

        String targetBranch() {
            return targetBranch;
        }

        PullRequestState state() {
            return state;
        }

        List<Review> reviews() {
            return reviews;
        }

        List<ReviewComment> comments() {
            return comments;
        }

        List<StatusCheck> statusChecks() {
            return statusChecks;
        }

        MergeStrategy mergeStrategy() {
            return mergeStrategy;
        }

        long unresolvedConversations() {
            return comments.stream()
                .filter(comment -> !comment.resolved())
                .count();
        }
    }

    static final class Repository {
        private final String name;
        private final Map<String, Branch> branches;
        private final Map<Integer, PullRequest> pullRequests;
        private final Map<String, BranchProtectionPolicy> protection;
        private final Set<String> eligibleReviewers;

        Repository(
            String name,
            Map<String, Branch> branches,
            Map<Integer, PullRequest> pullRequests,
            Map<String, BranchProtectionPolicy> protection,
            Set<String> eligibleReviewers
        ) {
            this.name = name;
            this.branches = Map.copyOf(branches);
            this.pullRequests = Map.copyOf(pullRequests);
            this.protection = Map.copyOf(protection);
            this.eligibleReviewers = Set.copyOf(eligibleReviewers);
        }
    }

    record MergeDecision(
        boolean eligible,
        List<String> reasons
    ) {
        MergeDecision {
            reasons = List.copyOf(reasons);
        }
    }

    record DashboardMetrics(
        long openPullRequests,
        long draftPullRequests,
        long mergeablePullRequests,
        long blockedPullRequests,
        long mergedPullRequests,
        long unresolvedConversations
    ) {}

    static final class MergeEligibilityService {
        private final Repository repository;

        MergeEligibilityService(Repository repository) {
            this.repository = repository;
        }

        MergeDecision evaluate(PullRequest pr) {
            List<String> reasons = new ArrayList<>();

            if (pr.state() != PullRequestState.OPEN) {
                reasons.add("Pull Request is not open.");
            }

            if (pr.state() == PullRequestState.DRAFT) {
                reasons.add("Draft Pull Requests cannot be merged.");
            }

            BranchProtectionPolicy policy =
                repository.protection.get(pr.targetBranch());

            if (policy == null) {
                reasons.add("Target branch is not protected by a policy.");
                return new MergeDecision(false, reasons);
            }

            long approvals = pr.reviews().stream()
                .filter(review ->
                    review.state() == ReviewState.APPROVED
                    && repository.eligibleReviewers.contains(review.reviewer())
                )
                .map(Review::reviewer)
                .distinct()
                .count();

            long requestedChanges = pr.reviews().stream()
                .filter(review ->
                    review.state() == ReviewState.CHANGES_REQUESTED
                    && repository.eligibleReviewers.contains(review.reviewer())
                )
                .map(Review::reviewer)
                .distinct()
                .count();

            if (approvals - requestedChanges < policy.requiredReviews()) {
                reasons.add(
                    "Required approvals: " + policy.requiredReviews()
                    + "; active eligible approvals: "
                    + Math.max(0, approvals - requestedChanges) + "."
                );
            }

            Map<String, CheckState> checks = new HashMap<>();
            for (StatusCheck check : pr.statusChecks()) {
                checks.put(check.name(), check.state());
            }

            for (String required : policy.requiredChecks()) {
                if (checks.get(required) != CheckState.PASSING) {
                    reasons.add(
                        "Required check '" + required
                        + "' is not passing."
                    );
                }
            }

            if (
                policy.requireConversationResolution()
                && pr.unresolvedConversations() > 0
            ) {
                reasons.add("Unresolved review conversations remain.");
            }

            if (
                policy.requireLinearHistory()
                && pr.mergeStrategy() == MergeStrategy.MERGE_COMMIT
            ) {
                reasons.add("Linear history is required.");
            }

            return new MergeDecision(reasons.isEmpty(), reasons);
        }
    }

    static final class DashboardService {
        private final Repository repository;
        private final MergeEligibilityService eligibilityService;

        DashboardService(Repository repository) {
            this.repository = repository;
            this.eligibilityService =
                new MergeEligibilityService(repository);
        }

        DashboardMetrics calculate() {
            long open = repository.pullRequests.values().stream()
                .filter(pr ->
                    pr.state() == PullRequestState.OPEN
                    || pr.state() == PullRequestState.DRAFT)
                .count();

            long drafts = repository.pullRequests.values().stream()
                .filter(pr -> pr.state() == PullRequestState.DRAFT)
                .count();

            long merged = repository.pullRequests.values().stream()
                .filter(pr -> pr.state() == PullRequestState.MERGED)
                .count();

            long mergeable = repository.pullRequests.values().stream()
                .filter(pr -> pr.state() == PullRequestState.OPEN)
                .filter(pr -> eligibilityService.evaluate(pr).eligible())
                .count();

            long unresolved = repository.pullRequests.values().stream()
                .mapToLong(PullRequest::unresolvedConversations)
                .sum();

            return new DashboardMetrics(
                open,
                drafts,
                mergeable,
                Math.max(0, open - drafts - mergeable),
                merged,
                unresolved
            );
        }

        MergeDecision evaluate(int number) {
            PullRequest pr = repository.pullRequests.get(number);

            if (pr == null) {
                throw new IllegalArgumentException(
                    "Unknown Pull Request: " + number
                );
            }

            return eligibilityService.evaluate(pr);
        }
    }

    static Repository sampleRepository() {
        List<Commit> commits = List.of(
            new Commit("d001", "Create dashboard architecture", "alice"),
            new Commit("d002", "Add governance metrics", "alice")
        );

        List<Review> reviews = List.of(
            new Review("bob", ReviewState.APPROVED, List.of()),
            new Review("carol", ReviewState.APPROVED, List.of())
        );

        List<ReviewComment> comments = List.of(
            new ReviewComment(
                1,
                "bob",
                "Clarify the status metric.",
                true
            ),
            new ReviewComment(
                2,
                "carol",
                "Explain policy ownership.",
                false
            )
        );

        List<StatusCheck> checks = List.of(
            new StatusCheck("unit-tests", CheckState.PASSING, true),
            new StatusCheck("security-scan", CheckState.PASSING, true),
            new StatusCheck("performance", CheckState.PENDING, false)
        );

        PullRequest pr = new PullRequest(
            500,
            "feature/dashboard",
            "main",
            "Repository governance dashboard",
            PullRequestState.OPEN,
            commits,
            reviews,
            comments,
            checks,
            MergeStrategy.SQUASH
        );

        Map<String, Branch> branches = Map.of(
            "main", new Branch("main", true, commits),
            "feature/dashboard",
                new Branch("feature/dashboard", false, commits)
        );

        BranchProtectionPolicy policy =
            new BranchProtectionPolicy(
                2,
                Set.of("unit-tests", "security-scan"),
                true,
                true,
                false,
                false,
                false
            );

        return new Repository(
            "enterprise-platform",
            branches,
            Map.of(500, pr),
            Map.of("main", policy),
            Set.of("alice", "bob", "carol", "david")
        );
    }

    static void validateRepository(Repository repository) {
        if (repository.name.isBlank()) {
            throw new IllegalArgumentException(
                "Repository name cannot be blank."
            );
        }

        if (!repository.branches.containsKey("main")) {
            throw new IllegalArgumentException(
                "Main branch is required."
            );
        }

        repository.pullRequests.values().forEach(pr -> {
            if (!repository.branches.containsKey(pr.sourceBranch())) {
                throw new IllegalArgumentException(
                    "Unknown source branch: " + pr.sourceBranch()
                );
            }

            if (!repository.branches.containsKey(pr.targetBranch())) {
                throw new IllegalArgumentException(
                    "Unknown target branch: " + pr.targetBranch()
                );
            }
        });
    }

    public static void main(String[] args) {
        Repository repository = sampleRepository();
        validateRepository(repository);

        DashboardService dashboard = new DashboardService(repository);
        DashboardMetrics metrics = dashboard.calculate();

        System.out.println("REPOSITORY GOVERNANCE DASHBOARD");
        System.out.println("================================");
        System.out.println(
            "Open Pull Requests:       " + metrics.openPullRequests()
        );
        System.out.println(
            "Draft Pull Requests:      " + metrics.draftPullRequests()
        );
        System.out.println(
            "Mergeable Pull Requests:  "
            + metrics.mergeablePullRequests()
        );
        System.out.println(
            "Blocked Pull Requests:    "
            + metrics.blockedPullRequests()
        );
        System.out.println(
            "Merged Pull Requests:     "
            + metrics.mergedPullRequests()
        );
        System.out.println(
            "Unresolved Conversations: "
            + metrics.unresolvedConversations()
        );

        MergeDecision decision = dashboard.evaluate(500);

        System.out.println("\nMERGE ELIGIBILITY");
        System.out.println("=================");
        System.out.println("Eligible: " + decision.eligible());

        for (String reason : decision.reasons()) {
            System.out.println("- " + reason);
        }
    }
}
