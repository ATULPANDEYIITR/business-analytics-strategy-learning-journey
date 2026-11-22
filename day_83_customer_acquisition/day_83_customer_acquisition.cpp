#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class Channel {
    PaidSearch,
    PaidSocial,
    OrganicSearch,
    Email,
    Referral,
    Affiliate,
    Content,
    Events,
    Direct
};

enum class CampaignStatus {
    Draft,
    Active,
    Paused,
    Completed
};

enum class ReviewDecision {
    Scale,
    Optimize,
    Reduce,
    InsufficientData
};

string channelName(Channel channel) {
    switch (channel) {
        case Channel::PaidSearch: return "Paid Search";
        case Channel::PaidSocial: return "Paid Social";
        case Channel::OrganicSearch: return "Organic Search";
        case Channel::Email: return "Email";
        case Channel::Referral: return "Referral";
        case Channel::Affiliate: return "Affiliate";
        case Channel::Content: return "Content";
        case Channel::Events: return "Events";
        case Channel::Direct: return "Direct";
    }

    throw invalid_argument("Unknown acquisition channel.");
}

string decisionName(ReviewDecision decision) {
    switch (decision) {
        case ReviewDecision::Scale: return "SCALE";
        case ReviewDecision::Optimize: return "OPTIMIZE";
        case ReviewDecision::Reduce: return "REDUCE";
        case ReviewDecision::InsufficientData: return "INSUFFICIENT DATA";
    }

    throw invalid_argument("Unknown decision.");
}

struct Campaign {
    string id;
    string name;
    Channel channel;
    double budget;
    double spend;
    long long impressions;
    long long clicks;
    long long leads;
    long long conversions;
    double revenue;
    CampaignStatus status = CampaignStatus::Draft;

    void validate() const {
        if (id.empty() || name.empty()) {
            throw invalid_argument("Campaign ID and name are required.");
        }

        if (!isfinite(budget) || !isfinite(spend) ||
            !isfinite(revenue) || budget < 0 ||
            spend < 0 || revenue < 0) {
            throw invalid_argument("Invalid campaign financial data.");
        }

        if (spend > budget) {
            throw invalid_argument("Campaign spend exceeds budget.");
        }

        if (impressions < 0 || clicks < 0 ||
            leads < 0 || conversions < 0) {
            throw invalid_argument("Negative marketing metric.");
        }

        if (clicks > impressions || leads > clicks ||
            conversions > leads) {
            throw invalid_argument("Invalid conversion funnel.");
        }
    }

    optional<double> cac() const {
        if (conversions == 0) return nullopt;
        return spend / conversions;
    }

    optional<double> roas() const {
        if (spend == 0) return nullopt;
        return revenue / spend;
    }

    double ctr() const {
        return impressions == 0
            ? 0.0
            : static_cast<double>(clicks) / impressions * 100.0;
    }

    double conversionRate() const {
        return leads == 0
            ? 0.0
            : static_cast<double>(conversions) / leads * 100.0;
    }

    void activate() {
        if (status != CampaignStatus::Draft &&
            status != CampaignStatus::Paused) {
            throw logic_error("Campaign cannot be activated from current state.");
        }

        status = CampaignStatus::Active;
    }

    void pause() {
        if (status != CampaignStatus::Active) {
            throw logic_error("Only active campaigns can be paused.");
        }

        status = CampaignStatus::Paused;
    }

    void complete() {
        if (status == CampaignStatus::Completed) {
            throw logic_error("Campaign already completed.");
        }

        status = CampaignStatus::Completed;
    }
};

struct Customer {
    string id;
    string campaignId;
    Channel channel;
    double initialRevenue;
    double monthlyRevenue;
    double grossMargin;
    double retention;

    void validate() const {
        if (id.empty() || campaignId.empty()) {
            throw invalid_argument("Customer and campaign IDs are required.");
        }

        if (!isfinite(initialRevenue) || !isfinite(monthlyRevenue) ||
            !isfinite(grossMargin) || !isfinite(retention)) {
            throw invalid_argument("Non-finite customer values.");
        }

        if (initialRevenue < 0 || monthlyRevenue < 0 ||
            grossMargin < 0 || grossMargin > 1 ||
            retention < 0 || retention > 1) {
            throw invalid_argument("Invalid customer economics.");
        }
    }

    double lifetimeValue(int months) const {
        if (months < 1) {
            throw invalid_argument("Projection period must be positive.");
        }

        const double initialProfit = initialRevenue * grossMargin;
        const double monthlyProfit = monthlyRevenue * grossMargin;

        double retained = 1.0;
        double recurringProfit = 0.0;

        for (int month = 1; month <= months; ++month) {
            retained *= retention;
            recurringProfit += retained * monthlyProfit;
        }

        return initialProfit + recurringProfit;
    }
};

struct ChannelMetrics {
    Channel channel;
    double spend = 0;
    double customerCount = 0;
    double revenue = 0;
    double grossProfit = 0;

    optional<double> cac() const {
        if (customerCount == 0) return nullopt;
        return spend / customerCount;
    }

    optional<double> ltv() const {
        if (customerCount == 0) return nullopt;
        return grossProfit / customerCount;
    }

    optional<double> ltvCacRatio() const {
        auto acquisitionCost = cac();
        auto lifetimeValue = ltv();

        if (!acquisitionCost || !lifetimeValue || *acquisitionCost <= 0) {
            return nullopt;
        }

        return *lifetimeValue / *acquisitionCost;
    }

    optional<double> roas() const {
        if (spend == 0) return nullopt;
        return revenue / spend;
    }
};

class Repository {
private:
    map<string, Campaign> campaigns;
    map<string, Customer> customers;

public:
    void addCampaign(const Campaign& campaign) {
        campaign.validate();

        if (campaigns.count(campaign.id)) {
            throw invalid_argument("Duplicate campaign ID.");
        }

        campaigns.emplace(campaign.id, campaign);
    }

    void activateCampaign(const string& campaignId) {
        auto it = campaigns.find(campaignId);

        if (it == campaigns.end()) {
            throw invalid_argument("Campaign not found.");
        }

        it->second.activate();
    }

    void addCustomer(const Customer& customer) {
        customer.validate();

        if (customers.count(customer.id)) {
            throw invalid_argument("Duplicate customer ID.");
        }

        auto campaign = campaigns.find(customer.campaignId);

        if (campaign == campaigns.end()) {
            throw invalid_argument("Customer references unknown campaign.");
        }

        if (campaign->second.channel != customer.channel) {
            throw invalid_argument("Customer channel does not match campaign.");
        }

        if (campaign->second.status != CampaignStatus::Active) {
            throw logic_error("Customer cannot be added to inactive campaign.");
        }

        customers.emplace(customer.id, customer);
    }

    const map<string, Campaign>& getCampaigns() const {
        return campaigns;
    }

    const map<string, Customer>& getCustomers() const {
        return customers;
    }
};

class GovernanceEngine {
private:
    const Repository& repository;

public:
    explicit GovernanceEngine(const Repository& repo)
        : repository(repo) {}

    map<Channel, ChannelMetrics> evaluate(int projectionMonths) const {
        map<Channel, ChannelMetrics> results;

        for (int i = 0; i <= static_cast<int>(Channel::Direct); ++i) {
            Channel channel = static_cast<Channel>(i);
            results.emplace(channel, ChannelMetrics{channel});
        }

        for (const auto& [id, campaign] : repository.getCampaigns()) {
            results.at(campaign.channel).spend += campaign.spend;
        }

        for (const auto& [id, customer] : repository.getCustomers()) {
            auto& item = results.at(customer.channel);

            item.customerCount += 1;
            item.revenue += customer.initialRevenue;
            item.grossProfit += customer.lifetimeValue(projectionMonths);
        }

        return results;
    }

    static ReviewDecision decide(
        const ChannelMetrics& metrics,
        double minimumLtvCac = 3.0,
        double maximumCac = 1000.0,
        int minimumCustomers = 10
    ) {
        auto cac = metrics.cac();
        auto ratio = metrics.ltvCacRatio();

        if (metrics.customerCount < minimumCustomers || !cac || !ratio) {
            return ReviewDecision::InsufficientData;
        }

        if (*ratio >= minimumLtvCac && *cac <= maximumCac) {
            return ReviewDecision::Scale;
        }

        if (*ratio >= 1.0) {
            return ReviewDecision::Optimize;
        }

        return ReviewDecision::Reduce;
    }

    optional<double> blendedCAC() const {
        double spend = 0;
        for (const auto& [id, campaign] : repository.getCampaigns()) {
            spend += campaign.spend;
        }

        double customerCount = repository.getCustomers().size();

        if (customerCount == 0) return nullopt;

        return spend / customerCount;
    }
};

struct BudgetForecast {
    Channel channel;
    double expectedCAC;
};

class BudgetOptimizer {
public:
    static map<Channel, double> allocate(
        double totalBudget,
        const vector<BudgetForecast>& forecasts,
        double minimumAllocation = 0.0
    ) {
        if (!isfinite(totalBudget) || totalBudget < 0 ||
            !isfinite(minimumAllocation) || minimumAllocation < 0) {
            throw invalid_argument("Invalid budget.");
        }

        if (forecasts.empty()) {
            throw invalid_argument("Forecast list cannot be empty.");
        }

        set<Channel> uniqueChannels;
        double efficiencyTotal = 0;

        for (const auto& item : forecasts) {
            if (!isfinite(item.expectedCAC) || item.expectedCAC <= 0) {
                throw invalid_argument("Expected CAC must be positive.");
            }

            if (!uniqueChannels.insert(item.channel).second) {
                throw invalid_argument("Duplicate forecast channel.");
            }

            efficiencyTotal += 1.0 / item.expectedCAC;
        }

        if (minimumAllocation * forecasts.size() > totalBudget) {
            throw invalid_argument("Minimum allocation exceeds total budget.");
        }

        double remaining = totalBudget -
            minimumAllocation * forecasts.size();

        map<Channel, double> allocation;
        double allocated = 0;

        for (const auto& item : forecasts) {
            double share = (1.0 / item.expectedCAC) / efficiencyTotal;
            double amount = minimumAllocation + remaining * share;

            allocation[item.channel] = amount;
            allocated += amount;
        }

        // Floating-point residual is assigned to the most efficient channel.
        auto best = min_element(
            forecasts.begin(),
            forecasts.end(),
            [](const auto& a, const auto& b) {
                return a.expectedCAC < b.expectedCAC;
            }
        );

        allocation[best->channel] += totalBudget - allocated;

        return allocation;
    }
};

Repository buildSampleRepository() {
    Repository repository;

    vector<Campaign> campaigns = {
        {"C001", "Search Acquisition", Channel::PaidSearch,
         50000, 42000, 500000, 25000, 5000, 1000, 180000},

        {"C002", "Social Acquisition", Channel::PaidSocial,
         40000, 36000, 800000, 40000, 6000, 600, 90000},

        {"C003", "Organic Acquisition", Channel::OrganicSearch,
         20000, 15000, 600000, 30000, 4500, 900, 150000},

        {"C004", "Referral Acquisition", Channel::Referral,
         15000, 12000, 100000, 10000, 3000, 750, 140000},

        {"C005", "Email Acquisition", Channel::Email,
         10000, 7000, 200000, 12000, 3600, 720, 110000}
    };

    for (auto& campaign : campaigns) {
        repository.addCampaign(campaign);
        repository.activateCampaign(campaign.id);
    }

    vector<Customer> customers = {
        {"U001", "C001", Channel::PaidSearch, 120, 100, 0.75, 0.92},
        {"U002", "C001", Channel::PaidSearch, 150, 100, 0.75, 0.92},
        {"U003", "C002", Channel::PaidSocial, 90, 100, 0.65, 0.90},
        {"U004", "C002", Channel::PaidSocial, 110, 100, 0.65, 0.90},
        {"U005", "C003", Channel::OrganicSearch, 140, 100, 0.80, 0.93},
        {"U006", "C003", Channel::OrganicSearch, 160, 100, 0.80, 0.93},
        {"U007", "C004", Channel::Referral, 180, 100, 0.82, 0.94},
        {"U008", "C004", Channel::Referral, 170, 100, 0.82, 0.94},
        {"U009", "C005", Channel::Email, 130, 100, 0.78, 0.92},
        {"U010", "C005", Channel::Email, 125, 100, 0.78, 0.92}
    };

    for (const auto& customer : customers) {
        repository.addCustomer(customer);
    }

    return repository;
}

void runTests() {
    Campaign campaign{
        "TEST", "Test Campaign", Channel::PaidSearch,
        1000, 800, 10000, 500, 100, 20, 2000
    };

    campaign.validate();

    if (!campaign.cac() || abs(*campaign.cac() - 40.0) > 0.000001) {
        throw runtime_error("CAC calculation test failed.");
    }

    Customer customer{
        "TEST-CUSTOMER", "TEST", Channel::PaidSearch,
        100, 100, 0.8, 0.9
    };

    if (customer.lifetimeValue(1) <= 0) {
        throw runtime_error("LTV calculation test failed.");
    }

    auto allocation = BudgetOptimizer::allocate(
        3000,
        {
            {Channel::PaidSearch, 50},
            {Channel::PaidSocial, 100}
        }
    );

    double allocated = 0;

    for (const auto& [channel, amount] : allocation) {
        allocated += amount;
    }

    if (abs(allocated - 3000) > 0.000001) {
        throw runtime_error("Budget allocation test failed.");
    }

    cout << "All validation tests passed.\n";
}

int main() {
    try {
        Repository repository = buildSampleRepository();
        GovernanceEngine engine(repository);

        cout << fixed << setprecision(2);

        cout << "\nCUSTOMER ACQUISITION ANALYSIS\n";
        cout << string(90, '=') << "\n";

        for (const auto& [id, campaign] : repository.getCampaigns()) {
            cout << campaign.name
                 << " | Channel: " << channelName(campaign.channel)
                 << " | Spend: " << campaign.spend
                 << " | Customers: " << campaign.conversions
                 << " | CAC: ";

            if (campaign.cac()) cout << *campaign.cac();
            else cout << "N/A";

            cout << " | ROAS: ";

            if (campaign.roas()) cout << *campaign.roas();
            else cout << "N/A";

            cout << "\n";
        }

        auto metrics = engine.evaluate(24);

        cout << "\nCHANNEL UNIT ECONOMICS\n";

        for (const auto& [channel, item] : metrics) {
            cout << channelName(channel)
                 << " | Spend: " << item.spend
                 << " | Customers: " << item.customerCount
                 << " | CAC: ";

            if (item.cac()) cout << *item.cac();
            else cout << "N/A";

            cout << " | LTV: ";

            if (item.ltv()) cout << *item.ltv();
            else cout << "N/A";

            cout << " | LTV/CAC: ";

            if (item.ltvCacRatio()) cout << *item.ltvCacRatio();
            else cout << "N/A";

            cout << " | Decision: "
                 << decisionName(GovernanceEngine::decide(
                     item, 3.0, 1000.0, 2
                 ))
                 << "\n";
        }

        cout << "\nBLENDED CAC: ";

        if (engine.blendedCAC()) {
            cout << *engine.blendedCAC() << "\n";
        } else {
            cout << "N/A\n";
        }

        cout << "\nBUDGET ALLOCATION\n";

        auto allocation = BudgetOptimizer::allocate(
            100000,
            {
                {Channel::PaidSearch, 42},
                {Channel::PaidSocial, 60},
                {Channel::OrganicSearch, 30},
                {Channel::Referral, 25},
                {Channel::Email, 20}
            }
        );

        for (const auto& [channel, amount] : allocation) {
            cout << channelName(channel) << ": " << amount << "\n";
        }

        cout << "\nVALIDATION\n";
        runTests();

    } catch (const exception& error) {
        cerr << "Acquisition analysis error: "
             << error.what() << "\n";

        return 1;
    }

    return 0;
}
