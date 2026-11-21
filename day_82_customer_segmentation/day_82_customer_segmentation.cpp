#include <algorithm>
#include <cmath>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

enum class AccountStatus {
    Active,
    Inactive,
    Suspended
};

enum class ValueTier {
    High,
    Medium,
    Low
};

enum class MergeDecision {
    Eligible,
    Rejected
};

struct Customer {
    int id;
    string name;
    int age;
    string region;
    double annualIncome;
    int purchaseFrequency;
    double monetaryValue;
    int recencyDays;
    int sessions;
    int cartAbandonments;
    int emailInteractions;
    AccountStatus status;
};

struct SegmentationPolicy {
    double highValueThreshold = 100000.0;
    double mediumValueThreshold = 30000.0;
    double highIncomeThreshold = 1200000.0;

    int recentDays = 30;
    int dormantDays = 180;
    int frequentPurchaseThreshold = 10;
    int engagedSessionThreshold = 20;
    int engagedEmailThreshold = 10;

    void validate() const {
        if (
            highValueThreshold <= mediumValueThreshold ||
            mediumValueThreshold < 0
        ) {
            throw invalid_argument("Invalid value thresholds.");
        }

        if (
            recentDays <= 0 ||
            dormantDays <= recentDays ||
            frequentPurchaseThreshold <= 0
        ) {
            throw invalid_argument("Invalid behavioral policy.");
        }
    }
};

struct SegmentResult {
    int customerId;
    string demographic;
    string behavioral;
    ValueTier valueTier;

    int recency;
    int frequency;
    double monetary;

    double averageOrderValue;
};

struct CampaignDecision {
    bool eligible;
    string campaign;
    string reason;
};

class CustomerValidator {
public:
    static void validate(const Customer& customer) {
        if (customer.id <= 0) {
            throw invalid_argument("Customer ID must be positive.");
        }

        if (customer.name.empty()) {
            throw invalid_argument("Customer name is required.");
        }

        if (customer.age < 18 || customer.age > 120) {
            throw invalid_argument("Invalid customer age.");
        }

        if (
            customer.annualIncome < 0 ||
            customer.monetaryValue < 0
        ) {
            throw invalid_argument("Financial values cannot be negative.");
        }

        if (
            customer.purchaseFrequency < 0 ||
            customer.recencyDays < 0 ||
            customer.sessions < 0 ||
            customer.cartAbandonments < 0 ||
            customer.emailInteractions < 0
        ) {
            throw invalid_argument("Behavioral values cannot be negative.");
        }

        if (!isfinite(customer.annualIncome) ||
            !isfinite(customer.monetaryValue)) {
            throw invalid_argument("Financial values must be finite.");
        }

        if (
            customer.purchaseFrequency == 0 &&
            customer.monetaryValue > 0
        ) {
            throw invalid_argument(
                "Spending requires at least one purchase."
            );
        }
    }
};

class SegmentationEngine {
private:
    SegmentationPolicy policy;

    string demographicSegment(const Customer& customer) const {
        string ageGroup;
        string incomeGroup;

        if (customer.age < 30) {
            ageGroup = "young_adult";
        } else if (customer.age < 45) {
            ageGroup = "adult";
        } else if (customer.age < 60) {
            ageGroup = "middle_aged";
        } else {
            ageGroup = "senior";
        }

        if (customer.annualIncome >= policy.highIncomeThreshold) {
            incomeGroup = "high_income";
        } else if (
            customer.annualIncome >= policy.highIncomeThreshold / 3.0
        ) {
            incomeGroup = "middle_income";
        } else {
            incomeGroup = "lower_income";
        }

        return ageGroup + "_" + incomeGroup;
    }

    string behavioralSegment(const Customer& customer) const {
        if (customer.recencyDays > policy.dormantDays) {
            return "dormant";
        }

        if (
            customer.recencyDays <= policy.recentDays &&
            customer.purchaseFrequency >=
                policy.frequentPurchaseThreshold
        ) {
            return "loyal_active";
        }

        if (customer.recencyDays <= policy.recentDays) {
            return "recent_customer";
        }

        if (
            customer.sessions >= policy.engagedSessionThreshold ||
            customer.emailInteractions >= policy.engagedEmailThreshold
        ) {
            return "digitally_engaged";
        }

        if (
            customer.purchaseFrequency >=
            policy.frequentPurchaseThreshold
        ) {
            return "repeat_customer";
        }

        return "occasional_customer";
    }

    ValueTier valueSegment(const Customer& customer) const {
        if (customer.monetaryValue >= policy.highValueThreshold) {
            return ValueTier::High;
        }

        if (customer.monetaryValue >= policy.mediumValueThreshold) {
            return ValueTier::Medium;
        }

        return ValueTier::Low;
    }

public:
    explicit SegmentationEngine(
        const SegmentationPolicy& configuration = SegmentationPolicy()
    ) : policy(configuration) {
        policy.validate();
    }

    SegmentResult evaluate(const Customer& customer) const {
        CustomerValidator::validate(customer);

        const double averageOrderValue =
            customer.purchaseFrequency > 0
            ? customer.monetaryValue / customer.purchaseFrequency
            : 0.0;

        return {
            customer.id,
            demographicSegment(customer),
            behavioralSegment(customer),
            valueSegment(customer),
            customer.recencyDays,
            customer.purchaseFrequency,
            customer.monetaryValue,
            averageOrderValue
        };
    }

    vector<SegmentResult> evaluateBatch(
        const vector<Customer>& customers
    ) const {
        vector<SegmentResult> results;

        results.reserve(customers.size());

        for (const auto& customer : customers) {
            try {
                results.push_back(evaluate(customer));
            } catch (const exception& error) {
                cerr << "Rejected customer "
                     << customer.id << ": "
                     << error.what() << '\n';
            }
        }

        return results;
    }
};

class CustomerRegistry {
private:
    unordered_map<int, Customer> customers;

public:
    void insert(const Customer& customer) {
        CustomerValidator::validate(customer);

        auto result = customers.emplace(customer.id, customer);

        if (!result.second) {
            throw invalid_argument("Duplicate customer ID.");
        }
    }

    const Customer& get(int id) const {
        auto it = customers.find(id);

        if (it == customers.end()) {
            throw out_of_range("Customer does not exist.");
        }

        return it->second;
    }

    vector<Customer> all() const {
        vector<Customer> result;
        result.reserve(customers.size());

        for (const auto& entry : customers) {
            result.push_back(entry.second);
        }

        sort(
            result.begin(),
            result.end(),
            [](const Customer& a, const Customer& b) {
                return a.id < b.id;
            }
        );

        return result;
    }
};

class CampaignEngine {
public:
    CampaignDecision evaluate(
        const Customer& customer,
        const SegmentResult& result
    ) const {
        if (customer.status != AccountStatus::Active) {
            return {
                false,
                "",
                "Account is not active."
            };
        }

        if (result.behavioral == "dormant") {
            return {
                false,
                "",
                "Requires a dedicated reactivation campaign."
            };
        }

        if (result.valueTier == ValueTier::High) {
            return {
                true,
                "premium_retention",
                "High monetary value."
            };
        }

        if (result.behavioral == "digitally_engaged") {
            return {
                true,
                "digital_engagement",
                "High digital activity."
            };
        }

        return {
            true,
            "standard_engagement",
            "Standard campaign eligibility."
        };
    }
};

class AnalyticsEngine {
private:
    static string tierName(ValueTier tier) {
        switch (tier) {
            case ValueTier::High:
                return "high_value";
            case ValueTier::Medium:
                return "medium_value";
            case ValueTier::Low:
                return "low_value";
        }

        throw logic_error("Unknown value tier.");
    }

public:
    void report(const vector<SegmentResult>& results) const {
        if (results.empty()) {
            cout << "No valid segmentation records.\n";
            return;
        }

        map<string, int> demographic;
        map<string, int> behavioral;
        map<string, int> value;
        map<string, map<string, int>> crossTab;

        double revenue = 0.0;

        for (const auto& result : results) {
            demographic[result.demographic]++;
            behavioral[result.behavioral]++;

            const string tier = tierName(result.valueTier);

            value[tier]++;
            crossTab[result.behavioral][tier]++;

            revenue += result.monetary;
        }

        cout << fixed << setprecision(2);

        cout << "\nTOTAL CUSTOMERS: "
             << results.size() << '\n';

        cout << "TOTAL MONETARY VALUE: Rs. "
             << revenue << '\n';

        cout << "AVERAGE CUSTOMER VALUE: Rs. "
             << revenue / results.size() << '\n';

        cout << "\nDEMOGRAPHIC DISTRIBUTION\n";

        for (const auto& entry : demographic) {
            cout << entry.first << ": "
                 << entry.second << '\n';
        }

        cout << "\nBEHAVIORAL DISTRIBUTION\n";

        for (const auto& entry : behavioral) {
            cout << entry.first << ": "
                 << entry.second << '\n';
        }

        cout << "\nVALUE DISTRIBUTION\n";

        for (const auto& entry : value) {
            cout << entry.first << ": "
                 << entry.second << '\n';
        }

        cout << "\nBEHAVIORAL-VALUE CROSS TABULATION\n";

        for (const auto& row : crossTab) {
            cout << row.first << '\n';

            for (const auto& column : row.second) {
                cout << "  "
                     << column.first << ": "
                     << column.second << '\n';
            }
        }
    }
};

string tierToString(ValueTier tier) {
    switch (tier) {
        case ValueTier::High:
            return "HIGH";
        case ValueTier::Medium:
            return "MEDIUM";
        case ValueTier::Low:
            return "LOW";
    }

    return "UNKNOWN";
}

void runTests() {
    SegmentationEngine engine;

    Customer customer{
        9001, "Test Customer", 28, "Delhi",
        1500000, 15, 125000, 10,
        40, 2, 15, AccountStatus::Active
    };

    SegmentResult result = engine.evaluate(customer);

    if (result.valueTier != ValueTier::High) {
        throw runtime_error("High-value test failed.");
    }

    if (result.behavioral != "loyal_active") {
        throw runtime_error("Behavioral test failed.");
    }

    Customer zeroPurchase{
        9002, "Zero Purchase", 30, "Pune",
        400000, 0, 0, 20,
        2, 0, 0, AccountStatus::Active
    };

    result = engine.evaluate(zeroPurchase);

    if (result.averageOrderValue != 0) {
        throw runtime_error("Zero purchase test failed.");
    }

    cout << "All C++17 tests passed.\n";
}

int main() {
    try {
        runTests();

        CustomerRegistry registry;

        registry.insert({
            3001, "Customer A", 27, "Delhi",
            1800000, 20, 165000, 5,
            50, 3, 20, AccountStatus::Active
        });

        registry.insert({
            3002, "Customer B", 39, "Mumbai",
            850000, 8, 65000, 25,
            28, 5, 12, AccountStatus::Active
        });

        registry.insert({
            3003, "Customer C", 55, "Lucknow",
            450000, 3, 18000, 95,
            8, 1, 2, AccountStatus::Active
        });

        registry.insert({
            3004, "Customer D", 65, "Pune",
            2200000, 22, 245000, 12,
            75, 2, 35, AccountStatus::Active
        });

        registry.insert({
            3005, "Customer E", 32, "Jaipur",
            700000, 1, 2500, 250,
            3, 0, 0, AccountStatus::Inactive
        });

        SegmentationEngine segmenter;
        CampaignEngine campaignEngine;
        AnalyticsEngine analytics;

        vector<Customer> customers = registry.all();

        vector<SegmentResult> results =
            segmenter.evaluateBatch(customers);

        cout << "\nCUSTOMER SEGMENTATION RESULTS\n";

        for (const auto& result : results) {
            const Customer& customer =
                registry.get(result.customerId);

            CampaignDecision campaign =
                campaignEngine.evaluate(customer, result);

            cout << "\nCustomer ID: "
                 << result.customerId << '\n';

            cout << "Demographic: "
                 << result.demographic << '\n';

            cout << "Behavioral: "
                 << result.behavioral << '\n';

            cout << "Value: "
                 << tierToString(result.valueTier) << '\n';

            cout << "Recency: "
                 << result.recency << " days\n";

            cout << "Frequency: "
                 << result.frequency << '\n';

            cout << "Monetary value: Rs. "
                 << fixed << setprecision(2)
                 << result.monetary << '\n';

            cout << "Campaign eligible: "
                 << boolalpha << campaign.eligible << '\n';

            cout << "Campaign: "
                 << (campaign.eligible ? campaign.campaign : "None")
                 << '\n';

            cout << "Decision: "
                 << campaign.reason << '\n';
        }

        analytics.report(results);

    } catch (const exception& error) {
        cerr << "Application failure: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
