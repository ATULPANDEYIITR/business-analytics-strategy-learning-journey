#include <algorithm>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

enum class PullRequestState {
    Draft,
    Open,
    Closed,
    Merged
};

enum class ReviewState {
    Commented,
    Approved,
    ChangesRequested,
    Dismissed
};

enum class CheckState {
    Passing,
    Failing,
    Pending
};

enum class MergeStrategy {
    MergeCommit,
    Squash,
    Rebase
};

struct Commit {
    std::string sha;
    std::string message;
    std::string author;
};

struct ReviewComment {
    int id;
    std::string reviewer;
    std::string body;
    bool resolved;
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::vector<ReviewComment> comments;
};

struct StatusCheck {
    std::string name;
    CheckState state;
    bool required;
};

struct BranchProtection {
    int requiredReviews{2};
    std::set<std::string> requiredChecks;
    bool requireConversationResolution{true};
    bool requireLinearHistory{false};
    bool allowForcePush{false};
    bool allowDirectPush{false};
    bool allowDeletion{false};
};

struct Branch {
    std::string name;
    bool protectedBranch;
    std::vector<Commit> commits;
};

struct PullRequest {
    int number;
    std::string sourceBranch;
    std::string targetBranch;
    std::string title;
    PullRequestState state;
    std::vector<Commit> commits;
    std::vector<Review> reviews;
    std::vector<ReviewComment> comments;
    std::vector<StatusCheck> checks;
    MergeStrategy strategy;

    int unresolvedConversations() const {
        return static_cast<int>(std::count_if(
            comments.begin(),
            comments.end(),
            [](const ReviewComment& c) { return !c.resolved; }
        ));
    }
};

struct Repository {
    std::string name;
    std::map<std::string, Branch> branches;
    std::map<int, PullRequest> pullRequests;
    std::map<std::string, BranchProtection> protection;
    std::set<std::string> eligibleReviewers;
};

struct Evaluation {
    bool eligible;
    std::vector<std::string> reasons;
};

struct DashboardMetrics {
    int open{};
    int drafts{};
    int mergeable{};
    int blocked{};
    int merged{};
    int unresolvedConversations{};
};

class GovernanceEngine {
private:
    const Repository& repository;

    bool isEligibleReviewer(const std::string& reviewer) const {
        return repository.eligibleReviewers.contains(reviewer);
    }

    int activeApprovals(const PullRequest& pr) const {
        std::set<std::string> approved;

        /*
         * A reviewer is counted once. A changes-requested decision removes
         * that reviewer's current approval, preventing duplicate approval
         * records from inflating the dashboard.
         */
        for (const auto& review : pr.reviews) {
            if (!isEligibleReviewer(review.reviewer)) {
                continue;
            }

            if (review.state == ReviewState::Approved) {
                approved.insert(review.reviewer);
            } else if (review.state == ReviewState::ChangesRequested) {
                approved.erase(review.reviewer);
            }
        }

        return static_cast<int>(approved.size());
    }

public:
    explicit GovernanceEngine(const Repository& repo) : repository(repo) {}

    Evaluation evaluate(const PullRequest& pr) const {
        std::vector<std::string> reasons;

        if (pr.state != PullRequestState::Open) {
            reasons.push_back("Pull Request is not open.");
        }

        if (pr.state == PullRequestState::Draft) {
            reasons.push_back("Draft Pull Requests cannot be merged.");
        }

        auto policyIt = repository.protection.find(pr.targetBranch);
        if (policyIt == repository.protection.end()) {
            reasons.push_back("Target branch has no protection policy.");
            return {false, reasons};
        }

        const auto& policy = policyIt->second;

        const int approvals = activeApprovals(pr);
        if (approvals < policy.requiredReviews) {
            reasons.push_back(
                "Required approvals: " +
                std::to_string(policy.requiredReviews) +
                "; eligible approvals: " +
                std::to_string(approvals) + "."
            );
        }

        std::map<std::string, CheckState> checks;
        for (const auto& check : pr.checks) {
            checks[check.name] = check.state;
        }

        for (const auto& required : policy.requiredChecks) {
            auto it = checks.find(required);

            if (it == checks.end() || it->second != CheckState::Passing) {
                reasons.push_back(
                    "Required status check '" + required +
                    "' is not passing."
                );
            }
        }

        if (
            policy.requireConversationResolution &&
            pr.unresolvedConversations() > 0
        ) {
            reasons.push_back("Unresolved review conversations remain.");
        }

        if (
            policy.requireLinearHistory &&
            pr.strategy == MergeStrategy::MergeCommit
        ) {
            reasons.push_back("Linear history is required.");
        }

        return {reasons.empty(), reasons};
    }

    DashboardMetrics metrics() const {
        DashboardMetrics metrics;

        for (const auto& [id, pr] : repository.pullRequests) {
            switch (pr.state) {
                case PullRequestState::Draft:
                    ++metrics.drafts;
                    ++metrics.open;
                    break;
                case PullRequestState::Open:
                    ++metrics.open;
                    break;
                case PullRequestState::Merged:
                    ++metrics.merged;
                    break;
                case PullRequestState::Closed:
                    break;
            }

            metrics.unresolvedConversations += pr.unresolvedConversations();

            if (pr.state == PullRequestState::Open) {
                if (evaluate(pr).eligible) {
                    ++metrics.mergeable;
                } else {
                    ++metrics.blocked;
                }
            }
        }

        return metrics;
    }
};

void validateRepository(const Repository& repo) {
    if (repo.name.empty()) {
        throw std::invalid_argument("Repository name cannot be empty.");
    }

    if (!repo.branches.contains("main")) {
        throw std::invalid_argument("Repository must contain main.");
    }

    for (const auto& [branch, policy] : repo.protection) {
        if (!repo.branches.contains(branch)) {
            throw std::invalid_argument(
                "Protection references unknown branch: " + branch
            );
        }

        if (policy.requiredReviews < 0) {
            throw std::invalid_argument(
                "Required reviews cannot be negative."
            );
        }
    }

    for (const auto& [id, pr] : repo.pullRequests) {
        if (!repo.branches.contains(pr.sourceBranch)) {
            throw std::invalid_argument(
                "Unknown source branch: " + pr.sourceBranch
            );
        }

        if (!repo.branches.contains(pr.targetBranch)) {
            throw std::invalid_argument(
                "Unknown target branch: " + pr.targetBranch
            );
        }
    }
}

Repository createRepository() {
    std::vector<Commit> commits{
        {"abc001", "Create dashboard shell", "alice"},
        {"abc002", "Add merge governance metrics", "alice"}
    };

    PullRequest pr{
        77,
        "feature/governance-dashboard",
        "main",
        "Repository governance dashboard",
        PullRequestState::Open,
        commits,
        {
            {"bob", ReviewState::Approved, {}},
            {"carol", ReviewState::Approved, {}}
        },
        {
            {1, "bob", "Please define the blocked state.", true},
            {2, "carol", "Check the policy hierarchy.", false}
        },
        {
            {"unit-tests", CheckState::Passing, true},
            {"security-scan", CheckState::Passing, true},
            {"performance", CheckState::Pending, false}
        },
        MergeStrategy::Squash
    };

    Repository repo;
    repo.name = "platform-governance";
    repo.branches.emplace(
        "main",
        Branch{"main", true, commits}
    );
    repo.branches.emplace(
        "feature/governance-dashboard",
        Branch{"feature/governance-dashboard", false, commits}
    );
    repo.pullRequests.emplace(pr.number, pr);

    BranchProtection policy;
    policy.requiredReviews = 2;
    policy.requiredChecks = {"unit-tests", "security-scan"};
    policy.requireConversationResolution = true;
    policy.requireLinearHistory = true;

    repo.protection.emplace("main", policy);
    repo.eligibleReviewers = {"alice", "bob", "carol", "david"};

    return repo;
}

int main() {
    try {
        Repository repository = createRepository();
        validateRepository(repository);

        GovernanceEngine engine(repository);
        DashboardMetrics metrics = engine.metrics();

        std::cout << "REPOSITORY GOVERNANCE DASHBOARD\n";
        std::cout << "============================================\n";
        std::cout << std::left
                  << std::setw(30) << "Open Pull Requests"
                  << metrics.open << '\n'
                  << std::setw(30) << "Draft Pull Requests"
                  << metrics.drafts << '\n'
                  << std::setw(30) << "Mergeable Pull Requests"
                  << metrics.mergeable << '\n'
                  << std::setw(30) << "Blocked Pull Requests"
                  << metrics.blocked << '\n'
                  << std::setw(30) << "Merged Pull Requests"
                  << metrics.merged << '\n'
                  << std::setw(30) << "Unresolved Conversations"
                  << metrics.unresolvedConversations << '\n';

        const PullRequest& pr = repository.pullRequests.at(77);
        Evaluation evaluation = engine.evaluate(pr);

        std::cout << "\nMERGE ELIGIBILITY\n";
        std::cout << "============================================\n";
        std::cout << "Eligible: "
                  << (evaluation.eligible ? "yes" : "no") << '\n';

        for (const auto& reason : evaluation.reasons) {
            std::cout << "- " << reason << '\n';
        }

        std::cout << "\nARCHITECTURAL VIEW\n";
        std::cout << "============================================\n";
        std::cout << "Repository -> Branch -> Pull Request -> Review\n";
        std::cout << "Review -> Approval -> Status Checks\n";
        std::cout << "Branch Protection -> Merge Eligibility -> Merge\n";

        return evaluation.eligible ? 0 : 2;
    } catch (const std::exception& ex) {
        std::cerr << "Governance failure: " << ex.what() << '\n';
        return 1;
    }
}
