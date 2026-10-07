#include <algorithm>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

/*
 * Repository Governance Join Engine
 *
 * Case study:
 * A repository governance service needs to combine repository, pull request,
 * review, CI status, and branch-policy data.
 *
 * The join engine demonstrates:
 *   INNER JOIN  -> only entities with relationships on both sides
 *   LEFT JOIN   -> preserve every row from the left relation
 *   RIGHT JOIN  -> preserve every row from the right relation
 *   FULL JOIN   -> preserve unmatched rows from both relations
 *
 * C++17 is used for optional values, structured data modeling, and explicit
 * ownership of the join algorithm.
 *
 * The program uses a hash-indexed equality join for realistic performance.
 */

enum class JoinType {
    INNER,
    LEFT,
    RIGHT,
    FULL
};

enum class ReviewState {
    APPROVED,
    CHANGES_REQUESTED,
    COMMENTED
};

struct Repository {
    int id;
    std::string name;
    std::string defaultBranch;
};

struct PullRequest {
    int id;
    int repositoryId;
    std::string sourceBranch;
    std::string targetBranch;
    bool draft;
};

struct Review {
    int id;
    int pullRequestId;
    std::string reviewer;
    ReviewState state;
};

struct StatusCheck {
    int id;
    int pullRequestId;
    std::string name;
    bool passed;
};

struct BranchPolicy {
    int repositoryId;
    int requiredApprovals;
    bool requireCi;
    bool requireConversationResolution;
};

struct GovernanceRow {
    std::optional<Repository> repository;
    std::optional<PullRequest> pullRequest;
    std::optional<Review> review;
    std::optional<StatusCheck> statusCheck;
    std::optional<BranchPolicy> policy;
};

struct RepositoryPullRequestRow {
    std::optional<Repository> repository;
    std::optional<PullRequest> pullRequest;
};

std::string reviewStateToString(ReviewState state) {
    switch (state) {
        case ReviewState::APPROVED:
            return "APPROVED";
        case ReviewState::CHANGES_REQUESTED:
            return "CHANGES_REQUESTED";
        case ReviewState::COMMENTED:
            return "COMMENTED";
    }

    throw std::logic_error("Unknown review state");
}

template <typename T>
std::string optionalId(const std::optional<T>& value, int T::*member) {
    if (!value.has_value()) {
        return "NULL";
    }

    return std::to_string(value->*member);
}

std::vector<RepositoryPullRequestRow> joinRepositoriesAndPullRequests(
    const std::vector<Repository>& repositories,
    const std::vector<PullRequest>& pullRequests,
    JoinType joinType
) {
    /*
     * Index pull requests by repository_id. The vector is necessary because
     * one repository can own many pull requests. A map<int, PullRequest>
     * would incorrectly discard duplicates.
     */
    std::unordered_map<int, std::vector<size_t>> prIndex;

    for (size_t i = 0; i < pullRequests.size(); ++i) {
        prIndex[pullRequests[i].repositoryId].push_back(i);
    }

    std::unordered_set<size_t> matchedPullRequests;
    std::vector<RepositoryPullRequestRow> result;

    for (const auto& repository : repositories) {
        auto iterator = prIndex.find(repository.id);

        if (iterator == prIndex.end()) {
            if (joinType == JoinType::LEFT || joinType == JoinType::FULL) {
                result.push_back({repository, std::nullopt});
            }

            continue;
        }

        for (size_t prIndexPosition : iterator->second) {
            matchedPullRequests.insert(prIndexPosition);

            result.push_back({
                repository,
                pullRequests[prIndexPosition]
            });
        }
    }

    if (joinType == JoinType::RIGHT || joinType == JoinType::FULL) {
        for (size_t i = 0; i < pullRequests.size(); ++i) {
            if (!matchedPullRequests.contains(i)) {
                result.push_back({
                    std::nullopt,
                    pullRequests[i]
                });
            }
        }
    }

    return result;
}

std::vector<GovernanceRow> joinPullRequestsToReviews(
    const std::vector<RepositoryPullRequestRow>& repositoryPullRequests,
    const std::vector<Review>& reviews,
    JoinType joinType
) {
    std::unordered_map<int, std::vector<size_t>> reviewIndex;

    for (size_t i = 0; i < reviews.size(); ++i) {
        reviewIndex[reviews[i].pullRequestId].push_back(i);
    }

    std::unordered_set<size_t> matchedReviews;
    std::vector<GovernanceRow> result;

    for (const auto& row : repositoryPullRequests) {
        if (!row.pullRequest.has_value()) {
            if (joinType == JoinType::LEFT || joinType == JoinType::FULL) {
                result.push_back({
                    row.repository,
                    row.pullRequest,
                    std::nullopt,
                    std::nullopt,
                    std::nullopt
                });
            }

            continue;
        }

        const int prId = row.pullRequest->id;
        auto iterator = reviewIndex.find(prId);

        if (iterator == reviewIndex.end()) {
            if (joinType == JoinType::LEFT || joinType == JoinType::FULL) {
                result.push_back({
                    row.repository,
                    row.pullRequest,
                    std::nullopt,
                    std::nullopt,
                    std::nullopt
                });
            }

            continue;
        }

        for (size_t reviewIndexPosition : iterator->second) {
            matchedReviews.insert(reviewIndexPosition);

            result.push_back({
                row.repository,
                row.pullRequest,
                reviews[reviewIndexPosition],
                std::nullopt,
                std::nullopt
            });
        }
    }

    if (joinType == JoinType::RIGHT || joinType == JoinType::FULL) {
        for (size_t i = 0; i < reviews.size(); ++i) {
            if (!matchedReviews.contains(i)) {
                result.push_back({
                    std::nullopt,
                    std::nullopt,
                    reviews[i],
                    std::nullopt,
                    std::nullopt
                });
            }
        }
    }

    return result;
}

std::vector<GovernanceRow> joinStatusChecks(
    const std::vector<GovernanceRow>& rows,
    const std::vector<StatusCheck>& checks,
    JoinType joinType
) {
    std::unordered_map<int, std::vector<size_t>> checkIndex;

    for (size_t i = 0; i < checks.size(); ++i) {
        checkIndex[checks[i].pullRequestId].push_back(i);
    }

    std::unordered_set<size_t> matchedChecks;
    std::vector<GovernanceRow> result;

    for (const auto& row : rows) {
        if (!row.pullRequest.has_value()) {
            if (joinType == JoinType::LEFT || joinType == JoinType::FULL) {
                result.push_back(row);
            }

            continue;
        }

        auto iterator = checkIndex.find(row.pullRequest->id);

        if (iterator == checkIndex.end()) {
            if (joinType == JoinType::LEFT || joinType == JoinType::FULL) {
                result.push_back(row);
            }

            continue;
        }

        for (size_t checkPosition : iterator->second) {
            matchedChecks.insert(checkPosition);

            GovernanceRow enriched = row;
            enriched.statusCheck = checks[checkPosition];
            result.push_back(enriched);
        }
    }

    if (joinType == JoinType::RIGHT || joinType == JoinType::FULL) {
        for (size_t i = 0; i < checks.size(); ++i) {
            if (!matchedChecks.contains(i)) {
                GovernanceRow orphan;
                orphan.statusCheck = checks[i];
                result.push_back(orphan);
            }
        }
    }

    return result;
}

std::vector<GovernanceRow> joinBranchPolicies(
    const std::vector<GovernanceRow>& rows,
    const std::vector<BranchPolicy>& policies,
    JoinType joinType
) {
    std::unordered_map<int, size_t> policyIndex;

    for (size_t i = 0; i < policies.size(); ++i) {
        /*
         * Branch policy is one-per-repository in this domain. A unique
         * repository_id constraint would enforce this at the database layer.
         */
        policyIndex[policies[i].repositoryId] = i;
    }

    std::unordered_set<size_t> matchedPolicies;
    std::vector<GovernanceRow> result;

    for (const auto& row : rows) {
        if (!row.repository.has_value()) {
            if (joinType == JoinType::LEFT || joinType == JoinType::FULL) {
                result.push_back(row);
            }

            continue;
        }

        auto iterator = policyIndex.find(row.repository->id);

        if (iterator == policyIndex.end()) {
            if (joinType == JoinType::LEFT || joinType == JoinType::FULL) {
                result.push_back(row);
            }

            continue;
        }

        matchedPolicies.insert(iterator->second);

        GovernanceRow enriched = row;
        enriched.policy = policies[iterator->second];
        result.push_back(enriched);
    }

    if (joinType == JoinType::RIGHT || joinType == JoinType::FULL) {
        for (size_t i = 0; i < policies.size(); ++i) {
            if (!matchedPolicies.contains(i)) {
                GovernanceRow orphan;
                orphan.policy = policies[i];
                result.push_back(orphan);
            }
        }
    }

    return result;
}

int countApprovals(const std::vector<Review>& reviews, int pullRequestId) {
    int approvals = 0;

    for (const auto& review : reviews) {
        if (
            review.pullRequestId == pullRequestId &&
            review.state == ReviewState::APPROVED
        ) {
            ++approvals;
        }
    }

    return approvals;
}

bool allRequiredChecksPassed(
    const std::vector<StatusCheck>& checks,
    int pullRequestId
) {
    bool foundCheck = false;

    for (const auto& check : checks) {
        if (check.pullRequestId != pullRequestId) {
            continue;
        }

        foundCheck = true;

        if (!check.passed) {
            return false;
        }
    }

    return foundCheck;
}

bool mergeEligible(
    const PullRequest& pullRequest,
    const std::vector<Review>& reviews,
    const std::vector<StatusCheck>& checks,
    const std::optional<BranchPolicy>& policy
) {
    if (!policy.has_value()) {
        return false;
    }

    if (pullRequest.draft) {
        return false;
    }

    if (
        countApprovals(reviews, pullRequest.id)
        < policy->requiredApprovals
    ) {
        return false;
    }

    if (
        policy->requireCi &&
        !allRequiredChecksPassed(checks, pullRequest.id)
    ) {
        return false;
    }

    return true;
}

void printRepositoryPullRequestRows(
    const std::vector<RepositoryPullRequestRow>& rows
) {
    std::cout << "\nRepository / Pull Request join\n";
    std::cout << "Repository\tPull Request\tSource -> Target\n";

    for (const auto& row : rows) {
        if (row.repository.has_value()) {
            std::cout << row.repository->name << "\t";
        } else {
            std::cout << "NULL\t";
        }

        if (row.pullRequest.has_value()) {
            std::cout << "#" << row.pullRequest->id << "\t";
            std::cout
                << row.pullRequest->sourceBranch
                << " -> "
                << row.pullRequest->targetBranch;
        } else {
            std::cout << "NULL\tNULL";
        }

        std::cout << '\n';
    }
}

void printGovernanceRows(const std::vector<GovernanceRow>& rows) {
    std::cout
        << "\nGovernance join result\n"
        << "Repository\tPR\tReview\tCI\tRequired Approvals\n";

    for (const auto& row : rows) {
        std::cout << (
            row.repository.has_value()
                ? row.repository->name
                : "NULL"
        ) << '\t';

        std::cout << (
            row.pullRequest.has_value()
                ? std::to_string(row.pullRequest->id)
                : "NULL"
        ) << '\t';

        if (row.review.has_value()) {
            std::cout
                << row.review->reviewer
                << ":"
                << reviewStateToString(row.review->state);
        } else {
            std::cout << "NULL";
        }

        std::cout << '\t';

        if (row.statusCheck.has_value()) {
            std::cout
                << row.statusCheck->name
                << ":"
                << (row.statusCheck->passed ? "PASS" : "FAIL");
        } else {
            std::cout << "NULL";
        }

        std::cout << '\t';

        if (row.policy.has_value()) {
            std::cout << row.policy->requiredApprovals;
        } else {
            std::cout << "NULL";
        }

        std::cout << '\n';
    }
}

void demonstrateJoinTypes() {
    const std::vector<Repository> repositories = {
        {1, "payments-api", "main"},
        {2, "identity-service", "main"},
        {3, "analytics-engine", "main"}
    };

    const std::vector<PullRequest> pullRequests = {
        {101, 1, "feature/cache", "main", false},
        {102, 1, "feature/tracing", "main", false},
        {103, 2, "security/headers", "main", true},
        {104, 9, "external/fix", "main", false}
    };

    for (JoinType type : {
        JoinType::INNER,
        JoinType::LEFT,
        JoinType::RIGHT,
        JoinType::FULL
    }) {
        auto rows = joinRepositoriesAndPullRequests(
            repositories,
            pullRequests,
            type
        );

        printRepositoryPullRequestRows(rows);
    }
}

void demonstrateEnterpriseCaseStudy() {
    const std::vector<Repository> repositories = {
        {1, "payments-api", "main"},
        {2, "identity-service", "main"},
        {3, "analytics-engine", "main"}
    };

    const std::vector<PullRequest> pullRequests = {
        {101, 1, "feature/cache", "main", false},
        {102, 1, "feature/tracing", "main", false},
        {103, 2, "security/headers", "main", false},
        {104, 9, "external/fix", "main", false}
    };

    const std::vector<Review> reviews = {
        {201, 101, "reviewer-a", ReviewState::APPROVED},
        {202, 101, "reviewer-b", ReviewState::APPROVED},
        {203, 102, "reviewer-a", ReviewState::CHANGES_REQUESTED},
        {204, 999, "reviewer-c", ReviewState::APPROVED}
    };

    const std::vector<StatusCheck> checks = {
        {301, 101, "build", true},
        {302, 101, "test", true},
        {303, 102, "build", true},
        {304, 102, "test", false},
        {305, 103, "build", true}
    };

    const std::vector<BranchPolicy> policies = {
        {1, 2, true, true},
        {2, 1, true, true}
    };

    /*
     * LEFT JOIN is appropriate here because governance reporting should not
     * lose repositories or pull requests merely because a related entity is
     * missing. Missing reviews or policies become explicit optional values.
     */
    auto repositoryPrRows = joinRepositoriesAndPullRequests(
        repositories,
        pullRequests,
        JoinType::LEFT
    );

    auto reviewRows = joinPullRequestsToReviews(
        repositoryPrRows,
        reviews,
        JoinType::LEFT
    );

    auto statusRows = joinStatusChecks(
        reviewRows,
        checks,
        JoinType::LEFT
    );

    auto governanceRows = joinBranchPolicies(
        statusRows,
        policies,
        JoinType::LEFT
    );

    printGovernanceRows(governanceRows);

    std::cout << "\nMerge eligibility\n";

    for (const auto& pullRequest : pullRequests) {
        std::optional<BranchPolicy> policy;

        for (const auto& candidate : policies) {
            if (candidate.repositoryId == pullRequest.repositoryId) {
                policy = candidate;
                break;
            }
        }

        const bool eligible = mergeEligible(
            pullRequest,
            reviews,
            checks,
            policy
        );

        std::cout
            << "PR #"
            << pullRequest.id
            << ": "
            << (eligible ? "MERGE ELIGIBLE" : "BLOCKED")
            << '\n';
    }

    /*
     * The orphan review with pullRequestId 999 illustrates why a FULL JOIN is
     * useful for data-quality audits. An ordinary LEFT JOIN from pull requests
     * would not expose that review because its parent does not exist.
     */
    auto auditRows = joinPullRequestsToReviews(
        repositoryPrRows,
        reviews,
        JoinType::FULL
    );

    std::cout << "\nFULL JOIN audit row count: "
              << auditRows.size()
              << '\n';
}

void demonstrateComplexity() {
    std::cout
        << "\nComplexity characteristics\n"
        << "A nested-loop equality join can require O(L * R) comparisons.\n"
        << "The hash-indexed implementation builds an index in O(R) and "
           "performs approximately O(L + R + M) work, where M is the number "
           "of produced matches.\n"
        << "One-to-many relationships can make M substantially larger than "
           "either input table.\n";
}

int main() {
    try {
        demonstrateJoinTypes();
        demonstrateEnterpriseCaseStudy();
        demonstrateComplexity();

        std::cout
            << "\nThe governance case study completed successfully.\n";
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
