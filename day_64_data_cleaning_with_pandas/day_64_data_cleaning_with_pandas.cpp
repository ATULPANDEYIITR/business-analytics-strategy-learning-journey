#include <algorithm>
#include <cctype>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

enum class ReviewState {
    Draft,
    Open,
    Approved,
    ChangesRequested,
    Closed,
    Merged
};

enum class Approval {
    Approved,
    Rejected,
    Pending,
    Dismissed,
    NotRequired
};

enum class StatusCheck {
    Passed,
    Failed,
    Pending
};

struct PullRequestRecord {
    int id{};
    std::string repository;
    std::string sourceBranch;
    std::string targetBranch;
    std::string reviewer;
    ReviewState reviewState;
    Approval approval;
    StatusCheck statusCheck;
    bool draft{};
    bool requiredReview{};
    bool conversationResolved{};
    bool forcePushAllowed{};
    bool mergeEligible{};
};

struct CleaningStats {
    std::size_t rowsBefore{};
    std::size_t rowsAfter{};
    std::size_t duplicatesRemoved{};
    std::size_t invalidRemoved{};
};

static std::string trim(const std::string& input) {
    std::size_t start = 0;
    while (start < input.size() &&
           std::isspace(static_cast<unsigned char>(input[start]))) {
        ++start;
    }

    std::size_t end = input.size();
    while (end > start &&
           std::isspace(static_cast<unsigned char>(input[end - 1]))) {
        --end;
    }

    return input.substr(start, end - start);
}

static std::string lower(std::string value) {
    std::transform(
        value.begin(),
        value.end(),
        value.begin(),
        [](unsigned char c) {
            return static_cast<char>(std::tolower(c));
        }
    );
    return value;
}

static std::string normalizeBranch(std::string value) {
    value = lower(trim(value));

    const std::string prefix = "refs/heads/";
    if (value.rfind(prefix, 0) == 0) {
        value.erase(0, prefix.size());
    }

    return value;
}

static std::optional<bool> parseBoolean(const std::string& value) {
    const std::string v = lower(trim(value));

    if (v == "true" || v == "yes" || v == "1" || v == "on") {
        return true;
    }

    if (v == "false" || v == "no" || v == "0" || v == "off") {
        return false;
    }

    return std::nullopt;
}

static bool mergeEligible(const PullRequestRecord& pr) {
    return pr.reviewState == ReviewState::Approved &&
           pr.approval == Approval::Approved &&
           pr.statusCheck == StatusCheck::Passed &&
           pr.conversationResolved;
}

static std::string makeKey(const PullRequestRecord& pr) {
    return std::to_string(pr.id) + "|" +
           pr.repository + "|" +
           pr.sourceBranch + "|" +
           pr.targetBranch + "|" +
           pr.reviewer;
}

static std::vector<PullRequestRecord> cleanRecords(
    const std::vector<PullRequestRecord>& input,
    CleaningStats& stats
) {
    stats.rowsBefore = input.size();

    std::vector<PullRequestRecord> valid;
    std::unordered_set<std::string> seen;

    for (auto pr : input) {
        pr.repository = trim(pr.repository);
        pr.reviewer = trim(pr.reviewer);
        pr.sourceBranch = normalizeBranch(pr.sourceBranch);
        pr.targetBranch = normalizeBranch(pr.targetBranch);

        if (pr.id <= 0 ||
            pr.repository.empty() ||
            pr.sourceBranch.empty() ||
            pr.targetBranch.empty()) {
            ++stats.invalidRemoved;
            continue;
        }

        const std::string key = makeKey(pr);

        if (!seen.insert(key).second) {
            ++stats.duplicatesRemoved;
            continue;
        }

        if (pr.targetBranch == "main" ||
            pr.targetBranch == "master" ||
            pr.targetBranch == "production") {
            pr.requiredReview = true;
        }

        if (pr.reviewState == ReviewState::Draft) {
            pr.draft = true;
        }

        if (pr.reviewState != ReviewState::Open &&
            pr.reviewState != ReviewState::ChangesRequested) {
            pr.conversationResolved = true;
        }

        // Force-push permission is denied by default after cleaning.
        pr.forcePushAllowed = false;
        pr.mergeEligible = mergeEligible(pr);

        valid.push_back(pr);
    }

    stats.rowsAfter = valid.size();
    return valid;
}

static const char* reviewStateName(ReviewState state) {
    switch (state) {
        case ReviewState::Draft: return "draft";
        case ReviewState::Open: return "open";
        case ReviewState::Approved: return "approved";
        case ReviewState::ChangesRequested: return "changes_requested";
        case ReviewState::Closed: return "closed";
        case ReviewState::Merged: return "merged";
    }
    return "unknown";
}

static const char* approvalName(Approval approval) {
    switch (approval) {
        case Approval::Approved: return "approved";
        case Approval::Rejected: return "rejected";
        case Approval::Pending: return "pending";
        case Approval::Dismissed: return "dismissed";
        case Approval::NotRequired: return "not_required";
    }
    return "unknown";
}

static const char* statusName(StatusCheck status) {
    switch (status) {
        case StatusCheck::Passed: return "passed";
        case StatusCheck::Failed: return "failed";
        case StatusCheck::Pending: return "pending";
    }
    return "unknown";
}

int main() {
    std::vector<PullRequestRecord> records{
        {
            301,
            "payments-api",
            "refs/heads/feature/refunds",
            "MAIN",
            "Priya",
            ReviewState::Approved,
            Approval::Approved,
            StatusCheck::Passed,
            false,
            true,
            true,
            false,
            false
        },
        {
            301,
            "payments-api",
            "refs/heads/feature/refunds",
            "main",
            "Priya",
            ReviewState::Approved,
            Approval::Approved,
            StatusCheck::Passed,
            false,
            true,
            true,
            false,
            false
        },
        {
            302,
            "payments-api",
            "feature/audit",
            "main",
            "Rahul",
            ReviewState::ChangesRequested,
            Approval::Pending,
            StatusCheck::Failed,
            false,
            true,
            false,
            false,
            false
        },
        {
            303,
            "inventory-api",
            "feature/cache",
            "develop",
            "",
            ReviewState::Open,
            Approval::Pending,
            StatusCheck::Pending,
            false,
            false,
            false,
            false,
            false
        },
        {
            304,
            "inventory-api",
            "feature/reports",
            "main",
            "Anita",
            ReviewState::Approved,
            Approval::Approved,
            StatusCheck::Passed,
            false,
            true,
            true,
            false,
            false
        },
        {
            -1,
            "",
            "feature/invalid",
            "main",
            "Unknown",
            ReviewState::Approved,
            Approval::Approved,
            StatusCheck::Passed,
            false,
            true,
            true,
            false,
            false
        }
    };

    CleaningStats stats{};
    const auto cleaned = cleanRecords(records, stats);

    std::cout << "DATA CLEANING AND GOVERNANCE REPORT\n";
    std::cout << "============================================\n";
    std::cout << "Rows before       : " << stats.rowsBefore << '\n';
    std::cout << "Rows after        : " << stats.rowsAfter << '\n';
    std::cout << "Duplicates removed: " << stats.duplicatesRemoved << '\n';
    std::cout << "Invalid removed   : " << stats.invalidRemoved << "\n\n";

    for (const auto& pr : cleaned) {
        std::cout
            << "PR #" << pr.id
            << " | " << pr.repository
            << " | " << pr.sourceBranch
            << " -> " << pr.targetBranch
            << " | review=" << reviewStateName(pr.reviewState)
            << " | approval=" << approvalName(pr.approval)
            << " | check=" << statusName(pr.statusCheck)
            << " | merge=" << std::boolalpha
            << pr.mergeEligible
            << '\n';
    }

    if (cleaned.size() != 4) {
        throw std::runtime_error("Unexpected cleaned record count.");
    }

    if (stats.duplicatesRemoved != 1) {
        throw std::runtime_error("Duplicate detection failed.");
    }

    if (!cleaned.front().mergeEligible) {
        throw std::runtime_error("Merge eligibility validation failed.");
    }

    std::cout << "\nValidation checks passed.\n";

    return 0;
}
