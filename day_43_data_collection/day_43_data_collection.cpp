#include <algorithm>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Repository-independent data collection governance case study:
 *
 * A retail organization collects internal inventory snapshots, external
 * supplier quotes, transactional order events, and behavioral events.
 *
 * This C++17 program models a validated ingestion and merge-like commit
 * decision for data: records are accepted only when their identity, source
 * category, timestamp, schema, and applicable permission rules are valid.
 * Monetary values use integer minor units instead of floating-point values.
 */

enum class DataCategory {
    Internal,
    External,
    Transactional,
    Behavioral
};

enum class CollectionStatus {
    Accepted,
    Duplicate,
    Rejected
};

std::string categoryName(DataCategory category) {
    switch (category) {
        case DataCategory::Internal:
            return "internal";
        case DataCategory::External:
            return "external";
        case DataCategory::Transactional:
            return "transactional";
        case DataCategory::Behavioral:
            return "behavioral";
    }
    throw std::logic_error("Unknown data category");
}

struct CollectionPolicy {
    std::string source;
    DataCategory category;
    std::string purpose;
    std::string lawfulBasis;
    bool requiresConsent = false;
};

struct CollectionRecord {
    std::string externalId;
    std::string source;
    DataCategory category;
    std::int64_t observedAtEpoch;
    std::int64_t collectedAtEpoch;
    std::string purpose;
    std::string lawfulBasis;
    std::map<std::string, std::string> fields;
};

struct IngestionResult {
    CollectionStatus status;
    std::string message;
    std::optional<CollectionRecord> record;
};

class ConsentRegistry {
private:
    std::set<std::pair<std::string, std::string>> permissions_;

public:
    void grant(const std::string& subject, const std::string& purpose) {
        if (subject.empty() || purpose.empty()) {
            throw std::invalid_argument("Subject and purpose are required");
        }
        permissions_.insert({subject, purpose});
    }

    void revoke(const std::string& subject, const std::string& purpose) {
        permissions_.erase({subject, purpose});
    }

    bool allows(
        const std::string& subject,
        const std::string& purpose
    ) const {
        return permissions_.count({subject, purpose}) != 0;
    }
};

class CollectionEngine {
private:
    ConsentRegistry& consent_;
    std::unordered_map<std::string, CollectionRecord> records_;
    std::vector<std::string> auditLog_;

    static std::string recordKey(
        const std::string& source,
        const std::string& externalId
    ) {
        return source + "\x1f" + externalId;
    }

    static void requireField(
        const CollectionRecord& record,
        const std::string& name
    ) {
        auto it = record.fields.find(name);
        if (it == record.fields.end() || it->second.empty()) {
            throw std::invalid_argument("Missing field: " + name);
        }
    }

    static long long parseNonNegativeInteger(
        const std::string& value,
        const std::string& field
    ) {
        if (value.empty()) {
            throw std::invalid_argument(field + " is empty");
        }

        std::size_t consumed = 0;
        long long parsed = 0;

        try {
            parsed = std::stoll(value, &consumed);
        } catch (const std::exception&) {
            throw std::invalid_argument(field + " is not an integer");
        }

        if (consumed != value.size() || parsed < 0) {
            throw std::invalid_argument(
                field + " must be a non-negative integer"
            );
        }

        return parsed;
    }

    static std::int64_t parseMoneyMinorUnits(
        const std::string& value
    ) {
        // Parse a decimal amount as integer minor units to avoid double
        // rounding in order reconciliation.
        if (value.empty()) {
            throw std::invalid_argument("Amount is empty");
        }

        const auto dot = value.find('.');
        const std::string whole = value.substr(0, dot);
        std::string fraction =
            dot == std::string::npos ? "" : value.substr(dot + 1);

        if (whole.empty() || fraction.size() > 2) {
            throw std::invalid_argument("Invalid monetary amount");
        }

        while (fraction.size() < 2) {
            fraction.push_back('0');
        }

        long long major = parseNonNegativeInteger(whole, "amount");

        long long minor = 0;
        if (!fraction.empty()) {
            minor = parseNonNegativeInteger(fraction, "fraction");
        }

        if (minor > 99 ||
            major > (INT64_MAX - minor) / 100) {
            throw std::invalid_argument("Amount exceeds supported range");
        }

        return static_cast<std::int64_t>(major * 100 + minor);
    }

    static void validate(const CollectionRecord& record) {
        if (record.externalId.empty() || record.source.empty()) {
            throw std::invalid_argument(
                "External ID and source are required"
            );
        }

        if (record.purpose.empty() || record.lawfulBasis.empty()) {
            throw std::invalid_argument(
                "Purpose and lawful basis are required"
            );
        }

        if (record.observedAtEpoch <= 0 ||
            record.collectedAtEpoch <= 0) {
            throw std::invalid_argument(
                "Timestamps must be positive epoch values"
            );
        }

        if (record.observedAtEpoch > record.collectedAtEpoch) {
            throw std::invalid_argument(
                "Observation cannot occur after collection"
            );
        }

        switch (record.category) {
            case DataCategory::Internal: {
                requireField(record, "warehouse");
                requireField(record, "sku");

                const auto available = parseNonNegativeInteger(
                    record.fields.at("availableUnits"),
                    "availableUnits"
                );
                const auto reserved = parseNonNegativeInteger(
                    record.fields.at("reservedUnits"),
                    "reservedUnits"
                );

                if (reserved > available) {
                    throw std::invalid_argument(
                        "Reserved inventory exceeds available inventory"
                    );
                }
                break;
            }

            case DataCategory::External: {
                requireField(record, "supplier");
                requireField(record, "sku");
                requireField(record, "currency");
                requireField(record, "unitPrice");

                if (record.fields.at("currency") != "INR" &&
                    record.fields.at("currency") != "USD" &&
                    record.fields.at("currency") != "EUR" &&
                    record.fields.at("currency") != "GBP") {
                    throw std::invalid_argument(
                        "Unsupported supplier currency"
                    );
                }

                parseMoneyMinorUnits(record.fields.at("unitPrice"));
                break;
            }

            case DataCategory::Transactional: {
                requireField(record, "orderId");
                requireField(record, "customerId");
                requireField(record, "currency");
                requireField(record, "status");

                parseMoneyMinorUnits(record.fields.at("amount"));

                const auto& status = record.fields.at("status");
                if (status != "pending" && status != "paid" &&
                    status != "refunded" && status != "cancelled") {
                    throw std::invalid_argument("Invalid order status");
                }
                break;
            }

            case DataCategory::Behavioral: {
                requireField(record, "visitorId");
                requireField(record, "eventType");
                requireField(record, "pagePath");

                const auto& path = record.fields.at("pagePath");
                if (path.empty() || path.front() != '/' ||
                    path.rfind("//", 0) == 0) {
                    throw std::invalid_argument(
                        "Behavioral page path must be relative"
                    );
                }

                const std::set<std::string> allowedEvents = {
                    "page_view",
                    "product_view",
                    "add_to_cart",
                    "search",
                    "checkout_started"
                };

                if (!allowedEvents.count(record.fields.at("eventType"))) {
                    throw std::invalid_argument(
                        "Unsupported behavioral event"
                    );
                }
                break;
            }
        }
    }

    static bool sameContent(
        const CollectionRecord& left,
        const CollectionRecord& right
    ) {
        return left.source == right.source &&
               left.category == right.category &&
               left.observedAtEpoch == right.observedAtEpoch &&
               left.purpose == right.purpose &&
               left.lawfulBasis == right.lawfulBasis &&
               left.fields == right.fields;
    }

public:
    explicit CollectionEngine(ConsentRegistry& consent)
        : consent_(consent) {}

    IngestionResult ingest(
        const CollectionPolicy& policy,
        const CollectionRecord& record
    ) {
        try {
            if (policy.source != record.source ||
                policy.category != record.category) {
                throw std::invalid_argument(
                    "Record does not match its registered source policy"
                );
            }

            if (policy.purpose != record.purpose ||
                policy.lawfulBasis != record.lawfulBasis) {
                throw std::invalid_argument(
                    "Purpose or collection basis conflicts with policy"
                );
            }

            if (policy.requiresConsent) {
                auto visitor = record.fields.find("visitorId");

                if (visitor == record.fields.end() ||
                    !consent_.allows(visitor->second, record.purpose)) {
                    throw std::invalid_argument(
                        "Purpose-specific permission is absent"
                    );
                }
            }

            validate(record);

            const std::string key = recordKey(
                record.source,
                record.externalId
            );
            auto existing = records_.find(key);

            if (existing != records_.end()) {
                if (sameContent(existing->second, record)) {
                    auditLog_.push_back(
                        "Duplicate ignored: " + categoryName(record.category)
                    );
                    return {
                        CollectionStatus::Duplicate,
                        "Identical source record already exists",
                        existing->second
                    };
                }

                throw std::invalid_argument(
                    "Conflicting duplicate requires source reconciliation"
                );
            }

            records_.emplace(key, record);
            auditLog_.push_back(
                "Accepted " + categoryName(record.category) +
                " record from " + record.source
            );

            return {
                CollectionStatus::Accepted,
                "Record validated and accepted",
                record
            };
        } catch (const std::exception& error) {
            auditLog_.push_back(
                "Rejected " + record.source + ": " + error.what()
            );

            return {
                CollectionStatus::Rejected,
                error.what(),
                std::nullopt
            };
        }
    }

    const auto& records() const {
        return records_;
    }

    const auto& auditLog() const {
        return auditLog_;
    }
};

struct RevenueReport {
    std::size_t paidOrders = 0;
    std::int64_t revenueMinorUnits = 0;
};

RevenueReport calculatePaidRevenue(
    const std::unordered_map<std::string, CollectionRecord>& records
) {
    RevenueReport report;

    for (const auto& entry : records) {
        const auto& record = entry.second;

        if (record.category != DataCategory::Transactional) {
            continue;
        }

        if (record.fields.at("status") != "paid" ||
            record.fields.at("currency") != "INR") {
            continue;
        }

        const auto amount = record.fields.at("amount");
        std::size_t dot = amount.find('.');
        std::string whole = amount.substr(0, dot);
        std::string fraction =
            dot == std::string::npos ? "" : amount.substr(dot + 1);

        while (fraction.size() < 2) {
            fraction.push_back('0');
        }

        const auto major = std::stoll(whole);
        const auto minor = std::stoll(fraction);

        report.revenueMinorUnits += major * 100 + minor;
        ++report.paidOrders;
    }

    return report;
}

std::string formatRupees(std::int64_t minorUnits) {
    std::ostringstream output;
    output << minorUnits / 100 << '.'
           << std::setw(2) << std::setfill('0')
           << minorUnits % 100;
    return output.str();
}

CollectionRecord makeRecord(
    const std::string& id,
    const std::string& source,
    DataCategory category,
    std::int64_t observed,
    std::int64_t collected,
    const std::string& purpose,
    const std::string& basis,
    std::map<std::string, std::string> fields
) {
    return {
        id,
        source,
        category,
        observed,
        collected,
        purpose,
        basis,
        std::move(fields)
    };
}

int main() {
    try {
        const std::int64_t now = 1791900000;

        ConsentRegistry consent;
        consent.grant("visitor-201", "product_experience_analytics");

        CollectionEngine engine(consent);

        const CollectionPolicy inventoryPolicy = {
            "erp_inventory",
            DataCategory::Internal,
            "inventory_reconciliation",
            "documented_business_purpose",
            false
        };

        const CollectionPolicy supplierPolicy = {
            "supplier_catalog_api",
            DataCategory::External,
            "supplier_price_comparison",
            "contract_and_documented_purpose",
            false
        };

        const CollectionPolicy orderPolicy = {
            "order_management",
            DataCategory::Transactional,
            "order_fulfillment",
            "contract_performance",
            false
        };

        const CollectionPolicy behaviorPolicy = {
            "web_analytics",
            DataCategory::Behavioral,
            "product_experience_analytics",
            "consent",
            true
        };

        auto inventory = makeRecord(
            "stock-2026-10-13",
            "erp_inventory",
            DataCategory::Internal,
            now - 60,
            now,
            "inventory_reconciliation",
            "documented_business_purpose",
            {
                {"warehouse", "DEL-01"},
                {"sku", "LAPTOP-14"},
                {"availableUnits", "184"},
                {"reservedUnits", "16"}
            }
        );

        auto supplier = makeRecord(
            "supplier-feed-8842",
            "supplier_catalog_api",
            DataCategory::External,
            now - 120,
            now,
            "supplier_price_comparison",
            "contract_and_documented_purpose",
            {
                {"supplier", "Northstar Components"},
                {"sku", "LAPTOP-14"},
                {"unitPrice", "64500.00"},
                {"currency", "INR"}
            }
        );

        auto order = makeRecord(
            "ORD-2026-1001",
            "order_management",
            DataCategory::Transactional,
            now - 30,
            now,
            "order_fulfillment",
            "contract_performance",
            {
                {"orderId", "ORD-2026-1001"},
                {"customerId", "CUS-0081"},
                {"amount", "72999.90"},
                {"currency", "INR"},
                {"status", "paid"}
            }
        );

        auto behavioral = makeRecord(
            "evt-5001",
            "web_analytics",
            DataCategory::Behavioral,
            now - 15,
            now,
            "product_experience_analytics",
            "consent",
            {
                {"visitorId", "visitor-201"},
                {"eventType", "checkout_started"},
                {"pagePath", "/checkout"}
            }
        );

        auto unauthorizedBehavior = makeRecord(
            "evt-5002",
            "web_analytics",
            DataCategory::Behavioral,
            now - 10,
            now,
            "product_experience_analytics",
            "consent",
            {
                {"visitorId", "visitor-202"},
                {"eventType", "page_view"},
                {"pagePath", "/home"}
            }
        );

        const std::vector<std::pair<CollectionPolicy, CollectionRecord>>
            examples = {
                {inventoryPolicy, inventory},
                {supplierPolicy, supplier},
                {orderPolicy, order},
                {behaviorPolicy, behavioral},
                {behaviorPolicy, unauthorizedBehavior}
            };

        for (const auto& example : examples) {
            auto result = engine.ingest(example.first, example.second);
            std::cout << categoryName(example.second.category)
                      << ": " << result.message << '\n';
        }

        // Re-ingestion with identical content does not create another row.
        auto duplicate = engine.ingest(inventoryPolicy, inventory);
        std::cout << "Duplicate test: " << duplicate.message << '\n';

        // A conflicting record with the same source key is rejected.
        auto conflictingInventory = inventory;
        conflictingInventory.fields["availableUnits"] = "190";

        auto conflict = engine.ingest(
            inventoryPolicy,
            conflictingInventory
        );
        std::cout << "Conflict test: " << conflict.message << '\n';

        const auto report = calculatePaidRevenue(engine.records());

        std::cout << "\nAccepted records: "
                  << engine.records().size() << '\n';
        std::cout << "Paid INR orders: "
                  << report.paidOrders << '\n';
        std::cout << "Paid INR revenue: Rs "
                  << formatRupees(report.revenueMinorUnits) << '\n';

        std::cout << "\nCollection audit log\n";
        for (const auto& entry : engine.auditLog()) {
            std::cout << "- " << entry << '\n';
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }
}
