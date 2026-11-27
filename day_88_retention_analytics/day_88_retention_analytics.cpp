#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

/*
 * RETENTION ANALYTICS ENGINE
 *
 * C++17 implementation of a customer retention platform.
 *
 * Core capabilities:
 * - Customer domain modeling
 * - Event ingestion and deduplication
 * - Purchase history management
 * - Churn risk assessment
 * - RFM segmentation
 * - Loyalty tier determination
 * - Campaign eligibility
 * - Campaign ROI
 * - Cohort retention
 * - Customer lifetime value
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic retention.cpp -o retention
 */

namespace retention {

// ============================================================
// 1. DOMAIN ENUMERATIONS
// ============================================================

enum class CustomerStatus {
    Active,
    AtRisk,
    Churned,
    Reactivated
};

enum class EventType {
    Purchase,
    Login,
    Support,
    EmailOpen,
    EmailClick,
    Subscription,
    Refund
};

enum class LoyaltyTier {
    Bronze,
    Silver,
    Gold,
    Platinum
};

enum class RiskLevel {
    Low,
    Medium,
    High
};


// ============================================================
// 2. DOMAIN EXCEPTIONS
// ============================================================

class DomainError : public std::runtime_error {
public:
    explicit DomainError(const std::string& message)
        : std::runtime_error(message) {}
};


// ============================================================
// 3. DOMAIN MODELS
// ============================================================

struct Customer {
    std::string id;
    std::string name;
    std::string email;
    std::string acquisitionMonth;
    int acquisitionDay;
    std::string region;
    double monthlyRevenue;

    CustomerStatus status = CustomerStatus::Active;
    LoyaltyTier tier = LoyaltyTier::Bronze;
    int loyaltyPoints = 0;
};

struct CustomerEvent {
    std::string id;
    std::string customerId;
    EventType type;
    int daysAgo;
    double amount;
};

struct RFMResult {
    int recency;
    int frequency;
    double monetary;
    double score;
    std::string segment;
};

struct ChurnResult {
    std::string customerId;
    double probability;
    RiskLevel level;
    std::vector<std::string> factors;
};

struct Campaign {
    std::string id;
    std::string name;
    double budget;
    double contactCost;
    CustomerStatus targetStatus;

    std::set<std::string> assigned;
    std::set<std::string> converted;
};


// ============================================================
// 4. ENUMERATION CONVERSION
// ============================================================

std::string toString(CustomerStatus status) {
    switch (status) {
        case CustomerStatus::Active: return "ACTIVE";
        case CustomerStatus::AtRisk: return "AT_RISK";
        case CustomerStatus::Churned: return "CHURNED";
        case CustomerStatus::Reactivated: return "REACTIVATED";
    }

    throw DomainError("Unknown customer status.");
}

std::string toString(LoyaltyTier tier) {
    switch (tier) {
        case LoyaltyTier::Bronze: return "BRONZE";
        case LoyaltyTier::Silver: return "SILVER";
        case LoyaltyTier::Gold: return "GOLD";
        case LoyaltyTier::Platinum: return "PLATINUM";
    }

    throw DomainError("Unknown loyalty tier.");
}

std::string toString(RiskLevel level) {
    switch (level) {
        case RiskLevel::Low: return "LOW";
        case RiskLevel::Medium: return "MEDIUM";
        case RiskLevel::High: return "HIGH";
    }

    throw DomainError("Unknown risk level.");
}


// ============================================================
// 5. VALIDATION
// ============================================================

void validateCustomer(const Customer& customer) {

    if (customer.id.empty()) {
        throw DomainError("Customer ID is required.");
    }

    if (customer.name.empty()) {
        throw DomainError("Customer name is required.");
    }

    if (customer.email.find('@') == std::string::npos) {
        throw DomainError("Invalid email address.");
    }

    if (customer.monthlyRevenue < 0 ||
        !std::isfinite(customer.monthlyRevenue)) {
        throw DomainError("Invalid monthly revenue.");
    }

    if (customer.acquisitionDay < 1 ||
        customer.acquisitionDay > 31) {
        throw DomainError("Invalid acquisition day.");
    }
}

void validateEvent(const CustomerEvent& event) {

    if (event.id.empty() || event.customerId.empty()) {
        throw DomainError("Event identifiers are required.");
    }

    if (event.daysAgo < 0) {
        throw DomainError("Event cannot be in the future.");
    }

    if (event.amount < 0 || !std::isfinite(event.amount)) {
        throw DomainError("Invalid event amount.");
    }

    if (event.type != EventType::Purchase &&
        event.type != EventType::Subscription &&
        event.amount != 0) {
        throw DomainError(
            "Monetary amount not supported by event type."
        );
    }
}


// ============================================================
// 6. CUSTOMER STATE MANAGEMENT
// ============================================================

class CustomerRepository {

private:
    std::unordered_map<std::string, Customer> customers;
    std::unordered_map<std::string, std::string> emailIndex;

public:

    void add(const Customer& customer) {

        validateCustomer(customer);

        if (customers.count(customer.id)) {
            throw DomainError("Duplicate customer ID.");
        }

        if (emailIndex.count(customer.email)) {
            throw DomainError("Duplicate customer email.");
        }

        customers.emplace(customer.id, customer);
        emailIndex.emplace(customer.email, customer.id);
    }

    Customer& get(const std::string& id) {

        auto iterator = customers.find(id);

        if (iterator == customers.end()) {
            throw DomainError("Customer not found: " + id);
        }

        return iterator->second;
    }

    const Customer& get(const std::string& id) const {

        auto iterator = customers.find(id);

        if (iterator == customers.end()) {
            throw DomainError("Customer not found: " + id);
        }

        return iterator->second;
    }

    std::vector<Customer*> all() {

        std::vector<Customer*> result;

        for (auto& entry : customers) {
            result.push_back(&entry.second);
        }

        return result;
    }

    std::size_t size() const {
        return customers.size();
    }
};


// ============================================================
// 7. EVENT REPOSITORY
// ============================================================

class EventRepository {

private:
    std::unordered_map<std::string, CustomerEvent> events;

    std::unordered_map<
        std::string,
        std::vector<CustomerEvent>
    > customerEvents;

public:

    void record(
        const CustomerEvent& event,
        const CustomerRepository& customers
    ) {

        validateEvent(event);

        customers.get(event.customerId);

        if (events.count(event.id)) {
            throw DomainError("Duplicate event ID.");
        }

        events.emplace(event.id, event);
        customerEvents[event.customerId].push_back(event);
    }

    std::vector<CustomerEvent> forCustomer(
        const std::string& customerId
    ) const {

        auto iterator = customerEvents.find(customerId);

        if (iterator == customerEvents.end()) {
            return {};
        }

        auto result = iterator->second;

        std::sort(
            result.begin(),
            result.end(),
            [](const CustomerEvent& a, const CustomerEvent& b) {
                return a.daysAgo > b.daysAgo;
            }
        );

        return result;
    }

    std::vector<CustomerEvent> all() const {

        std::vector<CustomerEvent> result;

        result.reserve(events.size());

        for (const auto& entry : events) {
            result.push_back(entry.second);
        }

        return result;
    }
};


// ============================================================
// 8. RFM ANALYTICS
// ============================================================

class RFMAnalyzer {

public:

    static RFMResult evaluate(
        const Customer& customer,
        const std::vector<CustomerEvent>& events
    ) {

        int recency = 0;
        int frequency = 0;
        double monetary = 0;

        bool foundPurchase = false;

        for (const auto& event : events) {

            if (event.type != EventType::Purchase) {
                continue;
            }

            frequency++;
            monetary += event.amount;

            if (!foundPurchase || event.daysAgo < recency) {
                recency = event.daysAgo;
                foundPurchase = true;
            }
        }

        if (!foundPurchase) {
            recency = 365;
        }

        double recencyScore =
            std::max(0.0, 1.0 - std::min(recency, 180) / 180.0);

        double frequencyScore =
            std::min(frequency / 12.0, 1.0);

        double monetaryScore =
            std::min(monetary / 12000.0, 1.0);

        double score = (
            recencyScore * 0.40 +
            frequencyScore * 0.30 +
            monetaryScore * 0.30
        ) * 100;

        std::string segment;

        if (frequency == 0) {
            segment = "NON_PURCHASING";
        } else if (recency <= 30 && score >= 65) {
            segment = "CHAMPIONS";
        } else if (recency <= 60) {
            segment = "LOYAL";
        } else if (recency <= 90) {
            segment = "AT_RISK";
        } else {
            segment = "HIBERNATING";
        }

        return {
            recency,
            frequency,
            monetary,
            score,
            segment
        };
    }
};


// ============================================================
// 9. CHURN RISK ENGINE
// ============================================================

class ChurnEngine {

private:
    double mediumThreshold;
    double highThreshold;

public:

    ChurnEngine(
        double medium = 0.35,
        double high = 0.60
    )
        : mediumThreshold(medium),
          highThreshold(high) {

        if (medium < 0 || high > 1 || medium >= high) {
            throw DomainError("Invalid risk thresholds.");
        }
    }

    ChurnResult evaluate(
        const Customer& customer,
        const std::vector<CustomerEvent>& events
    ) const {

        int purchaseInactivity = 365;
        int generalInactivity = 365;
        int purchaseCount = 0;
        int recentSupport = 0;

        bool hasPurchase = false;
        bool hasActivity = false;

        for (const auto& event : events) {

            if (!hasActivity || event.daysAgo < generalInactivity) {
                generalInactivity = event.daysAgo;
                hasActivity = true;
            }

            if (event.type == EventType::Purchase) {
                purchaseCount++;

                if (!hasPurchase ||
                    event.daysAgo < purchaseInactivity) {

                    purchaseInactivity = event.daysAgo;
                    hasPurchase = true;
                }
            }

            if (event.type == EventType::Support &&
                event.daysAgo <= 30) {
                recentSupport++;
            }
        }

        double risk = 0.05;
        std::vector<std::string> factors;

        if (purchaseInactivity > 30) {
            risk += 0.20;
            factors.push_back("Purchase inactivity above 30 days");
        }

        if (purchaseInactivity > 60) {
            risk += 0.20;
            factors.push_back("Purchase inactivity above 60 days");
        }

        if (purchaseInactivity > 90) {
            risk += 0.20;
            factors.push_back("Purchase inactivity above 90 days");
        }

        if (generalInactivity > 45) {
            risk += 0.15;
            factors.push_back("Low engagement");
        }

        if (purchaseCount == 0) {
            risk += 0.15;
            factors.push_back("No purchase history");
        }

        if (recentSupport >= 3) {
            risk += 0.10;
            factors.push_back("Repeated support interactions");
        }

        risk = std::min(risk, 0.99);

        RiskLevel level =
            risk >= highThreshold
                ? RiskLevel::High
                : risk >= mediumThreshold
                    ? RiskLevel::Medium
                    : RiskLevel::Low;

        return {
            customer.id,
            risk,
            level,
            factors
        };
    }
};


// ============================================================
// 10. LOYALTY ENGINE
// ============================================================

class LoyaltyEngine {

public:

    static LoyaltyTier determineTier(double spend) {

        if (spend >= 10000) return LoyaltyTier::Platinum;
        if (spend >= 5000) return LoyaltyTier::Gold;
        if (spend >= 2000) return LoyaltyTier::Silver;

        return LoyaltyTier::Bronze;
    }

    static double multiplier(LoyaltyTier tier) {

        switch (tier) {
            case LoyaltyTier::Bronze: return 1.0;
            case LoyaltyTier::Silver: return 1.25;
            case LoyaltyTier::Gold: return 1.5;
            case LoyaltyTier::Platinum: return 2.0;
        }

        throw DomainError("Unknown loyalty tier.");
    }

    static LoyaltyTier update(
        Customer& customer,
        const std::vector<CustomerEvent>& events
    ) {

        double spend = 0;

        for (const auto& event : events) {
            if (event.type == EventType::Purchase) {
                spend += event.amount;
            }
        }

        customer.tier = determineTier(spend);

        return customer.tier;
    }
};


// ============================================================
// 11. CAMPAIGN GOVERNANCE
// ============================================================

class CampaignEngine {

private:
    std::unordered_map<std::string, Campaign> campaigns;

public:

    void create(const Campaign& campaign) {

        if (campaign.id.empty() || campaign.budget < 0 ||
            campaign.contactCost < 0) {
            throw DomainError("Invalid campaign configuration.");
        }

        if (campaigns.count(campaign.id)) {
            throw DomainError("Duplicate campaign ID.");
        }

        campaigns.emplace(campaign.id, campaign);
    }

    void assign(
        const std::string& campaignId,
        const Customer& customer
    ) {

        auto iterator = campaigns.find(campaignId);

        if (iterator == campaigns.end()) {
            throw DomainError("Campaign not found.");
        }

        Campaign& campaign = iterator->second;

        if (customer.status != campaign.targetStatus) {
            throw DomainError("Customer is not eligible.");
        }

        if (campaign.assigned.count(customer.id)) {
            throw DomainError("Duplicate assignment.");
        }

        double projectedCost =
            (campaign.assigned.size() + 1)
            * campaign.contactCost;

        if (projectedCost > campaign.budget) {
            throw DomainError("Campaign budget exceeded.");
        }

        campaign.assigned.insert(customer.id);
    }

    void convert(
        const std::string& campaignId,
        const std::string& customerId
    ) {

        auto iterator = campaigns.find(campaignId);

        if (iterator == campaigns.end()) {
            throw DomainError("Campaign not found.");
        }

        Campaign& campaign = iterator->second;

        if (!campaign.assigned.count(customerId)) {
            throw DomainError("Customer not assigned.");
        }

        campaign.converted.insert(customerId);
    }

    void report(
        const std::string& campaignId,
        double revenuePerConversion
    ) const {

        auto iterator = campaigns.find(campaignId);

        if (iterator == campaigns.end()) {
            throw DomainError("Campaign not found.");
        }

        if (revenuePerConversion < 0) {
            throw DomainError("Revenue cannot be negative.");
        }

        const Campaign& campaign = iterator->second;

        double cost =
            campaign.assigned.size() * campaign.contactCost;

        double revenue =
            campaign.converted.size() * revenuePerConversion;

        double conversionRate =
            campaign.assigned.empty()
                ? 0
                : static_cast<double>(
                    campaign.converted.size()
                ) / campaign.assigned.size() * 100;

        double roi =
            cost > 0
                ? (revenue - cost) / cost * 100
                : 0;

        std::cout << "\nCAMPAIGN PERFORMANCE\n";
        std::cout << "Campaign: " << campaign.name << '\n';
        std::cout << "Assigned: " << campaign.assigned.size() << '\n';
        std::cout << "Converted: " << campaign.converted.size() << '\n';
        std::cout << "Conversion rate: "
                  << conversionRate << "%\n";
        std::cout << "Campaign cost: " << cost << '\n';
        std::cout << "Revenue: " << revenue << '\n';
        std::cout << "ROI: " << roi << "%\n";
    }
};


// ============================================================
// 12. COHORT RETENTION ENGINE
// ============================================================

class CohortEngine {

public:

    static int monthDifference(
        int startMonth,
        int endMonth
    ) {
        return endMonth - startMonth;
    }

    static void calculate(
        const std::vector<Customer>& customers,
        const std::vector<CustomerEvent>& events
    ) {

        std::map<std::string, std::set<std::string>> cohorts;

        std::map<
            std::pair<std::string, int>,
            std::set<std::string>
        > active;

        std::unordered_map<std::string, const Customer*> index;

        for (const auto& customer : customers) {

            cohorts[customer.acquisitionMonth].insert(
                customer.id
            );

            index[customer.id] = &customer;
        }

        for (const auto& event : events) {

            if (event.type != EventType::Purchase &&
                event.type != EventType::Login) {
                continue;
            }

            auto iterator = index.find(event.customerId);

            if (iterator == index.end()) {
                continue;
            }

            const Customer& customer = *iterator->second;

            int cohortMonth = std::stoi(
                customer.acquisitionMonth.substr(5, 2)
            );

            int eventMonth = cohortMonth + event.daysAgo / 30;

            int period = monthDifference(
                cohortMonth,
                eventMonth
            );

            if (period >= 0) {
                active[
                    {customer.acquisitionMonth, period}
                ].insert(customer.id);
            }
        }

        std::cout << "\nCOHORT RETENTION\n";
        std::cout << "--------------------------------------\n";

        for (const auto& cohort : cohorts) {

            const auto& members = cohort.second;

            std::cout << cohort.first
                      << " | Size: " << members.size();

            for (const auto& period : active) {

                if (period.first.first != cohort.first) {
                    continue;
                }

                double retention =
                    static_cast<double>(period.second.size())
                    / members.size() * 100;

                std::cout << " | M"
                          << period.first.second
                          << ": "
                          << std::fixed
                          << std::setprecision(2)
                          << retention << "%";
            }

            std::cout << '\n';
        }
    }
};


// ============================================================
// 13. CUSTOMER LIFETIME VALUE
// ============================================================

double calculateCLV(
    double monthlyRevenue,
    double grossMargin,
    double monthlyChurn
) {

    if (monthlyRevenue < 0 ||
        grossMargin < 0 ||
        grossMargin > 1 ||
        monthlyChurn <= 0 ||
        monthlyChurn > 1) {

        throw DomainError("Invalid CLV inputs.");
    }

    return monthlyRevenue * grossMargin / monthlyChurn;
}


// ============================================================
// 14. RETENTION ANALYTICS SERVICE
// ============================================================

class RetentionService {

private:
    CustomerRepository customers;
    EventRepository events;
    ChurnEngine churnEngine;

public:

    RetentionService()
        : churnEngine(0.35, 0.60) {}

    CustomerRepository& customerRepository() {
        return customers;
    }

    void addCustomer(const Customer& customer) {
        customers.add(customer);
    }

    void recordEvent(const CustomerEvent& event) {
        events.record(event, customers);
    }

    void analyze() {

        std::cout << "\nCUSTOMER RETENTION REPORT\n";
        std::cout << "======================================\n";

        int highRisk = 0;
        int mediumRisk = 0;
        int lowRisk = 0;

        for (Customer* customer : customers.all()) {

            const auto history =
                events.forCustomer(customer->id);

            const auto rfm = RFMAnalyzer::evaluate(
                *customer,
                history
            );

            const auto churn = churnEngine.evaluate(
                *customer,
                history
            );

            LoyaltyEngine::update(
                *customer,
                history
            );

            if (churn.level == RiskLevel::High) {
                highRisk++;

                if (customer->status == CustomerStatus::Active) {
                    customer->status = CustomerStatus::AtRisk;
                }
            } else if (churn.level == RiskLevel::Medium) {
                mediumRisk++;
            } else {
                lowRisk++;

                if (customer->status == CustomerStatus::AtRisk) {
                    customer->status = CustomerStatus::Active;
                }
            }

            std::cout
                << "\nCustomer: " << customer->id
                << "\nStatus: " << toString(customer->status)
                << "\nRisk: " << toString(churn.level)
                << "\nChurn score: "
                << churn.probability
                << "\nRFM segment: " << rfm.segment
                << "\nRFM score: " << rfm.score
                << "\nLifetime spend: " << rfm.monetary
                << "\nLoyalty tier: " << toString(customer->tier)
                << '\n';
        }

        std::cout << "\nRISK DISTRIBUTION\n";
        std::cout << "High: " << highRisk << '\n';
        std::cout << "Medium: " << mediumRisk << '\n';
        std::cout << "Low: " << lowRisk << '\n';
    }

    void cohortReport() const {
        CohortEngine::calculate(
            const_cast<CustomerRepository&>(customers).all(),
            events.all()
        );
    }
};


// ============================================================
// 15. EXECUTABLE SAMPLE SCENARIO
// ============================================================

void runTests() {

    if (std::abs(
        calculateCLV(1000, 0.70, 0.05) - 14000
    ) > 0.001) {
        throw DomainError("CLV test failed.");
    }

    if (LoyaltyEngine::determineTier(12000) !=
        LoyaltyTier::Platinum) {
        throw DomainError("Loyalty test failed.");
    }

    if (CohortEngine::monthDifference(1, 4) != 3) {
        throw DomainError("Cohort test failed.");
    }

    try {
        calculateCLV(1000, 0.70, 0);
        throw DomainError("Invalid CLV input was accepted.");
    } catch (const DomainError& error) {
        if (std::string(error.what()) ==
            "Invalid CLV input was accepted.") {
            throw;
        }
    }

    std::cout << "All tests passed.\n";
}


} // namespace retention


int main() {

    using namespace retention;

    try {

        runTests();

        RetentionService service;

        std::vector<Customer> sampleCustomers = {
            {
                "C001", "Aarav Sharma", "aarav@example.com",
                "2026-01", 10, "North", 999
            },
            {
                "C002", "Priya Verma", "priya@example.com",
                "2026-02", 15, "South", 1499
            },
            {
                "C003", "Rahul Singh", "rahul@example.com",
                "2026-03", 20, "West", 799
            },
            {
                "C004", "Ananya Gupta", "ananya@example.com",
                "2026-04", 5, "East", 1999
            }
        };

        for (const auto& customer : sampleCustomers) {
            service.addCustomer(customer);
        }

        std::vector<CustomerEvent> sampleEvents = {
            {"E001", "C001", EventType::Purchase, 5, 3000},
            {"E002", "C001", EventType::Purchase, 35, 2500},
            {"E003", "C001", EventType::Login, 1, 0},
            {"E004", "C002", EventType::Purchase, 15, 1500},
            {"E005", "C002", EventType::Login, 2, 0},
            {"E006", "C003", EventType::Purchase, 110, 700},
            {"E007", "C004", EventType::Purchase, 80, 8000},
            {"E008", "C004", EventType::Support, 10, 0},
            {"E009", "C004", EventType::Support, 8, 0},
            {"E010", "C004", EventType::Support, 5, 0}
        };

        for (const auto& event : sampleEvents) {
            service.recordEvent(event);
        }

        service.analyze();
        service.cohortReport();

        std::cout << "\nCLV ESTIMATE\n";
        std::cout << calculateCLV(1500, 0.65, 0.04)
                  << '\n';

        CampaignEngine campaignEngine;

        Campaign campaign = {
            "CMP001",
            "November Reactivation",
            1000,
            50,
            CustomerStatus::AtRisk
        };

        campaignEngine.create(campaign);

        auto& repository = service.customerRepository();

        for (Customer* customer : repository.all()) {

            if (customer->status == CustomerStatus::AtRisk) {
                campaignEngine.assign("CMP001", *customer);
            }
        }

        if (!campaignEngineReportPlaceholder) {
        }

    } catch (const std::exception& error) {
        std::cerr << "Retention engine failure: "
                  << error.what() << '\n';

        return 1;
    }

    return 0;
}
