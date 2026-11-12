#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class Channel {
    Organic,
    PaidSearch,
    Social,
    Referral,
    Partnership
};

string channelName(Channel channel) {
    switch (channel) {
        case Channel::Organic: return "Organic";
        case Channel::PaidSearch: return "Paid Search";
        case Channel::Social: return "Social";
        case Channel::Referral: return "Referral";
        case Channel::Partnership: return "Partnership";
    }
    throw invalid_argument("Unknown channel");
}

struct Acquisition {
    Channel channel;
    double advertisingCost;
    double salesCost;
    double marketingCost;
    int customers;
    string period;

    double totalCost() const {
        return advertisingCost + salesCost + marketingCost;
    }

    double cac() const {
        return totalCost() / customers;
    }
};

struct Customer {
    string id;
    string cohort;
    Channel channel;
    double monthlyRevenue;
    double variableCost;
    double lifetimeMonths;
    double churnRate;
};

struct Economics {
    double cac;
    double contribution;
    double margin;
    double grossLtv;
    double contributionLtv;
    double ltvCacRatio;
    optional<double> payback;
    string classification;
};

struct BranchProtection {
    int requiredApprovals = 2;
    bool requireStatusChecks = true;
    bool requireResolvedConversations = true;
    bool prohibitDirectPush = true;
    bool prohibitForcePush = true;
    double minimumLtvCacRatio = 3.0;
    double maximumPaybackMonths = 12.0;
};

struct StatusChecks {
    bool financialValidation = false;
    bool dataQuality = false;
    bool securityAudit = false;

    bool passed() const {
        return financialValidation &&
               dataQuality &&
               securityAudit;
    }
};

enum class ReviewState {
    Pending,
    Approved,
    ChangesRequested,
    Dismissed
};

struct Review {
    string reviewerId;
    ReviewState state;
    bool eligibleReviewer;
    bool stale;
    bool conversationResolved;
};

struct PullRequest {
    int id;
    string sourceBranch;
    string targetBranch;
    string baseCommit;
    string headCommit;
    bool draft = false;
    bool open = true;
    bool mergeConflict = false;
    bool linearHistory = true;
    bool directPush = false;
    bool forcePush = false;
    int resolvedConversations = 0;
    int unresolvedConversations = 0;

    vector<Review> reviews;
    StatusChecks checks;
    optional<Economics> economics;
};

class UnitEconomicsEngine {
private:
    static void validateNonNegative(double value, const string& field) {
        if (!isfinite(value) || value < 0) {
            throw invalid_argument(field + " must be finite and non-negative");
        }
    }

public:
    Economics evaluate(
        const Acquisition& acquisition,
        const Customer& customer
    ) const {
        validateNonNegative(acquisition.advertisingCost, "Advertising cost");
        validateNonNegative(acquisition.salesCost, "Sales cost");
        validateNonNegative(acquisition.marketingCost, "Marketing cost");
        validateNonNegative(customer.monthlyRevenue, "Revenue");
        validateNonNegative(customer.variableCost, "Variable cost");

        if (acquisition.customers <= 0) {
            throw invalid_argument("Customer count must be positive");
        }

        if (customer.lifetimeMonths <= 0 ||
            !isfinite(customer.lifetimeMonths)) {
            throw invalid_argument("Customer lifetime must be positive");
        }

        if (customer.churnRate < 0 || customer.churnRate >= 1 ||
            !isfinite(customer.churnRate)) {
            throw invalid_argument("Invalid churn rate");
        }

        if (acquisition.channel != customer.channel) {
            throw invalid_argument("Acquisition channel mismatch");
        }

        if (customer.monthlyRevenue == 0 &&
            customer.variableCost > 0) {
            throw invalid_argument("Variable cost without revenue");
        }

        double cac = acquisition.cac();
        double contribution =
            customer.monthlyRevenue - customer.variableCost;

        double margin = customer.monthlyRevenue > 0
            ? contribution / customer.monthlyRevenue * 100.0
            : 0.0;

        double grossLtv =
            customer.monthlyRevenue * customer.lifetimeMonths;

        double contributionLtv =
            contribution * customer.lifetimeMonths;

        optional<double> payback;

        if (contribution > 0) {
            payback = cac / contribution;
        }

        double ratio = cac > 0
            ? contributionLtv / cac
            : contributionLtv > 0
                ? INFINITY
                : 0.0;

        string classification;

        if (contribution <= 0) {
            classification = "NEGATIVE_CONTRIBUTION";
        } else if (contributionLtv <= cac) {
            classification = "UNPROFITABLE";
        } else if (payback && *payback <= customer.lifetimeMonths) {
            classification = "LIFETIME_POSITIVE";
        } else {
            classification = "PAYBACK_EXCEEDS_LIFETIME";
        }

        return {
            cac,
            contribution,
            margin,
            grossLtv,
            contributionLtv,
            ratio,
            payback,
            classification
        };
    }
};

class CohortAnalyzer {
public:
    struct Aggregate {
        int customers = 0;
        double revenue = 0;
        double variableCost = 0;
    };

    map<string, Aggregate> analyze(
        const vector<Customer>& customers
    ) const {
        map<string, Aggregate> result;

        for (const auto& customer : customers) {
            auto& aggregate = result[customer.cohort];

            aggregate.customers++;
            aggregate.revenue += customer.monthlyRevenue;
            aggregate.variableCost += customer.variableCost;
        }

        return result;
    }
};

class GovernanceEngine {
private:
    BranchProtection policy;

    int countEligibleApprovals(const PullRequest& pr) const {
        set<string> reviewers;

        for (const auto& review : pr.reviews) {
            if (review.eligibleReviewer &&
                !review.stale &&
                review.state == ReviewState::Approved) {
                reviewers.insert(review.reviewerId);
            }
        }

        return static_cast<int>(reviewers.size());
    }

public:
    explicit GovernanceEngine(BranchProtection protection)
        : policy(protection) {}

    vector<string> evaluate(const PullRequest& pr) const {
        vector<string> violations;

        if (!pr.open) {
            violations.push_back("PULL_REQUEST_CLOSED");
        }

        if (pr.draft) {
            violations.push_back("DRAFT_NOT_MERGEABLE");
        }

        if (pr.sourceBranch.empty() || pr.targetBranch.empty()) {
            violations.push_back("INVALID_BRANCH_REFERENCE");
        }

        if (pr.sourceBranch == pr.targetBranch) {
            violations.push_back("SOURCE_EQUALS_TARGET");
        }

        if (pr.mergeConflict) {
            violations.push_back("MERGE_CONFLICT");
        }

        if (pr.directPush && policy.prohibitDirectPush) {
            violations.push_back("DIRECT_PUSH_PROHIBITED");
        }

        if (pr.forcePush && policy.prohibitForcePush) {
            violations.push_back("FORCE_PUSH_PROHIBITED");
        }

        if (!pr.linearHistory) {
            violations.push_back("LINEAR_HISTORY_REQUIRED");
        }

        if (policy.requireStatusChecks && !pr.checks.passed()) {
            violations.push_back("REQUIRED_STATUS_CHECK_FAILED");
        }

        if (countEligibleApprovals(pr) < policy.requiredApprovals) {
            violations.push_back("INSUFFICIENT_APPROVALS");
        }

        for (const auto& review : pr.reviews) {
            if (review.eligibleReviewer &&
                !review.stale &&
                review.state == ReviewState::ChangesRequested) {
                violations.push_back("CHANGES_REQUESTED");
                break;
            }
        }

        if (policy.requireResolvedConversations &&
            pr.unresolvedConversations > 0) {
            violations.push_back("UNRESOLVED_CONVERSATIONS");
        }

        if (!pr.economics) {
            violations.push_back("ECONOMICS_NOT_EVALUATED");
        } else {
            const auto& economics = *pr.economics;

            if (economics.contribution <= 0) {
                violations.push_back("NON_POSITIVE_CONTRIBUTION");
            }

            if (economics.ltvCacRatio < policy.minimumLtvCacRatio) {
                violations.push_back("LTV_CAC_BELOW_POLICY");
            }

            if (!economics.payback ||
                *economics.payback > policy.maximumPaybackMonths) {
                violations.push_back("PAYBACK_EXCEEDS_POLICY");
            }
        }

        return violations;
    }

    bool mergeEligible(const PullRequest& pr) const {
        return evaluate(pr).empty();
    }
};

void printEconomics(const Economics& result) {
    cout << fixed << setprecision(2);

    cout << "\nCUSTOMER UNIT ECONOMICS\n";
    cout << "CAC: INR " << result.cac << '\n';
    cout << "Monthly contribution: INR " << result.contribution << '\n';
    cout << "Contribution margin: " << result.margin << "%\n";
    cout << "Gross LTV: INR " << result.grossLtv << '\n';
    cout << "Contribution LTV: INR " << result.contributionLtv << '\n';
    cout << "LTV/CAC: " << result.ltvCacRatio << '\n';

    cout << "Payback: ";

    if (result.payback) {
        cout << *result.payback << " months\n";
    } else {
        cout << "Not achievable\n";
    }

    cout << "Classification: " << result.classification << '\n';
}

void runTests(const UnitEconomicsEngine& engine) {
    Acquisition acquisition{
        Channel::PaidSearch, 30000, 10000, 10000, 100, "2026-01"
    };

    Customer customer{
        "C001", "2026-Q1", Channel::PaidSearch,
        1000, 300, 18, 0.04
    };

    Economics result = engine.evaluate(acquisition, customer);

    if (abs(result.cac - 500) > 0.001 ||
        abs(result.contribution - 700) > 0.001 ||
        abs(*result.payback - 500.0 / 700.0) > 0.001) {
        throw runtime_error("Calculation test failed");
    }

    cout << "Unit economics tests passed.\n";
}

int main() {
    try {
        UnitEconomicsEngine economicsEngine;
        runTests(economicsEngine);

        Acquisition acquisition{
            Channel::PaidSearch,
            30000,
            10000,
            10000,
            100,
            "2026-01"
        };

        Customer customer{
            "C001",
            "2026-Q1",
            Channel::PaidSearch,
            1000,
            300,
            18,
            0.04
        };

        Economics economics =
            economicsEngine.evaluate(acquisition, customer);

        printEconomics(economics);

        vector<Customer> customers = {
            customer,
            {
                "C002", "2026-Q1", Channel::Social,
                800, 280, 15, 0.05
            },
            {
                "C003", "2026-Q2", Channel::Referral,
                1200, 350, 24, 0.025
            }
        };

        CohortAnalyzer analyzer;
        auto cohorts = analyzer.analyze(customers);

        cout << "\nCOHORT ANALYSIS\n";

        for (const auto& [name, aggregate] : cohorts) {
            double contribution =
                aggregate.revenue - aggregate.variableCost;

            double margin = aggregate.revenue > 0
                ? contribution / aggregate.revenue * 100
                : 0;

            cout << name
                 << " | Customers: " << aggregate.customers
                 << " | Revenue: " << aggregate.revenue
                 << " | Contribution: " << contribution
                 << " | Margin: " << margin << "%\n";
        }

        BranchProtection protection;
        protection.requiredApprovals = 2;
        protection.minimumLtvCacRatio = 3;
        protection.maximumPaybackMonths = 12;

        GovernanceEngine governance(protection);

        PullRequest pr;
        pr.id = 101;
        pr.sourceBranch = "feature/pricing-optimization";
        pr.targetBranch = "main";
        pr.baseCommit = "base-commit-001";
        pr.headCommit = "head-commit-009";
        pr.linearHistory = true;
        pr.checks = {true, true, true};
        pr.resolvedConversations = 4;
        pr.unresolvedConversations = 0;
        pr.economics = economics;

        pr.reviews = {
            {"reviewer-01", ReviewState::Approved, true, false, true},
            {"reviewer-02", ReviewState::Approved, true, false, true}
        };

        cout << "\nREPOSITORY MERGE GOVERNANCE\n";

        auto violations = governance.evaluate(pr);

        if (violations.empty()) {
            cout << "Merge eligible: YES\n";
        } else {
            cout << "Merge eligible: NO\n";

            for (const auto& violation : violations) {
                cout << "- " << violation << '\n';
            }
        }

        // Demonstrate an adverse acquisition scenario.
        Acquisition expensiveAcquisition{
            Channel::Social, 90000, 20000, 10000, 100, "2026-02"
        };

        Customer socialCustomer{
            "C004", "2026-Q2", Channel::Social,
            500, 350, 12, 0.08
        };

        auto adverse = economicsEngine.evaluate(
            expensiveAcquisition,
            socialCustomer
        );

        cout << "\nADVERSE SCENARIO\n";
        printEconomics(adverse);

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
