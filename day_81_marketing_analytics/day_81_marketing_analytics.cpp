#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

enum class Channel {
    Search,
    Social,
    Email,
    Display
};

enum class AttributionModel {
    FirstTouch,
    LastTouch,
    Linear
};

string channelName(Channel channel) {
    switch (channel) {
        case Channel::Search: return "Search";
        case Channel::Social: return "Social";
        case Channel::Email: return "Email";
        case Channel::Display: return "Display";
    }

    throw invalid_argument("Unknown channel.");
}

struct Campaign {
    string id;
    string name;
    Channel channel;
    double budget;
};

struct Metrics {
    long long impressions = 0;
    long long clicks = 0;
    long long conversions = 0;
    double spend = 0;
    double revenue = 0;
};

struct Customer {
    string id;
    double acquisitionCost;
    double lifetimeRevenue;
};

struct Touchpoint {
    string campaignId;
    long long timestamp;
};

struct Performance {
    string campaignId;
    double ctr;
    double conversionRate;
    double cpc;
    double cpa;
    double roas;
    double roi;
};

class MarketingGovernanceEngine {
private:
    unordered_map<string, Campaign> campaigns;
    unordered_map<string, Metrics> metrics;
    unordered_map<string, Customer> customers;

    unordered_map<string, vector<Touchpoint>> journeys;
    unordered_set<string> processedEvents;

    static double divide(double a, double b) {
        return b == 0 ? 0.0 : a / b;
    }

    void validateCampaign(const Campaign& campaign) const {
        if (campaign.id.empty() || campaign.name.empty()) {
            throw invalid_argument("Campaign identity is required.");
        }

        if (!isfinite(campaign.budget) || campaign.budget < 0) {
            throw invalid_argument("Invalid campaign budget.");
        }
    }

public:
    void addCampaign(const Campaign& campaign) {
        validateCampaign(campaign);

        if (campaigns.count(campaign.id)) {
            throw invalid_argument("Duplicate campaign.");
        }

        campaigns.emplace(campaign.id, campaign);
        metrics.emplace(campaign.id, Metrics{});
    }

    void addCustomer(const Customer& customer) {
        if (customer.id.empty() ||
            !isfinite(customer.acquisitionCost) ||
            !isfinite(customer.lifetimeRevenue) ||
            customer.acquisitionCost < 0 ||
            customer.lifetimeRevenue < 0) {
            throw invalid_argument("Invalid customer.");
        }

        if (!customers.emplace(customer.id, customer).second) {
            throw invalid_argument("Duplicate customer.");
        }
    }

    void recordImpression(
        const string& eventId,
        const string& campaignId
    ) {
        if (!processedEvents.insert(eventId).second) {
            return;
        }

        auto it = metrics.find(campaignId);

        if (it == metrics.end()) {
            processedEvents.erase(eventId);
            throw invalid_argument("Unknown campaign.");
        }

        it->second.impressions++;
    }

    void recordClick(
        const string& eventId,
        const string& campaignId
    ) {
        if (processedEvents.count(eventId)) {
            return;
        }

        auto it = metrics.find(campaignId);

        if (it == metrics.end()) {
            throw invalid_argument("Unknown campaign.");
        }

        if (it->second.clicks >= it->second.impressions) {
            throw invalid_argument(
                "Click requires an available impression."
            );
        }

        it->second.clicks++;
        processedEvents.insert(eventId);
    }

    void recordConversion(
        const string& eventId,
        const string& campaignId,
        double revenue
    ) {
        if (processedEvents.count(eventId)) {
            return;
        }

        auto it = metrics.find(campaignId);

        if (it == metrics.end()) {
            throw invalid_argument("Unknown campaign.");
        }

        if (!isfinite(revenue) || revenue < 0) {
            throw invalid_argument("Invalid revenue.");
        }

        if (it->second.conversions >= it->second.clicks) {
            throw invalid_argument(
                "Conversion requires a recorded click."
            );
        }

        it->second.conversions++;
        it->second.revenue += revenue;
        processedEvents.insert(eventId);
    }

    void recordSpend(const string& campaignId, double amount) {
        auto campaign = campaigns.find(campaignId);
        auto data = metrics.find(campaignId);

        if (campaign == campaigns.end() || data == metrics.end()) {
            throw invalid_argument("Unknown campaign.");
        }

        if (!isfinite(amount) || amount < 0) {
            throw invalid_argument("Invalid expenditure.");
        }

        if (data->second.spend + amount > campaign->second.budget) {
            throw invalid_argument("Campaign budget exceeded.");
        }

        data->second.spend += amount;
    }

    void addTouchpoint(
        const string& customerId,
        const string& campaignId,
        long long timestamp
    ) {
        if (!customers.count(customerId)) {
            throw invalid_argument("Unknown customer.");
        }

        if (!campaigns.count(campaignId)) {
            throw invalid_argument("Unknown campaign.");
        }

        if (timestamp < 0) {
            throw invalid_argument("Invalid timestamp.");
        }

        journeys[customerId].push_back({
            campaignId,
            timestamp
        });

        auto& events = journeys[customerId];

        sort(
            events.begin(),
            events.end(),
            [](const Touchpoint& a, const Touchpoint& b) {
                return a.timestamp < b.timestamp;
            }
        );
    }

    Performance calculatePerformance(
        const string& campaignId
    ) const {
        auto it = metrics.find(campaignId);

        if (it == metrics.end()) {
            throw invalid_argument("Unknown campaign.");
        }

        const Metrics& m = it->second;

        return {
            campaignId,
            divide(m.clicks, m.impressions) * 100,
            divide(m.conversions, m.clicks) * 100,
            divide(m.spend, m.clicks),
            divide(m.spend, m.conversions),
            divide(m.revenue, m.spend),
            divide(m.revenue - m.spend, m.spend) * 100
        };
    }

    map<string, double> attributeRevenue(
        const string& customerId,
        AttributionModel model
    ) const {
        auto customer = customers.find(customerId);

        if (customer == customers.end()) {
            throw invalid_argument("Unknown customer.");
        }

        auto journey = journeys.find(customerId);

        if (journey == journeys.end() || journey->second.empty()) {
            return {};
        }

        const auto& events = journey->second;

        map<string, double> allocations;

        if (model == AttributionModel::FirstTouch) {
            allocations[events.front().campaignId] =
                customer->second.lifetimeRevenue;
        } else if (model == AttributionModel::LastTouch) {
            allocations[events.back().campaignId] =
                customer->second.lifetimeRevenue;
        } else {
            const double share =
                customer->second.lifetimeRevenue / events.size();

            for (const auto& event : events) {
                allocations[event.campaignId] += share;
            }
        }

        return allocations;
    }

    map<string, Metrics> channelReport() const {
        map<string, Metrics> result;

        for (const auto& [id, campaign] : campaigns) {
            const Metrics& source = metrics.at(id);
            Metrics& target = result[channelName(campaign.channel)];

            target.impressions += source.impressions;
            target.clicks += source.clicks;
            target.conversions += source.conversions;
            target.spend += source.spend;
            target.revenue += source.revenue;
        }

        return result;
    }

    vector<Performance> rankedCampaigns() const {
        vector<Performance> result;

        for (const auto& [id, campaign] : campaigns) {
            result.push_back(calculatePerformance(id));
        }

        sort(
            result.begin(),
            result.end(),
            [](const Performance& a, const Performance& b) {
                if (a.roas != b.roas) {
                    return a.roas > b.roas;
                }

                return a.conversionRate > b.conversionRate;
            }
        );

        return result;
    }

    void printDashboard() const {
        cout << fixed << setprecision(2);

        cout << "\nMARKETING PERFORMANCE DASHBOARD\n";
        cout << string(90, '=') << '\n';

        cout
            << left << setw(12) << "Campaign"
            << right << setw(12) << "CTR"
            << setw(15) << "Conversion"
            << setw(12) << "CPC"
            << setw(12) << "CPA"
            << setw(12) << "ROAS"
            << setw(12) << "ROI"
            << '\n';

        for (const auto& report : rankedCampaigns()) {
            cout
                << left << setw(12) << report.campaignId
                << right << setw(12) << report.ctr
                << setw(15) << report.conversionRate
                << setw(12) << report.cpc
                << setw(12) << report.cpa
                << setw(12) << report.roas
                << setw(12) << report.roi
                << '\n';
        }

        cout << "\nCHANNEL PERFORMANCE\n";

        for (const auto& [channel, m] : channelReport()) {
            cout
                << channel
                << " | Spend: " << m.spend
                << " | Revenue: " << m.revenue
                << " | Conversions: " << m.conversions
                << " | ROAS: " << divide(m.revenue, m.spend)
                << '\n';
        }
    }
};

void runTests(MarketingGovernanceEngine& engine) {
    auto report = engine.calculatePerformance("C001");

    if (abs(report.ctr - 8.0) > 0.001) {
        throw runtime_error("CTR calculation failed.");
    }

    if (abs(report.roas - 6.0) > 0.001) {
        throw runtime_error("ROAS calculation failed.");
    }

    const auto attribution = engine.attributeRevenue(
        "U001",
        AttributionModel::FirstTouch
    );

    if (attribution.empty()) {
        throw runtime_error("Attribution test failed.");
    }

    cout << "Validation tests passed.\n";
}

int main() {
    try {
        MarketingGovernanceEngine engine;

        engine.addCampaign({
            "C001",
            "Search Acquisition",
            Channel::Search,
            50000
        });

        engine.addCampaign({
            "C002",
            "Social Awareness",
            Channel::Social,
            40000
        });

        engine.addCampaign({
            "C003",
            "Email Retention",
            Channel::Email,
            20000
        });

        engine.addCustomer({
            "U001",
            500,
            3000
        });

        engine.addCustomer({
            "U002",
            400,
            2500
        });

        // Search campaign: 8,000 clicks from 100,000 impressions.
        for (int i = 0; i < 100000; ++i) {
            engine.recordImpression(
                "SI" + to_string(i), "C001"
            );
        }

        for (int i = 0; i < 8000; ++i) {
            engine.recordClick(
                "SC" + to_string(i), "C001"
            );
        }

        for (int i = 0; i < 640; ++i) {
            engine.recordConversion(
                "SV" + to_string(i), "C001", 375
            );
        }

        engine.recordSpend("C001", 40000);

        // Social campaign.
        for (int i = 0; i < 150000; ++i) {
            engine.recordImpression(
                "DI" + to_string(i), "C002"
            );
        }

        for (int i = 0; i < 6000; ++i) {
            engine.recordClick(
                "DC" + to_string(i), "C002"
            );
        }

        for (int i = 0; i < 240; ++i) {
            engine.recordConversion(
                "DV" + to_string(i), "C002", 375
            );
        }

        engine.recordSpend("C002", 30000);

        engine.addTouchpoint("U001", "C002", 100);
        engine.addTouchpoint("U001", "C001", 200);

        engine.addTouchpoint("U002", "C001", 300);
        engine.addTouchpoint("U002", "C003", 400);

        runTests(engine);
        engine.printDashboard();

        cout << "\nCUSTOMER ATTRIBUTION\n";

        for (const auto& [campaign, revenue] :
             engine.attributeRevenue(
                 "U001",
                 AttributionModel::Linear
             )) {
            cout << campaign << ": " << revenue << '\n';
        }

        cout << "\nProgram completed successfully.\n";

    } catch (const exception& error) {
        cerr << "Error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
