#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

/*
 * Conversion Analytics and Funnel Optimization
 * C++17
 *
 * Repository-independent conversion analytics engine.
 * Uses typed events, indexed user journeys, funnel evaluation,
 * attribution, experiment evaluation and mergeable reports.
 */

enum class Stage {
    Visit,
    ProductView,
    AddToCart,
    Checkout,
    Purchase
};

const std::vector<Stage> STAGES = {
    Stage::Visit,
    Stage::ProductView,
    Stage::AddToCart,
    Stage::Checkout,
    Stage::Purchase
};

std::string stageName(Stage stage) {
    switch (stage) {
        case Stage::Visit: return "visit";
        case Stage::ProductView: return "product_view";
        case Stage::AddToCart: return "add_to_cart";
        case Stage::Checkout: return "checkout";
        case Stage::Purchase: return "purchase";
    }

    throw std::invalid_argument("Unknown stage");
}

int stageIndex(Stage stage) {
    for (int i = 0; i < static_cast<int>(STAGES.size()); ++i) {
        if (STAGES[i] == stage) return i;
    }

    throw std::invalid_argument("Invalid stage");
}


// ---------------------------------------------------------
// 1. DOMAIN MODEL
// ---------------------------------------------------------

struct Event {
    std::string eventId;
    std::string userId;
    Stage stage;
    long long timestamp;
    std::string channel;
    std::string campaign;
    double revenue = 0.0;
};

struct FunnelStep {
    std::string stage;
    std::size_t users = 0;
    std::size_t previousUsers = 0;
    double conversionRate = 0.0;
    double dropOffRate = 0.0;
};

struct FunnelReport {
    std::size_t visitors = 0;
    std::size_t conversions = 0;
    double overallRate = 0.0;
    std::vector<FunnelStep> steps;
};

struct ChannelMetrics {
    std::size_t visitors = 0;
    std::size_t conversions = 0;
    double revenue = 0.0;

    double conversionRate() const {
        if (visitors == 0) return 0.0;

        return 100.0 * conversions / visitors;
    }

    double revenuePerVisitor() const {
        if (visitors == 0) return 0.0;

        return revenue / visitors;
    }
};


// ---------------------------------------------------------
// 2. VALIDATION
// ---------------------------------------------------------

void validateEvent(const Event& event) {
    if (event.eventId.empty() || event.userId.empty()) {
        throw std::invalid_argument("Missing event or user ID");
    }

    if (event.channel.empty() || event.campaign.empty()) {
        throw std::invalid_argument("Missing attribution information");
    }

    if (!std::isfinite(event.revenue) || event.revenue < 0.0) {
        throw std::invalid_argument("Invalid revenue");
    }

    if (event.stage != Stage::Purchase && event.revenue != 0.0) {
        throw std::invalid_argument(
            "Only purchase events can contain revenue"
        );
    }

    stageIndex(event.stage);
}

double safeRate(std::size_t numerator, std::size_t denominator) {
    if (numerator > denominator) {
        throw std::invalid_argument("Numerator exceeds denominator");
    }

    if (denominator == 0) return 0.0;

    return 100.0 * static_cast<double>(numerator) / denominator;
}


// ---------------------------------------------------------
// 3. EVENT STORE
// ---------------------------------------------------------

class EventStore {
private:
    std::vector<Event> events;
    std::unordered_set<std::string> eventIds;

public:
    bool add(const Event& event) {
        validateEvent(event);

        if (eventIds.count(event.eventId)) {
            return false;
        }

        eventIds.insert(event.eventId);
        events.push_back(event);

        return true;
    }

    std::size_t addBatch(const std::vector<Event>& batch) {
        std::size_t accepted = 0;

        // Validate the complete batch before modifying persistent state.
        std::unordered_set<std::string> incoming;

        for (const auto& event : batch) {
            validateEvent(event);

            if (eventIds.count(event.eventId) ||
                !incoming.insert(event.eventId).second) {
                throw std::invalid_argument(
                    "Duplicate ID inside ingestion batch"
                );
            }
        }

        for (const auto& event : batch) {
            if (add(event)) ++accepted;
        }

        return accepted;
    }

    const std::vector<Event>& all() const {
        return events;
    }

    std::size_t size() const {
        return events.size();
    }
};


// ---------------------------------------------------------
// 4. USER JOURNEY INDEX
// ---------------------------------------------------------

struct Journey {
    std::map<Stage, long long> firstOccurrence;
    std::set<Stage> observed;
};

class JourneyIndex {
private:
    std::unordered_map<std::string, Journey> journeys;

public:
    explicit JourneyIndex(const std::vector<Event>& events) {
        for (const auto& event : events) {
            auto& journey = journeys[event.userId];

            journey.observed.insert(event.stage);

            auto it = journey.firstOccurrence.find(event.stage);

            if (it == journey.firstOccurrence.end()) {
                journey.firstOccurrence[event.stage] = event.timestamp;
            } else {
                it->second = std::min(
                    it->second,
                    event.timestamp
                );
            }
        }
    }

    std::size_t reachedStages(const std::string& userId) const {
        auto it = journeys.find(userId);

        if (it == journeys.end()) return 0;

        long long previousTime = -1;
        std::size_t reached = 0;

        for (Stage stage : STAGES) {
            auto timestamp = it->second.firstOccurrence.find(stage);

            if (timestamp == it->second.firstOccurrence.end()) {
                break;
            }

            if (
                reached > 0 &&
                timestamp->second < previousTime
            ) {
                break;
            }

            previousTime = timestamp->second;
            ++reached;
        }

        return reached;
    }

    bool hasVisited(const std::string& userId) const {
        auto it = journeys.find(userId);

        return it != journeys.end() &&
               it->second.observed.count(Stage::Visit);
    }

    const std::unordered_map<std::string, Journey>& all() const {
        return journeys;
    }
};


// ---------------------------------------------------------
// 5. FUNNEL GOVERNANCE ENGINE
// ---------------------------------------------------------

class FunnelEngine {
public:
    FunnelReport analyze(const std::vector<Event>& events) const {
        JourneyIndex index(events);

        FunnelReport report;

        std::vector<std::string> visitors;

        for (const auto& [userId, journey] : index.all()) {
            if (index.hasVisited(userId)) {
                visitors.push_back(userId);
            }
        }

        report.visitors = visitors.size();

        std::size_t previous = report.visitors;

        for (std::size_t i = 0; i < STAGES.size(); ++i) {
            std::size_t reached = 0;

            for (const auto& userId : visitors) {
                if (index.reachedStages(userId) > i) {
                    ++reached;
                }
            }

            const double rate = safeRate(reached, previous);

            report.steps.push_back({
                stageName(STAGES[i]),
                reached,
                previous,
                rate,
                previous == 0 ? 0.0 : 100.0 - rate
            });

            previous = reached;
        }

        report.conversions = report.steps.back().users;

        report.overallRate = safeRate(
            report.conversions,
            report.visitors
        );

        return report;
    }
};


// ---------------------------------------------------------
// 6. ATTRIBUTION ENGINE
// ---------------------------------------------------------

class AttributionEngine {
public:
    std::map<std::string, ChannelMetrics> analyze(
        const std::vector<Event>& events
    ) const {

        std::map<std::string, ChannelMetrics> result;

        std::map<std::string, std::set<std::string>> visitors;
        std::map<std::string, std::set<std::string>> buyers;

        for (const auto& event : events) {
            auto& metric = result[event.channel];

            if (event.stage == Stage::Visit) {
                visitors[event.channel].insert(event.userId);
            }

            if (event.stage == Stage::Purchase) {
                buyers[event.channel].insert(event.userId);
                metric.revenue += event.revenue;
            }
        }

        for (auto& [channel, metric] : result) {
            metric.visitors = visitors[channel].size();

            for (const auto& user : buyers[channel]) {
                if (visitors[channel].count(user)) {
                    ++metric.conversions;
                }
            }
        }

        return result;
    }
};


// ---------------------------------------------------------
// 7. A/B EXPERIMENT EVALUATION
// ---------------------------------------------------------

struct ExperimentResult {
    double controlRate;
    double treatmentRate;
    double absoluteLift;
    double relativeLift;
    double zScore;
    double pValue;
    bool significant;
};

double normalCDF(double x) {
    return 0.5 * std::erfc(-x / std::sqrt(2.0));
}

ExperimentResult evaluateExperiment(
    std::size_t controlConversions,
    std::size_t controlUsers,
    std::size_t treatmentConversions,
    std::size_t treatmentUsers
) {
    if (
        controlUsers == 0 ||
        treatmentUsers == 0 ||
        controlConversions > controlUsers ||
        treatmentConversions > treatmentUsers
    ) {
        throw std::invalid_argument("Invalid experiment sample");
    }

    const double p1 =
        static_cast<double>(controlConversions) / controlUsers;

    const double p2 =
        static_cast<double>(treatmentConversions) / treatmentUsers;

    const double pooled =
        static_cast<double>(
            controlConversions + treatmentConversions
        ) / (controlUsers + treatmentUsers);

    const double standardError = std::sqrt(
        pooled * (1.0 - pooled) *
        (1.0 / controlUsers + 1.0 / treatmentUsers)
    );

    const double z = standardError == 0.0
        ? 0.0
        : (p2 - p1) / standardError;

    const double pValue =
        2.0 * (1.0 - normalCDF(std::abs(z)));

    const double relativeLift = p1 == 0.0
        ? 0.0
        : ((p2 - p1) / p1) * 100.0;

    return {
        p1 * 100.0,
        p2 * 100.0,
        (p2 - p1) * 100.0,
        relativeLift,
        z,
        pValue,
        pValue < 0.05
    };
}


// ---------------------------------------------------------
// 8. BOTTLENECK DETECTION
// ---------------------------------------------------------

std::string findBottleneck(const FunnelReport& report) {
    if (report.steps.empty()) {
        throw std::invalid_argument("Empty funnel report");
    }

    const auto worst = std::max_element(
        report.steps.begin(),
        report.steps.end(),
        [](const FunnelStep& a, const FunnelStep& b) {
            return a.dropOffRate < b.dropOffRate;
        }
    );

    return worst->stage;
}


// ---------------------------------------------------------
// 9. SAMPLE DATA
// ---------------------------------------------------------

std::vector<Event> sampleEvents() {
    const std::vector<std::tuple<
        std::string,
        std::vector<Stage>,
        std::string,
        double
    >> records = {
        {"u1", STAGES, "organic", 2500},
        {"u2", {Stage::Visit, Stage::ProductView,
                Stage::AddToCart, Stage::Checkout}, "paid", 0},
        {"u3", {Stage::Visit, Stage::ProductView,
                Stage::AddToCart, Stage::Purchase}, "organic", 1800},
        {"u4", {Stage::Visit, Stage::ProductView}, "social", 0},
        {"u5", STAGES, "paid", 3200},
        {"u6", {Stage::Visit, Stage::ProductView}, "social", 0},
        {"u7", STAGES, "organic", 1500},
        {"u8", {Stage::Visit, Stage::ProductView,
                Stage::AddToCart}, "paid", 0},
        {"u9", {Stage::Visit}, "referral", 0},
        {"u10", STAGES, "organic", 4100}
    };

    std::vector<Event> events;

    long long base = 1000000;

    for (std::size_t i = 0; i < records.size(); ++i) {
        const auto& [userId, stages, channel, revenue] = records[i];

        for (std::size_t j = 0; j < stages.size(); ++j) {
            events.push_back({
                userId + "-" + std::to_string(j),
                userId,
                stages[j],
                base + static_cast<long long>(i * 20 + j * 5),
                channel,
                channel == "organic" ? "seo" : channel,
                stages[j] == Stage::Purchase ? revenue : 0.0
            });
        }
    }

    return events;
}


// ---------------------------------------------------------
// 10. REPORTING
// ---------------------------------------------------------

void printReport(
    const FunnelReport& report,
    const std::map<std::string, ChannelMetrics>& channels
) {
    std::cout << std::fixed << std::setprecision(2);

    std::cout << "\nCONVERSION FUNNEL\n";
    std::cout << "Visitors: " << report.visitors << "\n";
    std::cout << "Conversions: " << report.conversions << "\n";
    std::cout << "Overall conversion: "
              << report.overallRate << "%\n";

    std::cout << "\nSTAGE PERFORMANCE\n";

    for (const auto& step : report.steps) {
        std::cout
            << std::setw(15) << std::left << step.stage
            << " Users: " << step.users
            << " Conversion: " << step.conversionRate
            << "% Drop-off: " << step.dropOffRate
            << "%\n";
    }

    std::cout << "\nCHANNEL PERFORMANCE\n";

    for (const auto& [name, metric] : channels) {
        std::cout
            << name
            << " | Visitors: " << metric.visitors
            << " | Conversions: " << metric.conversions
            << " | Rate: " << metric.conversionRate()
            << "% | Revenue: " << metric.revenue
            << "\n";
    }
}


// ---------------------------------------------------------
// 11. MAIN
// ---------------------------------------------------------

int main() {
    try {
        EventStore store;

        const auto events = sampleEvents();

        store.addBatch(events);

        // Duplicate event rejection.
        if (store.add(events.front())) {
            throw std::runtime_error("Deduplication failed");
        }

        FunnelEngine funnelEngine;
        AttributionEngine attributionEngine;

        const FunnelReport report = funnelEngine.analyze(
            store.all()
        );

        const auto channels = attributionEngine.analyze(
            store.all()
        );

        printReport(report, channels);

        std::cout << "\nFUNNEL BOTTLENECK\n";
        std::cout << findBottleneck(report) << "\n";

        const auto experiment = evaluateExperiment(
            120, 2000, 150, 2000
        );

        std::cout << "\nA/B TEST\n";
        std::cout << "Control: "
                  << experiment.controlRate << "%\n";

        std::cout << "Treatment: "
                  << experiment.treatmentRate << "%\n";

        std::cout << "Absolute lift: "
                  << experiment.absoluteLift << " percentage points\n";

        std::cout << "Relative lift: "
                  << experiment.relativeLift << "%\n";

        std::cout << "P-value: "
                  << experiment.pValue << "\n";

        std::cout << "Statistically significant: "
                  << (experiment.significant ? "Yes" : "No")
                  << "\n";

        // Correctness assertions.
        if (report.visitors != 10 ||
            report.conversions != 4) {
            throw std::runtime_error("Funnel validation failed");
        }

        if (safeRate(25, 100) != 25.0) {
            throw std::runtime_error("Metric validation failed");
        }

        if (findBottleneck(report).empty()) {
            throw std::runtime_error("Bottleneck validation failed");
        }

        try {
            safeRate(10, 5);
            throw std::runtime_error(
                "Invalid conversion ratio was accepted"
            );
        } catch (const std::invalid_argument&) {
            // Expected validation failure.
        }

        std::cout << "\nAll validation checks passed.\n";

    } catch (const std::exception& error) {
        std::cerr << "Execution error: "
                  << error.what() << "\n";

        return 1;
    }

    return 0;
}
