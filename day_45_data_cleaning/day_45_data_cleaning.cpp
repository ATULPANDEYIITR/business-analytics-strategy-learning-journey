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
#include <unordered_set>
#include <vector>

/*
 * Repository-scale data quality case study:
 *
 * A customer transaction import arrives from several operational systems.
 * The governance engine must distinguish:
 *
 * - missing values: information is absent or represented by a missing token
 * - duplicates: the same business record appears more than once
 * - inconsistent data: the same logical value is represented differently
 *
 * The program deliberately keeps these concerns separate. Normalization is
 * performed before duplicate detection because "Lucknow" and "lucknow" can
 * otherwise prevent reliable duplicate identification.
 */

struct Transaction {
    std::string customerId;
    std::string name;
    std::optional<std::string> email;
    std::optional<std::string> phone;
    std::string city;
    std::optional<double> amount;
    std::string currency;
    std::string status;
    std::optional<std::string> signupDate;
};

struct AuditEvent {
    std::string customerId;
    std::string field;
    std::string category;
    std::string action;
    std::string detail;
};

class DataQualityEngine {
private:
    std::vector<AuditEvent> audit;

    static std::string trim(const std::string& value) {
        const auto first = value.find_first_not_of(" \t\r\n");
        if (first == std::string::npos) {
            return "";
        }

        const auto last = value.find_last_not_of(" \t\r\n");
        return value.substr(first, last - first + 1);
    }

    static std::string lower(std::string value) {
        for (char& c : value) {
            c = static_cast<char>(
                std::tolower(static_cast<unsigned char>(c))
            );
        }
        return value;
    }

    static bool isMissingToken(const std::string& value) {
        const std::string token = lower(trim(value));

        static const std::unordered_set<std::string> missing = {
            "", "na", "n/a", "null", "none", "unknown", "-", "--"
        };

        return missing.contains(token);
    }

    static std::string canonicalCity(const std::string& value) {
        const std::string token = lower(trim(value));

        if (token == "lucknow" || token == "lko") {
            return "Lucknow";
        }

        if (token == "kanpur" || token == "knp") {
            return "Kanpur";
        }

        return trim(value);
    }

    static std::string canonicalStatus(const std::string& value) {
        const std::string token = lower(trim(value));

        if (token == "active" || token == "act") {
            return "active";
        }

        if (token == "pending" || token == "pend") {
            return "pending";
        }

        if (token == "inactive" || token == "in-active") {
            return "inactive";
        }

        return token;
    }

    static std::string canonicalCurrency(const std::string& value) {
        std::string token = lower(trim(value));

        if (token == "rs" || token == "rs." ||
            token == "₹" || token == "rupee" || token == "rupees") {
            return "INR";
        }

        std::transform(
            token.begin(),
            token.end(),
            token.begin(),
            [](unsigned char c) {
                return static_cast<char>(std::toupper(c));
            }
        );

        return token;
    }

    static std::optional<double> parseAmount(
        const std::optional<std::string>& source
    ) {
        if (!source.has_value() || isMissingToken(*source)) {
            return std::nullopt;
        }

        std::string value = trim(*source);

        value.erase(
            std::remove(value.begin(), value.end(), ','),
            value.end()
        );

        const std::string lowerValue = lower(value);

        if (lowerValue.rfind("rs.", 0) == 0) {
            value = value.substr(3);
        } else if (lowerValue.rfind("rs", 0) == 0) {
            value = value.substr(2);
        } else if (lowerValue.rfind("inr", 0) == 0) {
            value = value.substr(3);
        }

        try {
            size_t consumed = 0;
            const double amount = std::stod(value, &consumed);

            if (consumed != value.size()) {
                return std::nullopt;
            }

            if (amount < 0) {
                throw std::invalid_argument(
                    "negative transaction amount"
                );
            }

            return amount;
        } catch (const std::invalid_argument&) {
            return std::nullopt;
        } catch (const std::out_of_range&) {
            return std::nullopt;
        }
    }

    static std::string normalizePhone(
        const std::optional<std::string>& source
    ) {
        if (!source.has_value()) {
            return "";
        }

        std::string digits;

        for (char c : *source) {
            if (std::isdigit(static_cast<unsigned char>(c))) {
                digits += c;
            }
        }

        if (digits.empty()) {
            return "";
        }

        if (digits.size() == 12 && digits.rfind("91", 0) == 0) {
            return "+91 " + digits.substr(2, 5) + " " + digits.substr(7);
        }

        if (digits.size() == 10) {
            return "+91 " + digits.substr(0, 5) + " " + digits.substr(5);
        }

        return "+" + digits;
    }

    static std::string makeBusinessKey(const Transaction& t) {
        std::ostringstream out;

        out << t.customerId << '|'
            << t.name << '|'
            << t.email.value_or("<NULL>") << '|'
            << t.phone.value_or("<NULL>") << '|'
            << t.city << '|';

        if (t.amount.has_value()) {
            out << std::fixed << std::setprecision(2) << *t.amount;
        } else {
            out << "<NULL>";
        }

        out << '|'
            << t.currency << '|'
            << t.status << '|'
            << t.signupDate.value_or("<NULL>");

        return out.str();
    }

    void addAudit(
        const Transaction& transaction,
        const std::string& field,
        const std::string& category,
        const std::string& action,
        const std::string& detail
    ) {
        audit.push_back({
            transaction.customerId,
            field,
            category,
            action,
            detail
        });
    }

public:
    std::vector<Transaction> normalize(
        const std::vector<Transaction>& source
    ) {
        std::vector<Transaction> result;

        for (const auto& sourceRecord : source) {
            Transaction current = sourceRecord;

            if (current.email.has_value() &&
                isMissingToken(*current.email)) {
                addAudit(
                    current,
                    "email",
                    "missing",
                    "standardized",
                    "Missing token converted to null"
                );
                current.email = std::nullopt;
            }

            if (current.phone.has_value() &&
                isMissingToken(*current.phone)) {
                addAudit(
                    current,
                    "phone",
                    "missing",
                    "standardized",
                    "Missing token converted to null"
                );
                current.phone = std::nullopt;
            }

            if (current.amount.has_value()) {
                const auto original = *current.amount;
                if (original < 0) {
                    addAudit(
                        current,
                        "amount",
                        "invalid",
                        "rejected",
                        "Negative amount"
                    );
                    current.amount = std::nullopt;
                }
            }

            const std::string originalCity = current.city;
            current.city = canonicalCity(current.city);

            if (originalCity != current.city) {
                addAudit(
                    current,
                    "city",
                    "inconsistent",
                    "normalized",
                    originalCity + " -> " + current.city
                );
            }

            const std::string originalStatus = current.status;
            current.status = canonicalStatus(current.status);

            if (originalStatus != current.status) {
                addAudit(
                    current,
                    "status",
                    "inconsistent",
                    "normalized",
                    originalStatus + " -> " + current.status
                );
            }

            const std::string originalCurrency = current.currency;
            current.currency = canonicalCurrency(current.currency);

            if (originalCurrency != current.currency) {
                addAudit(
                    current,
                    "currency",
                    "inconsistent",
                    "normalized",
                    originalCurrency + " -> " + current.currency
                );
            }

            const std::string originalPhone =
                current.phone.value_or("");

            const std::string normalizedPhone =
                normalizePhone(current.phone);

            if (!normalizedPhone.empty()) {
                current.phone = normalizedPhone;

                if (originalPhone != normalizedPhone) {
                    addAudit(
                        current,
                        "phone",
                        "inconsistent",
                        "normalized",
                        originalPhone + " -> " + normalizedPhone
                    );
                }
            }

            result.push_back(current);
        }

        return result;
    }

    std::vector<Transaction> removeDuplicates(
        const std::vector<Transaction>& records
    ) {
        std::unordered_set<std::string> seen;
        std::vector<Transaction> unique;

        for (const auto& record : records) {
            const std::string key = makeBusinessKey(record);

            if (seen.contains(key)) {
                addAudit(
                    record,
                    "__record__",
                    "duplicate",
                    "removed",
                    "Normalized business key already exists"
                );
                continue;
            }

            seen.insert(key);
            unique.push_back(record);
        }

        return unique;
    }

    void imputeMissingAmounts(
        std::vector<Transaction>& records
    ) {
        std::map<std::string, std::vector<double>> valuesByCity;

        for (const auto& record : records) {
            if (record.amount.has_value()) {
                valuesByCity[record.city].push_back(*record.amount);
            }
        }

        std::map<std::string, double> medians;

        for (auto& [city, values] : valuesByCity) {
            std::sort(values.begin(), values.end());

            const size_t middle = values.size() / 2;

            if (values.size() % 2 == 1) {
                medians[city] = values[middle];
            } else {
                medians[city] =
                    (values[middle - 1] + values[middle]) / 2.0;
            }
        }

        for (auto& record : records) {
            if (!record.amount.has_value() &&
                medians.contains(record.city)) {
                record.amount = medians[record.city];

                addAudit(
                    record,
                    "amount",
                    "missing",
                    "imputed",
                    "City-level median applied"
                );
            }
        }
    }

    std::vector<std::string> validate(
        const Transaction& record
    ) const {
        std::vector<std::string> errors;

        if (record.customerId.empty()) {
            errors.push_back("customerId is required");
        }

        if (record.name.empty()) {
            errors.push_back("name is required");
        }

        if (record.amount.has_value() && *record.amount < 0) {
            errors.push_back("amount cannot be negative");
        }

        static const std::set<std::string> currencies = {
            "INR", "USD", "EUR", "GBP"
        };

        if (!currencies.contains(record.currency)) {
            errors.push_back("unsupported currency");
        }

        static const std::set<std::string> statuses = {
            "active", "pending", "inactive"
        };

        if (!statuses.contains(record.status)) {
            errors.push_back("unsupported status");
        }

        return errors;
    }

    const std::vector<AuditEvent>& auditEvents() const {
        return audit;
    }
};

void printRecord(const Transaction& t) {
    std::cout
        << t.customerId << " | "
        << t.name << " | "
        << t.email.value_or("<missing>") << " | "
        << t.phone.value_or("<missing>") << " | "
        << t.city << " | ";

    if (t.amount.has_value()) {
        std::cout << std::fixed
                  << std::setprecision(2)
                  << *t.amount;
    } else {
        std::cout << "<missing>";
    }

    std::cout << " | "
              << t.currency
              << " | "
              << t.status
              << '\n';
}

int main() {
    std::vector<Transaction> source = {
        {
            "C001", "Asha Sharma",
            "ASHA@EXAMPLE.COM",
            "+91 98765 43210",
            "Lucknow",
            1250.0,
            "INR",
            "active",
            "2026-01-05"
        },
        {
            "C002", "Rahul Verma",
            "rahul@example.com",
            "9876543211",
            "Lucknow",
            850.0,
            "inr",
            "Active",
            "2026-01-05"
        },
        {
            "C003", "Meera Singh",
            std::nullopt,
            "+91-91234-56789",
            "Kanpur",
            std::nullopt,
            "INR",
            "ACTIVE",
            "2026-01-08"
        },
        {
            "C004", "Arun Kumar",
            "arun@example.com",
            std::nullopt,
            "Kanpur",
            450.0,
            "INR",
            "active",
            "2026-01-09"
        },
        {
            "C005", "Neha Gupta",
            "neha@example.com",
            "+91 90000 11111",
            "Lucknow",
            1250.0,
            "INR",
            "Active",
            "2026-01-10"
        },
        {
            "C005", "Neha Gupta",
            "neha@example.com",
            "+91 90000 11111",
            "Lucknow",
            1250.0,
            "INR",
            "Active",
            "2026-01-10"
        },
        {
            "C006", "Ravi Patel",
            "ravi@example.com",
            "+91-98888-22222",
            "lucknow",
            850.0,
            "INR",
            "active",
            "2026-01-11"
        },
        {
            "C007", "Sonia Rao",
            "sonia@example.com",
            "+91 97777 33333",
            "Kanpur",
            std::nullopt,
            "INR",
            "pending",
            "2026-01-12"
        },
        {
            "C008", "Vikram Das",
            "vIKRAM@EXAMPLE.COM",
            "+91 96666 44444",
            "Kanpur",
            1250.0,
            "INR",
            "active",
            "2026-01-13"
        },
        {
            "C009", "Pooja Nair",
            "pooja@example.com",
            "+91 95555 55555",
            "Lucknow",
            1250.0,
            "Rs.",
            "active",
            "2026-01-14"
        }
    };

    DataQualityEngine engine;

    std::cout << "DATA QUALITY CASE STUDY\n";
    std::cout << "======================\n\n";

    auto normalized = engine.normalize(source);
    engine.imputeMissingAmounts(normalized);
    auto unique = engine.removeDuplicates(normalized);

    std::cout << "CLEANED TRANSACTIONS\n";
    std::cout << "====================\n";

    for (const auto& record : unique) {
        printRecord(record);
    }

    std::cout << "\nVALIDATION\n";
    std::cout << "==========\n";

    for (const auto& record : unique) {
        const auto errors = engine.validate(record);

        if (errors.empty()) {
            std::cout << record.customerId << ": valid\n";
        } else {
            std::cout << record.customerId << ": invalid\n";
            for (const auto& error : errors) {
                std::cout << "  " << error << '\n';
            }
        }
    }

    std::cout << "\nAUDIT TRAIL\n";
    std::cout << "===========\n";

    for (const auto& event : engine.auditEvents()) {
        std::cout
            << event.customerId << " | "
            << event.field << " | "
            << event.category << " | "
            << event.action << " | "
            << event.detail << '\n';
    }

    /*
     * The dominant cost of duplicate detection is expected O(n) average
     * because unordered_set provides average constant-time lookup.
     * Sorting-based approaches can provide deterministic ordering but
     * increase the main duplicate-detection cost to O(n log n).
     *
     * The normalization pass is O(n * f), where f is the number of fields.
     * Median calculation costs O(n log n) in the worst case because each
     * city's amount list is sorted independently.
     */
    return 0;
}
