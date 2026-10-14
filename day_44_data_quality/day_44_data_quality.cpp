#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

/*
 * Repository Data Quality Case Study
 *
 * Scenario:
 * A platform receives customer master data from several operational systems.
 * Before the dataset reaches an analytical database, a C++ quality engine
 * evaluates accuracy, completeness, consistency, and validity.
 *
 * The implementation uses C++17 standard-library facilities only.
 */

enum class Dimension {
    Accuracy,
    Completeness,
    Consistency,
    Validity
};

std::string dimensionName(Dimension dimension) {
    switch (dimension) {
        case Dimension::Accuracy: return "Accuracy";
        case Dimension::Completeness: return "Completeness";
        case Dimension::Consistency: return "Consistency";
        case Dimension::Validity: return "Validity";
    }
    return "Unknown";
}

struct Customer {
    std::string id;
    std::string name;
    std::string email;
    std::string country;
    std::string currency;
    std::string status;
    std::string signupDate;
    double creditLimit{};
};

struct Issue {
    Dimension dimension;
    std::string field;
    std::string customerId;
    std::string message;
};

struct ReferenceCustomer {
    std::string email;
    std::string country;
    std::string currency;
};

class DataQualityException : public std::runtime_error {
public:
    explicit DataQualityException(const std::string& message)
        : std::runtime_error(message) {}
};

class QualityEngine {
private:
    const std::set<std::string> validCountries{
        "IN", "US", "GB", "DE", "FR", "JP", "SG", "AU"
    };

    const std::set<std::string> validStatuses{
        "active", "inactive", "pending"
    };

    const std::map<std::string, std::string> currencyByCountry{
        {"IN", "INR"},
        {"US", "USD"},
        {"GB", "GBP"},
        {"DE", "EUR"},
        {"FR", "EUR"},
        {"JP", "JPY"},
        {"SG", "SGD"},
        {"AU", "AUD"}
    };

    const std::map<std::string, ReferenceCustomer> verifiedCustomers{
        {
            "C1001",
            {"atul@example.com", "IN", "INR"}
        },
        {
            "C1002",
            {"maria@example.com", "DE", "EUR"}
        }
    };

    static bool isBlank(const std::string& value) {
        return value.empty();
    }

    static bool looksLikeEmail(const std::string& email) {
        const auto at = email.find('@');
        const auto dot = email.rfind('.');

        return at != std::string::npos &&
               at > 0 &&
               dot != std::string::npos &&
               dot > at + 1 &&
               dot + 1 < email.size();
    }

    static bool validDate(const std::string& value) {
        if (value.size() != 10 ||
            value[4] != '-' ||
            value[7] != '-') {
            return false;
        }

        for (std::size_t i = 0; i < value.size(); ++i) {
            if (i == 4 || i == 7) continue;
            if (!std::isdigit(static_cast<unsigned char>(value[i]))) {
                return false;
            }
        }

        const int month = std::stoi(value.substr(5, 2));
        const int day = std::stoi(value.substr(8, 2));

        return month >= 1 && month <= 12 && day >= 1 && day <= 31;
    }

    void completeness(
        const Customer& customer,
        std::vector<Issue>& issues
    ) const {
        const auto addIfBlank =
            [&](const std::string& field, const std::string& value) {
                if (isBlank(value)) {
                    issues.push_back({
                        Dimension::Completeness,
                        field,
                        customer.id,
                        "Required value is missing."
                    });
                }
            };

        addIfBlank("id", customer.id);
        addIfBlank("name", customer.name);
        addIfBlank("email", customer.email);
        addIfBlank("country", customer.country);
        addIfBlank("currency", customer.currency);
        addIfBlank("status", customer.status);
        addIfBlank("signupDate", customer.signupDate);
    }

    void validity(
        const Customer& customer,
        std::vector<Issue>& issues
    ) const {
        if (!validCountries.contains(customer.country)) {
            issues.push_back({
                Dimension::Validity,
                "country",
                customer.id,
                "Country code is outside the accepted domain."
            });
        }

        if (!validStatuses.contains(customer.status)) {
            issues.push_back({
                Dimension::Validity,
                "status",
                customer.id,
                "Status is outside the accepted domain."
            });
        }

        if (!customer.email.empty() && !looksLikeEmail(customer.email)) {
            issues.push_back({
                Dimension::Validity,
                "email",
                customer.id,
                "Email does not satisfy the required structure."
            });
        }

        if (!validDate(customer.signupDate)) {
            issues.push_back({
                Dimension::Validity,
                "signupDate",
                customer.id,
                "Date must use YYYY-MM-DD and contain valid calendar components."
            });
        }

        if (customer.creditLimit < 0) {
            issues.push_back({
                Dimension::Validity,
                "creditLimit",
                customer.id,
                "Credit limit cannot be negative."
            });
        }
    }

    void consistency(
        const Customer& customer,
        std::vector<Issue>& issues
    ) const {
        const auto currencyIt = currencyByCountry.find(customer.country);

        if (currencyIt != currencyByCountry.end() &&
            currencyIt->second != customer.currency) {
            issues.push_back({
                Dimension::Consistency,
                "currency",
                customer.id,
                "Country and currency contradict the reference mapping."
            });
        }

        if (customer.status == "inactive" && customer.creditLimit > 0) {
            issues.push_back({
                Dimension::Consistency,
                "creditLimit",
                customer.id,
                "Inactive customer has a positive credit limit."
            });
        }

        if (std::any_of(
                customer.name.begin(),
                customer.name.end(),
                [](unsigned char c) { return std::isdigit(c); })) {
            issues.push_back({
                Dimension::Consistency,
                "name",
                customer.id,
                "Customer name contains numeric characters."
            });
        }
    }

    void accuracy(
        const Customer& customer,
        std::vector<Issue>& issues
    ) const {
        const auto it = verifiedCustomers.find(customer.id);

        if (it == verifiedCustomers.end()) {
            return;
        }

        const ReferenceCustomer& reference = it->second;

        if (customer.email != reference.email) {
            issues.push_back({
                Dimension::Accuracy,
                "email",
                customer.id,
                "Email differs from the independently verified value."
            });
        }

        if (customer.country != reference.country) {
            issues.push_back({
                Dimension::Accuracy,
                "country",
                customer.id,
                "Country differs from the independently verified value."
            });
        }

        if (customer.currency != reference.currency) {
            issues.push_back({
                Dimension::Accuracy,
                "currency",
                customer.id,
                "Currency differs from the independently verified value."
            });
        }
    }

    void crossRecordChecks(
        const std::vector<Customer>& customers,
        std::vector<Issue>& issues
    ) const {
        std::unordered_map<std::string, int> idCounts;
        std::unordered_map<std::string, std::vector<std::string>> emailOwners;

        for (const auto& customer : customers) {
            ++idCounts[customer.id];

            if (!customer.email.empty()) {
                emailOwners[customer.email].push_back(customer.id);
            }
        }

        for (const auto& [id, count] : idCounts) {
            if (count > 1) {
                issues.push_back({
                    Dimension::Consistency,
                    "id",
                    id,
                    "Customer identifier occurs more than once."
                });
            }
        }

        for (const auto& [email, owners] : emailOwners) {
            if (owners.size() > 1) {
                for (const auto& owner : owners) {
                    issues.push_back({
                        Dimension::Consistency,
                        "email",
                        owner,
                        "Email address is assigned to multiple records."
                    });
                }
            }
        }
    }

public:
    std::vector<Issue> validate(
        const std::vector<Customer>& customers
    ) const {
        std::vector<Issue> issues;

        for (const auto& customer : customers) {
            completeness(customer, issues);
            validity(customer, issues);
            consistency(customer, issues);
            accuracy(customer, issues);
        }

        crossRecordChecks(customers, issues);
        return issues;
    }

    std::map<Dimension, double> scores(
        const std::vector<Customer>& customers,
        const std::vector<Issue>& issues
    ) const {
        std::map<Dimension, std::set<std::string>> affected;

        for (const auto& issue : issues) {
            affected[issue.dimension].insert(issue.customerId);
        }

        std::map<Dimension, double> result;

        for (Dimension dimension : {
                 Dimension::Accuracy,
                 Dimension::Completeness,
                 Dimension::Consistency,
                 Dimension::Validity
             }) {
            if (customers.empty()) {
                result[dimension] = 100.0;
                continue;
            }

            const auto affectedCount = affected[dimension].size();

            result[dimension] =
                100.0 *
                static_cast<double>(customers.size() - affectedCount) /
                static_cast<double>(customers.size());
        }

        return result;
    }
};

void printReport(
    const std::vector<Customer>& customers,
    const std::vector<Issue>& issues,
    const std::map<Dimension, double>& scores
) {
    std::cout << "\nDATA QUALITY SCORECARD\n";
    std::cout << "=====================\n";

    for (const auto& [dimension, score] : scores) {
        std::cout << std::left
                  << std::setw(15)
                  << dimensionName(dimension)
                  << std::fixed
                  << std::setprecision(2)
                  << score
                  << "%\n";
    }

    std::set<std::string> invalidCustomers;

    for (const auto& issue : issues) {
        invalidCustomers.insert(issue.customerId);
    }

    std::cout << "\nRecords: " << customers.size() << '\n';
    std::cout << "Records with no detected issues: "
              << customers.size() - invalidCustomers.size()
              << '\n';

    std::cout << "\nQUALITY ISSUES\n";
    std::cout << "==============\n";

    for (const auto& issue : issues) {
        std::cout << '['
                  << dimensionName(issue.dimension)
                  << "] "
                  << issue.customerId
                  << '.'
                  << issue.field
                  << ": "
                  << issue.message
                  << '\n';
    }
}

int main() {
    try {
        const std::vector<Customer> customers{
            {
                "C1001",
                "Atul Pandey",
                "atul@example.com",
                "IN",
                "INR",
                "active",
                "2026-01-15",
                500000.0
            },
            {
                "C1002",
                "Maria Silva",
                "maria.changed@example.com",
                "DE",
                "EUR",
                "active",
                "2026-02-12",
                75000.0
            },
            {
                "C1003",
                "Ravi Kumar",
                "",
                "IN",
                "INR",
                "pending",
                "2026-03-10",
                25000.0
            },
            {
                "C1004",
                "Elena7",
                "elena@example",
                "XX",
                "USD",
                "unknown",
                "2027-04-01",
                -500.0
            },
            {
                "C1005",
                "John Smith",
                "john@example.com",
                "US",
                "EUR",
                "inactive",
                "2026-02-01",
                1000.0
            },
            {
                "C1006",
                "Duplicate User",
                "atul@example.com",
                "IN",
                "INR",
                "active",
                "2026-04-01",
                30000.0
            }
        };

        QualityEngine engine;

        const auto issues = engine.validate(customers);
        const auto scores = engine.scores(customers, issues);

        printReport(customers, issues, scores);

        const double overall =
            std::accumulate(
                scores.begin(),
                scores.end(),
                0.0,
                [](double total, const auto& entry) {
                    return total + entry.second;
                }
            ) / static_cast<double>(scores.size());

        std::cout << "\nOverall quality score: "
                  << std::fixed
                  << std::setprecision(2)
                  << overall
                  << "%\n";

        /*
         * The quality gate is intentionally separated from the scoring engine.
         * A business may tolerate a small number of issues in one dimension
         * while requiring validity to remain above a stricter threshold.
         */
        const bool validityGate =
            scores.at(Dimension::Validity) >= 90.0;

        if (!validityGate) {
            std::cout << "Validity quality gate: FAILED\n";
        } else {
            std::cout << "Validity quality gate: PASSED\n";
        }

        return validityGate ? 0 : 2;
    }
    catch (const std::exception& error) {
        std::cerr << "Quality processing failed: "
                  << error.what()
                  << '\n';
        return 1;
    }
}
