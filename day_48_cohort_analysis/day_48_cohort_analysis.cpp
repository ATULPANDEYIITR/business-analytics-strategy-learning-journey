#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <vector>

struct Customer {
    std::string id;
    std::string cohort;
    std::string acquisitionChannel;
    std::string plan;
};

struct Event {
    std::string customerId;
    int period;
    std::string type;
    double revenue;
};

struct BranchPolicy {
    bool protectedBranch = true;
    bool restrictDirectPush = true;
    bool restrictForcePush = true;
    bool restrictDeletion = true;
    bool requireLinearHistory = false;
    bool requireConversationResolution = true;
    int requiredApprovals = 2;
    std::set<std::string> requiredChecks;
};

enum class ReviewState {
    Commented,
    ChangesRequested,
    Approved,
    Dismissed
};

struct Review {
    std::string reviewer;
    ReviewState state;
    bool eligible;
};

struct PullRequest {
    int id;
    std::string sourceBranch;
    std::string targetBranch;
    std::set<std::string> commits;
    std::vector<Review> reviews;
    std::map<std::string, bool> statusChecks;
    bool draft = false;
    bool conflicts = false;
    bool conversationsResolved = true;
    bool open = true;
    bool baseBranchChangedSinceReview = false;
};

struct EvaluationResult {
    bool eligible;
    std::vector<std::string> reasons;
};

class GovernanceEngine {
private:
    std::unordered_map<std::string, BranchPolicy> policies;

public:
    void addPolicy(const std::string& branch, const BranchPolicy& policy) {
        policies[branch] = policy;
    }

    EvaluationResult evaluate(const PullRequest& pr) const {
        EvaluationResult result{true, {}};

        if (!pr.open) {
            result.eligible = false;
            result.reasons.push_back("Pull Request is closed.");
        }

        if (pr.draft) {
            result.eligible = false;
            result.reasons.push_back("Draft Pull Request cannot be merged.");
        }

        if (pr.sourceBranch.empty() || pr.targetBranch.empty()) {
            result.eligible = false;
            result.reasons.push_back("Source and target branches are required.");
        }

        if (pr.sourceBranch == pr.targetBranch) {
            result.eligible = false;
            result.reasons.push_back("Source and target branches must differ.");
        }

        if (pr.commits.empty()) {
            result.eligible = false;
            result.reasons.push_back("Pull Request contains no commits.");
        }

        if (pr.conflicts) {
            result.eligible = false;
            result.reasons.push_back("Merge conflicts must be resolved.");
        }

        auto policyIt = policies.find(pr.targetBranch);

        if (policyIt == policies.end()) {
            result.eligible = false;
            result.reasons.push_back("No governance policy exists for target branch.");
            return result;
        }

        const BranchPolicy& policy = policyIt->second;

        if (!policy.protectedBranch) {
            return result;
        }

        if (policy.requireConversationResolution && !pr.conversationsResolved) {
            result.eligible = false;
            result.reasons.push_back("Unresolved review conversations remain.");
        }

        for (const auto& [check, passed] : pr.statusChecks) {
            if (!passed) {
                result.eligible = false;
                result.reasons.push_back("Required status check failed: " + check);
            }
        }

        for (const std::string& required : policy.requiredChecks) {
            auto it = pr.statusChecks.find(required);

            if (it == pr.statusChecks.end()) {
                result.eligible = false;
                result.reasons.push_back("Required status check missing: " + required);
            } else if (!it->second) {
                result.eligible = false;
                result.reasons.push_back("Required status check failed: " + required);
            }
        }

        std::set<std::string> validApprovers;
        bool changesRequested = false;

        for (const Review& review : pr.reviews) {
            if (!review.eligible) {
                continue;
            }

            if (review.state == ReviewState::ChangesRequested) {
                changesRequested = true;
            }

            if (review.state == ReviewState::Approved) {
                validApprovers.insert(review.reviewer);
            }
        }

        if (changesRequested) {
            result.eligible = false;
            result.reasons.push_back("An eligible reviewer has requested changes.");
        }

        if (pr.baseBranchChangedSinceReview) {
            result.eligible = false;
            result.reasons.push_back(
                "Base branch changed after approval; policy requires revalidation."
            );
        }

        if (static_cast<int>(validApprovers.size()) < policy.requiredApprovals) {
            result.eligible = false;
            result.reasons.push_back(
                "Required approval count has not been reached."
            );
        }

        return result;
    }
};

class CohortGovernanceReport {
private:
    std::vector<Customer> customers;
    std::vector<Event> events;

public:
    CohortGovernanceReport(
        std::vector<Customer> customers,
        std::vector<Event> events
    )
        : customers(std::move(customers)), events(std::move(events)) {}

    std::map<std::string, std::set<std::string>> activeUsersByCohortPeriod() const {
        std::map<std::string, std::set<std::string>> result;

        std::unordered_map<std::string, Customer> customerIndex;

        for (const auto& customer : customers) {
            if (customerIndex.contains(customer.id)) {
                throw std::runtime_error("Duplicate customer ID: " + customer.id);
            }

            customerIndex[customer.id] = customer;
        }

        for (const auto& event : events) {
            if (!customerIndex.contains(event.customerId)) {
                throw std::runtime_error(
                    "Event references unknown customer: " + event.customerId
                );
            }

            const auto& customer = customerIndex.at(event.customerId);

            if (event.revenue < 0) {
                throw std::runtime_error("Negative revenue is invalid.");
            }

            std::string key =
                customer.cohort + "|M" + std::to_string(event.period);

            result[key].insert(event.customerId);
        }

        return result;
    }

    void printRetention() const {
        auto activity = activeUsersByCohortPeriod();

        std::map<std::string, int> cohortSizes;

        for (const auto& customer : customers) {
            cohortSizes[customer.cohort]++;
        }

        std::cout << "\nCOHORT RETENTION\n";
        std::cout << "===============================\n";

        for (const auto& [key, active] : activity) {
            auto delimiter = key.find('|');
            std::string cohort = key.substr(0, delimiter);
            std::string period = key.substr(delimiter + 1);

            double retention =
                static_cast<double>(active.size()) / cohortSizes.at(cohort);

            std::cout << cohort
                      << " "
                      << period
                      << " active="
                      << active.size()
                      << " retention="
                      << std::fixed
                      << std::setprecision(1)
                      << retention * 100
                      << "%\n";
        }
    }
};

static void demonstrateGovernance() {
    BranchPolicy mainPolicy;
    mainPolicy.protectedBranch = true;
    mainPolicy.restrictDirectPush = true;
    mainPolicy.restrictForcePush = true;
    mainPolicy.restrictDeletion = true;
    mainPolicy.requireConversationResolution = true;
    mainPolicy.requiredApprovals = 2;
    mainPolicy.requiredChecks = {
        "unit-tests",
        "security-scan",
        "build"
    };

    GovernanceEngine engine;
    engine.addPolicy("main", mainPolicy);

    PullRequest healthy{
        104,
        "feature/cohort-retention",
        "main",
        {"a91f", "b72e"},
        {
            {"reviewer-alice", ReviewState::Approved, true},
            {"reviewer-bob", ReviewState::Approved, true},
            {"external-reviewer", ReviewState::Approved, false}
        },
        {
            {"unit-tests", true},
            {"security-scan", true},
            {"build", true}
        },
        false,
        false,
        true,
        true,
        false
    };

    PullRequest blocked = healthy;
    blocked.id = 105;
    blocked.conflicts = true;
    blocked.statusChecks["security-scan"] = false;

    for (const PullRequest& pr : {healthy, blocked}) {
        EvaluationResult evaluation = engine.evaluate(pr);

        std::cout << "\nPull Request #" << pr.id << "\n";
        std::cout << "Merge eligible: "
                  << (evaluation.eligible ? "YES" : "NO")
                  << "\n";

        for (const auto& reason : evaluation.reasons) {
            std::cout << "  " << reason << "\n";
        }
    }

    std::cout << "\nGovernance distinctions:\n";
    std::cout << "Pull Request = proposed change and merge lifecycle.\n";
    std::cout << "Code Review = evaluation and reviewer discussion.\n";
    std::cout << "Approval = explicit review decision from an eligible reviewer.\n";
    std::cout << "Branch Protection = repository-level rules controlling merge eligibility.\n";
}

int main() {
    try {
        std::vector<Customer> customers{
            {"C001", "2026-01", "organic", "pro"},
            {"C002", "2026-01", "paid", "basic"},
            {"C003", "2026-02", "referral", "pro"},
            {"C004", "2026-02", "organic", "basic"},
            {"C005", "2026-03", "paid", "pro"},
            {"C006", "2026-03", "referral", "basic"}
        };

        std::vector<Event> events{
            {"C001", 0, "signup", 0},
            {"C001", 0, "purchase", 49},
            {"C001", 1, "login", 0},
            {"C001", 2, "purchase", 49},
            {"C002", 0, "signup", 0},
            {"C002", 1, "login", 0},
            {"C003", 0, "signup", 0},
            {"C003", 1, "purchase", 49},
            {"C004", 0, "signup", 0},
            {"C005", 0, "signup", 0},
            {"C005", 1, "purchase", 49},
            {"C006", 0, "signup", 0}
        };

        CohortGovernanceReport report(customers, events);
        report.printRetention();

        demonstrateGovernance();

        std::cout << "\nPerformance characteristics:\n";
        std::cout << "Customer lookup uses an unordered_map for expected O(1) access.\n";
        std::cout << "Active users use sets so repeated events do not inflate retention.\n";
        std::cout << "Governance evaluation scans reviews and required checks once, "
                     "making it proportional to policy and Pull Request state size.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }
}
