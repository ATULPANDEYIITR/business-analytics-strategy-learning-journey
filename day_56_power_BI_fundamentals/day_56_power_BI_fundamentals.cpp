#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

enum class ReviewState {
    Pending,
    Approved,
    Rejected
};

enum class MergeStrategy {
    MergeCommit,
    Squash,
    Rebase
};

struct Commit {
    std::string hash;
    std::string message;
};

struct Review {
    std::string reviewer;
    ReviewState state;
    bool stale;
};

struct StatusCheck {
    std::string name;
    bool passed;
    bool required;
};

struct BranchProtection {
    bool requirePullRequest;
    bool requireApprovals;
    int requiredApprovals;
    bool requireStatusChecks;
    bool blockDirectPush;
    bool blockForcePush;
    bool requireConversationResolution;
    bool requireLinearHistory;
    std::unordered_set<std::string> requiredChecks;
};

struct PullRequest {
    int id;
    std::string sourceBranch;
    std::string targetBranch;
    std::vector<Commit> commits;
    std::vector<Review> reviews;
    std::vector<StatusCheck> checks;
    int unresolvedConversations;
    bool draft;
    bool closed;
    bool conflict;
};

class GovernanceEngine {
public:
    explicit GovernanceEngine(BranchProtection protection)
        : protection_(std::move(protection)) {}

    bool eligibleForMerge(const PullRequest& pr,
                          const std::unordered_set<std::string>& eligibleReviewers,
                          std::vector<std::string>& failures) const {
        failures.clear();

        if (pr.closed) {
            failures.push_back("Pull Request is closed.");
        }

        if (pr.draft) {
            failures.push_back("Pull Request is still a draft.");
        }

        if (pr.sourceBranch.empty() || pr.targetBranch.empty()) {
            failures.push_back("Source and target branches are required.");
        }

        if (pr.sourceBranch == pr.targetBranch) {
            failures.push_back("Source and target branches cannot be identical.");
        }

        if (pr.commits.empty()) {
            failures.push_back("Pull Request contains no commits.");
        }

        if (pr.conflict) {
            failures.push_back("Pull Request has unresolved merge conflicts.");
        }

        if (protection_.requirePullRequest && pr.id <= 0) {
            failures.push_back("A valid Pull Request is required.");
        }

        if (protection_.requireApprovals) {
            std::unordered_set<std::string> approvingReviewers;

            for (const Review& review : pr.reviews) {
                if (review.state == ReviewState::Approved &&
                    !review.stale &&
                    eligibleReviewers.contains(review.reviewer)) {
                    approvingReviewers.insert(review.reviewer);
                }
            }

            if (static_cast<int>(approvingReviewers.size()) <
                protection_.requiredApprovals) {
                failures.push_back(
                    "Required number of current eligible approvals is missing."
                );
            }
        }

        if (protection_.requireStatusChecks) {
            std::unordered_map<std::string, bool> checkResults;

            for (const StatusCheck& check : pr.checks) {
                checkResults[check.name] = check.passed;
            }

            for (const auto& required : protection_.requiredChecks) {
                auto it = checkResults.find(required);

                if (it == checkResults.end()) {
                    failures.push_back("Missing required check: " + required);
                } else if (!it->second) {
                    failures.push_back("Failed required check: " + required);
                }
            }
        }

        if (protection_.requireConversationResolution &&
            pr.unresolvedConversations > 0) {
            failures.push_back("Unresolved review conversations remain.");
        }

        if (protection_.requireLinearHistory &&
            protection_.requirePullRequest &&
            pr.commits.size() > 1000) {
            failures.push_back(
                "History exceeds the configured governance inspection limit."
            );
        }

        return failures.empty();
    }

    void printDecision(const PullRequest& pr,
                       const std::unordered_set<std::string>& eligibleReviewers) const {
        std::vector<std::string> failures;

        const bool eligible =
            eligibleForMerge(pr, eligibleReviewers, failures);

        std::cout << "\nPull Request #" << pr.id << "\n";
        std::cout << "  " << pr.sourceBranch
                  << " -> " << pr.targetBranch << "\n";
        std::cout << "  Merge strategy: "
                  << mergeStrategyName(MergeStrategy::Squash) << "\n";
        std::cout << "  Decision: "
                  << (eligible ? "MERGE ELIGIBLE" : "BLOCKED") << "\n";

        if (!eligible) {
            for (const auto& failure : failures) {
                std::cout << "  - " << failure << "\n";
            }
        }
    }

private:
    BranchProtection protection_;

    static std::string mergeStrategyName(MergeStrategy strategy) {
        switch (strategy) {
            case MergeStrategy::MergeCommit:
                return "Merge Commit";
            case MergeStrategy::Squash:
                return "Squash";
            case MergeStrategy::Rebase:
                return "Rebase";
        }

        return "Unknown";
    }
};

void validateBranchName(const std::string& branch) {
    if (branch.empty() || branch.front() == '/' || branch.back() == '/') {
        throw std::invalid_argument("Invalid branch name.");
    }

    if (branch.find("..") != std::string::npos ||
        branch.find(' ') != std::string::npos) {
        throw std::invalid_argument("Branch name contains forbidden syntax.");
    }
}

int main() {
    try {
        BranchProtection protection{
            true,  // Pull Request required
            true,  // Approvals required
            2,     // Two approvals
            true,  // Status checks required
            true,  // Direct push blocked
            true,  // Force push blocked
            true,  // Conversations must be resolved
            true,  // Linear history policy
            {"build", "unit-tests", "security-scan"}
        };

        GovernanceEngine engine(protection);

        validateBranchName("feature/power-bi-dashboard");

        std::unordered_set<std::string> eligibleReviewers{
            "analyst-1",
            "engineer-2",
            "architect-3"
        };

        PullRequest ready{
            101,
            "feature/power-bi-dashboard",
            "main",
            {
                {"a81c", "Add sales dataset"},
                {"b92d", "Add report measures"},
                {"c73e", "Add validation rules"}
            },
            {
                {"analyst-1", ReviewState::Approved, false},
                {"engineer-2", ReviewState::Approved, false},
                {"architect-3", ReviewState::Approved, true}
            },
            {
                {"build", true, true},
                {"unit-tests", true, true},
                {"security-scan", true, true}
            },
            0,
            false,
            false,
            false
        };

        engine.printDecision(ready, eligibleReviewers);

        PullRequest blocked = ready;
        blocked.id = 102;
        blocked.reviews[0].stale = true;
        blocked.checks[2].passed = false;
        blocked.unresolvedConversations = 1;

        engine.printDecision(blocked, eligibleReviewers);

        PullRequest draft = ready;
        draft.id = 103;
        draft.draft = true;

        engine.printDecision(draft, eligibleReviewers);

        // Governance state is evaluated in O(C + R), where C is the number
        // of checks and R is the number of reviews.
        std::cout << "\nGovernance evaluation completed.\n";
        std::cout << "Direct pushes and force pushes are represented as "
                     "repository policy constraints rather than review decisions.\n";
    }
    catch (const std::exception& ex) {
        std::cerr << "Fatal configuration error: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}
