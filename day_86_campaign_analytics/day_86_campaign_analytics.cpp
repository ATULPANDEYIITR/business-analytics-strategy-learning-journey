#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Campaign Analytics Performance Engine
 *
 * C++17 implementation focused on:
 * - Efficient metric computation
 * - Portfolio and channel aggregation
 * - Campaign ranking
 * - Budget allocation
 * - Performance thresholds
 * - Data validation
 * - Explicit campaign state
 */

namespace marketing {

enum class Channel {
    Search,
    Social,
    Email,
    Display,
    Affiliate,
    Video
};

enum class Status {
    Active,
    Paused,
    Completed
};

enum class Performance {
    Excellent,
    Profitable,
    BreakEven,
    LossMaking,
    NoInvestment
};

std::string toString(Channel channel) {
    switch (channel) {
        case Channel::Search: return "Search";
        case Channel::Social: return "Social";
        case Channel::Email: return "Email";
        case Channel::Display: return "Display";
        case Channel::Affiliate: return "Affiliate";
        case Channel::Video: return "Video";
    }

    throw std::invalid_argument("Unknown channel");
}

std::string toString(Status status) {
    switch (status) {
        case Status::Active: return "Active";
        case Status::Paused: return "Paused";
        case Status::Completed: return "Completed";
    }

    throw std::invalid_argument("Unknown status");
}

struct Campaign {
    std::string id;
    std::string name;
    Channel channel;
    Status status;

    double budget;
    double spend;
    double revenue;

    long long impressions;
    long long clicks;
    long long conversions;

    void validate() const {
        if (id.empty() || name.empty()) {
            throw std::invalid_argument(
                "Campaign ID and name are required"
            );
        }

        if (
            !std::isfinite(budget) ||
            !std::isfinite(spend) ||
            !std::isfinite(revenue) ||
            budget <= 0 ||
            spend < 0 ||
            revenue < 0
        ) {
            throw std::invalid_argument(
                "Invalid financial values"
            );
        }

        if (
            impressions < 0 ||
            clicks < 0 ||
            conversions < 0
        ) {
            throw std::invalid_argument(
                "Negative funnel values"
            );
        }

        if (
            clicks > impressions ||
            conversions > clicks
        ) {
            throw std::invalid_argument(
                "Invalid conversion funnel"
            );
        }
    }
};

struct Metrics {
    std::string id;
    std::string name;
    Channel channel;
    Status status;

    double spend;
    double revenue;
    double profit;

    double roi;
    double roas;

    double ctr;
    double conversionRate;

    double cpc;
    double cpa;
    double cpm;

    double budgetUtilization;
};

struct Portfolio {
    double spend = 0;
    double revenue = 0;
    double profit = 0;
    double roi = 0;
    double roas = 0;
    std::size_t campaigns = 0;
};

struct ChannelSummary {
    double spend = 0;
    double revenue = 0;
    double profit = 0;
    double roi = 0;
    double roas = 0;
    std::size_t campaigns = 0;
};

class MetricEngine {
private:
    static double divide(double numerator, double denominator) {
        return denominator == 0
            ? 0.0
            : numerator / denominator;
    }

public:
    static Metrics calculate(const Campaign& campaign) {
        campaign.validate();

        Metrics result{};

        result.id = campaign.id;
        result.name = campaign.name;
        result.channel = campaign.channel;
        result.status = campaign.status;

        result.spend = campaign.spend;
        result.revenue = campaign.revenue;
        result.profit = campaign.revenue - campaign.spend;

        result.roi = divide(
            result.profit * 100,
            campaign.spend
        );

        result.roas = divide(
            campaign.revenue,
            campaign.spend
        );

        result.ctr = divide(
            campaign.clicks * 100.0,
            campaign.impressions
        );

        result.conversionRate = divide(
            campaign.conversions * 100.0,
            campaign.clicks
        );

        result.cpc = divide(
            campaign.spend,
            campaign.clicks
        );

        result.cpa = divide(
            campaign.spend,
            campaign.conversions
        );

        result.cpm = divide(
            campaign.spend * 1000.0,
            campaign.impressions
        );

        result.budgetUtilization = divide(
            campaign.spend * 100,
            campaign.budget
        );

        return result;
    }

    static Performance classify(const Metrics& metrics) {
        if (metrics.spend == 0) {
            return Performance::NoInvestment;
        }

        if (metrics.roi > 100 && metrics.roas >= 3) {
            return Performance::Excellent;
        }

        if (metrics.roi > 0 && metrics.roas > 1) {
            return Performance::Profitable;
        }

        if (metrics.roi == 0) {
            return Performance::BreakEven;
        }

        return Performance::LossMaking;
    }

    static std::string toString(Performance performance) {
        switch (performance) {
            case Performance::Excellent: return "Excellent";
            case Performance::Profitable: return "Profitable";
            case Performance::BreakEven: return "Break Even";
            case Performance::LossMaking: return "Loss Making";
            case Performance::NoInvestment: return "No Investment";
        }

        throw std::invalid_argument("Unknown performance");
    }
};

class CampaignRegistry {
private:
    // Ordered map provides deterministic ID-based access.
    std::map<std::string, Campaign> campaigns;

public:
    void add(const Campaign& campaign) {
        campaign.validate();

        auto result = campaigns.emplace(
            campaign.id,
            campaign
        );

        if (!result.second) {
            throw std::invalid_argument(
                "Duplicate campaign ID: " + campaign.id
            );
        }
    }

    const Campaign& get(const std::string& id) const {
        auto iterator = campaigns.find(id);

        if (iterator == campaigns.end()) {
            throw std::out_of_range(
                "Campaign not found: " + id
            );
        }

        return iterator->second;
    }

    std::vector<Metrics> evaluate() const {
        std::vector<Metrics> result;
        result.reserve(campaigns.size());

        for (const auto& entry : campaigns) {
            result.push_back(
                MetricEngine::calculate(entry.second)
            );
        }

        return result;
    }

    void recordSpend(
        const std::string& id,
        double additionalSpend
    ) {
        if (
            !std::isfinite(additionalSpend) ||
            additionalSpend < 0
        ) {
            throw std::invalid_argument(
                "Invalid additional spend"
            );
        }

        auto iterator = campaigns.find(id);

        if (iterator == campaigns.end()) {
            throw std::out_of_range("Unknown campaign");
        }

        Campaign updated = iterator->second;
        updated.spend += additionalSpend;
        updated.validate();

        // Commit only after validation succeeds.
        iterator->second = updated;
    }
};

class PortfolioAnalyzer {
public:
    static Portfolio calculate(
        const std::vector<Metrics>& metrics
    ) {
        Portfolio portfolio;

        portfolio.campaigns = metrics.size();

        for (const auto& metric : metrics) {
            portfolio.spend += metric.spend;
            portfolio.revenue += metric.revenue;
        }

        portfolio.profit =
            portfolio.revenue - portfolio.spend;

        portfolio.roi = portfolio.spend
            ? portfolio.profit / portfolio.spend * 100
            : 0;

        portfolio.roas = portfolio.spend
            ? portfolio.revenue / portfolio.spend
            : 0;

        return portfolio;
    }

    static std::map<Channel, ChannelSummary> byChannel(
        const std::vector<Metrics>& metrics
    ) {
        std::map<Channel, ChannelSummary> result;

        for (const auto& metric : metrics) {
            auto& summary = result[metric.channel];

            summary.spend += metric.spend;
            summary.revenue += metric.revenue;
            summary.campaigns++;
        }

        for (auto& entry : result) {
            auto& summary = entry.second;

            summary.profit =
                summary.revenue - summary.spend;

            summary.roi = summary.spend
                ? summary.profit / summary.spend * 100
                : 0;

            summary.roas = summary.spend
                ? summary.revenue / summary.spend
                : 0;
        }

        return result;
    }

    static std::vector<Metrics> rank(
        std::vector<Metrics> metrics
    ) {
        std::sort(
            metrics.begin(),
            metrics.end(),
            [](const Metrics& a, const Metrics& b) {
                if (a.profit != b.profit) {
                    return a.profit > b.profit;
                }

                if (a.roi != b.roi) {
                    return a.roi > b.roi;
                }

                return a.roas > b.roas;
            }
        );

        return metrics;
    }
};

struct Allocation {
    std::string campaignId;
    double amount;
};

class BudgetOptimizer {
public:
    static std::vector<Allocation> allocate(
        const std::vector<Metrics>& metrics,
        double availableBudget,
        double minimumRoas = 1.5
    ) {
        if (
            !std::isfinite(availableBudget) ||
            availableBudget < 0 ||
            minimumRoas < 0
        ) {
            throw std::invalid_argument(
                "Invalid optimization parameters"
            );
        }

        std::vector<const Metrics*> eligible;
        double totalSpend = 0;

        for (const auto& metric : metrics) {
            if (
                metric.status == Status::Active &&
                metric.roas >= minimumRoas &&
                metric.spend > 0
            ) {
                eligible.push_back(&metric);
                totalSpend += metric.spend;
            }
        }

        std::vector<Allocation> allocations;

        if (eligible.empty()) {
            return allocations;
        }

        for (const Metrics* metric : eligible) {
            const double share =
                metric->spend / totalSpend;

            allocations.push_back({
                metric->id,
                availableBudget * share
            });
        }

        return allocations;
    }
};

void printReport(
    const Portfolio& portfolio,
    const std::vector<Metrics>& ranking,
    const std::map<Channel, ChannelSummary>& channels
) {
    std::cout << std::fixed << std::setprecision(2);

    std::cout << "\nPORTFOLIO REPORT\n";
    std::cout << "------------------------------\n";

    std::cout << "Campaigns: " << portfolio.campaigns << '\n';
    std::cout << "Spend:     " << portfolio.spend << '\n';
    std::cout << "Revenue:   " << portfolio.revenue << '\n';
    std::cout << "Profit:    " << portfolio.profit << '\n';
    std::cout << "ROI:       " << portfolio.roi << "%\n";
    std::cout << "ROAS:      " << portfolio.roas << '\n';

    std::cout << "\nCAMPAIGN RANKING\n";
    std::cout << "------------------------------\n";

    for (std::size_t i = 0; i < ranking.size(); ++i) {
        const auto& metric = ranking[i];

        std::cout
            << i + 1 << ". "
            << metric.name
            << " | Profit: " << metric.profit
            << " | ROI: " << metric.roi << "%"
            << " | ROAS: " << metric.roas
            << " | "
            << MetricEngine::toString(
                MetricEngine::classify(metric)
            )
            << '\n';
    }

    std::cout << "\nCHANNEL ANALYSIS\n";
    std::cout << "------------------------------\n";

    for (const auto& entry : channels) {
        const auto& summary = entry.second;

        std::cout
            << toString(entry.first)
            << " | Spend: " << summary.spend
            << " | Revenue: " << summary.revenue
            << " | ROI: " << summary.roi << "%"
            << " | ROAS: " << summary.roas
            << '\n';
    }
}

void runTests() {
    Campaign test{
        "TEST",
        "Validation Campaign",
        Channel::Search,
        Status::Active,
        1000,
        500,
        1500,
        10000,
        1000,
        100
    };

    const Metrics metric = MetricEngine::calculate(test);

    if (
        std::abs(metric.roas - 3.0) > 0.000001 ||
        std::abs(metric.roi - 200.0) > 0.000001
    ) {
        throw std::runtime_error(
            "Metric calculation test failed"
        );
    }

    Campaign invalid = test;
    invalid.id = "INVALID";
    invalid.clicks = 20000;

    bool rejected = false;

    try {
        invalid.validate();
    } catch (const std::invalid_argument&) {
        rejected = true;
    }

    if (!rejected) {
        throw std::runtime_error(
            "Invalid campaign was accepted"
        );
    }

    std::cout << "All C++ validation tests passed.\n";
}

Campaign makeCampaign(
    std::string id,
    std::string name,
    Channel channel,
    double budget,
    double spend,
    long long impressions,
    long long clicks,
    long long conversions,
    double revenue,
    Status status = Status::Active
) {
    return Campaign{
        std::move(id),
        std::move(name),
        channel,
        status,
        budget,
        spend,
        revenue,
        impressions,
        clicks,
        conversions
    };
}

} // namespace marketing

int main() {
    using namespace marketing;

    try {
        runTests();

        CampaignRegistry registry;

        registry.add(makeCampaign(
            "C001", "Search Conversion",
            Channel::Search, 50000, 35000,
            500000, 25000, 1500, 140000
        ));

        registry.add(makeCampaign(
            "C002", "Social Awareness",
            Channel::Social, 40000, 30000,
            800000, 16000, 400, 45000
        ));

        registry.add(makeCampaign(
            "C003", "Email Retention",
            Channel::Email, 20000, 12000,
            200000, 30000, 2400, 96000
        ));

        registry.add(makeCampaign(
            "C004", "Display Remarketing",
            Channel::Display, 30000, 25000,
            1000000, 10000, 250, 18000
        ));

        registry.add(makeCampaign(
            "C005", "Affiliate Acquisition",
            Channel::Affiliate, 25000, 15000,
            300000, 12000, 900, 75000
        ));

        registry.add(makeCampaign(
            "C006", "Video Awareness",
            Channel::Video, 35000, 0,
            0, 0, 0, 0,
            Status::Paused
        ));

        const auto metrics = registry.evaluate();

        const auto portfolio =
            PortfolioAnalyzer::calculate(metrics);

        const auto ranking =
            PortfolioAnalyzer::rank(metrics);

        const auto channels =
            PortfolioAnalyzer::byChannel(metrics);

        printReport(portfolio, ranking, channels);

        const auto allocations = BudgetOptimizer::allocate(
            metrics,
            100000,
            1.5
        );

        std::cout << "\nBUDGET RECOMMENDATIONS\n";
        std::cout << "------------------------------\n";

        for (const auto& allocation : allocations) {
            std::cout
                << allocation.campaignId
                << ": "
                << allocation.amount
                << '\n';
        }

        std::cout << "\nBudget allocation total: "
                  << std::accumulate(
                      allocations.begin(),
                      allocations.end(),
                      0.0,
                      [](double total, const Allocation& a) {
                          return total + a.amount;
                      }
                  )
                  << '\n';

    } catch (const std::exception& error) {
        std::cerr
            << "Campaign analytics error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
