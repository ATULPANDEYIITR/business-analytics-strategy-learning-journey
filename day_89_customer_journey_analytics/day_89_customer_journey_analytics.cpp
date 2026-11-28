#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

// ============================================================
// 1. DOMAIN MODEL
// ============================================================

enum class EventType {
    Impression,
    Click,
    PageView,
    ProductView,
    Search,
    AddToCart,
    Checkout,
    Purchase,
    Signup,
    Support
};

enum class Channel {
    OrganicSearch,
    PaidSearch,
    Social,
    Email,
    Direct,
    Referral,
    Display
};

enum class Consent {
    Granted,
    Denied,
    Unknown
};

enum class JourneyStage {
    Awareness,
    Consideration,
    Conversion,
    Retention
};

string toString(EventType type) {
    switch (type) {
        case EventType::Impression: return "impression";
        case EventType::Click: return "click";
        case EventType::PageView: return "page_view";
        case EventType::ProductView: return "product_view";
        case EventType::Search: return "search";
        case EventType::AddToCart: return "add_to_cart";
        case EventType::Checkout: return "checkout";
        case EventType::Purchase: return "purchase";
        case EventType::Signup: return "signup";
        case EventType::Support: return "support";
    }

    throw invalid_argument("Unknown event type");
}

string toString(Channel channel) {
    switch (channel) {
        case Channel::OrganicSearch: return "organic_search";
        case Channel::PaidSearch: return "paid_search";
        case Channel::Social: return "social";
        case Channel::Email: return "email";
        case Channel::Direct: return "direct";
        case Channel::Referral: return "referral";
        case Channel::Display: return "display";
    }

    throw invalid_argument("Unknown channel");
}

string toString(JourneyStage stage) {
    switch (stage) {
        case JourneyStage::Awareness: return "awareness";
        case JourneyStage::Consideration: return "consideration";
        case JourneyStage::Conversion: return "conversion";
        case JourneyStage::Retention: return "retention";
    }

    throw invalid_argument("Unknown stage");
}

// ============================================================
// 2. CUSTOMER AND EVENT STRUCTURES
// ============================================================

struct Customer {
    string id;
    Consent consent;
    string registrationMonth;
};

struct Event {
    string id;
    string customerId;
    string sessionId;
    EventType type;
    Channel channel;
    long long timestamp;
    string page;
    double value = 0.0;
};

struct Session {
    string customerId;
    string sessionId;
    long long start;
    long long end;
    int eventCount;
    Channel entryChannel;
    string exitPage;

    double durationSeconds() const {
        return static_cast<double>(end - start);
    }
};

// ============================================================
// 3. EVENT VALIDATION
// ============================================================

class EventValidator {
public:
    static void validate(const Event& event) {
        if (event.id.empty() ||
            event.customerId.empty() ||
            event.sessionId.empty()) {
            throw invalid_argument("Missing event identifiers");
        }

        if (event.page.empty() || event.page.size() > 500) {
            throw invalid_argument("Invalid page identifier");
        }

        if (event.timestamp < 0) {
            throw invalid_argument("Invalid event timestamp");
        }

        if (!isfinite(event.value) || event.value < 0) {
            throw invalid_argument("Invalid monetary value");
        }

        if (event.type == EventType::Purchase && event.value <= 0) {
            throw invalid_argument("Purchase must have positive value");
        }
    }
};

// ============================================================
// 4. CUSTOMER IDENTITY REGISTRY
// ============================================================

class IdentityRegistry {
private:
    unordered_map<string, string> identifierToCustomer;

public:
    void associate(
        const string& identifier,
        const string& customerId
    ) {
        if (identifier.empty() || customerId.empty()) {
            throw invalid_argument("Invalid identity association");
        }

        auto it = identifierToCustomer.find(identifier);

        if (it != identifierToCustomer.end() &&
            it->second != customerId) {
            throw runtime_error("Identity collision detected");
        }

        identifierToCustomer[identifier] = customerId;
    }

    string resolve(const string& identifier) const {
        auto it = identifierToCustomer.find(identifier);

        return it == identifierToCustomer.end()
            ? ""
            : it->second;
    }

    void eraseCustomer(const string& customerId) {
        for (auto it = identifierToCustomer.begin();
             it != identifierToCustomer.end();) {

            if (it->second == customerId) {
                it = identifierToCustomer.erase(it);
            } else {
                ++it;
            }
        }
    }
};

// ============================================================
// 5. EVENT COLLECTION AND PRIVACY
// ============================================================

class EventRepository {
private:
    unordered_map<string, Customer> customers;
    unordered_map<string, Event> events;
    unordered_map<string, vector<string>> customerEventIds;

public:
    void registerCustomer(const Customer& customer) {
        if (customer.id.empty()) {
            throw invalid_argument("Customer ID is required");
        }

        customers[customer.id] = customer;
    }

    void addEvent(const Event& event) {
        EventValidator::validate(event);

        if (events.count(event.id)) {
            return;
        }

        auto customer = customers.find(event.customerId);

        if (customer == customers.end()) {
            throw runtime_error("Unknown customer");
        }

        if (customer->second.consent != Consent::Granted) {
            throw runtime_error("Analytics consent not granted");
        }

        events.emplace(event.id, event);
        customerEventIds[event.customerId].push_back(event.id);
    }

    vector<Event> getEvents() const {
        vector<Event> result;

        result.reserve(events.size());

        for (const auto& entry : events) {
            result.push_back(entry.second);
        }

        sort(result.begin(), result.end(),
             [](const Event& a, const Event& b) {
                 if (a.customerId != b.customerId) {
                     return a.customerId < b.customerId;
                 }

                 return a.timestamp < b.timestamp;
             });

        return result;
    }

    vector<Event> getCustomerEvents(
        const string& customerId
    ) const {
        vector<Event> result;

        auto it = customerEventIds.find(customerId);

        if (it == customerEventIds.end()) {
            return result;
        }

        for (const string& id : it->second) {
            auto event = events.find(id);

            if (event != events.end()) {
                result.push_back(event->second);
            }
        }

        sort(result.begin(), result.end(),
             [](const Event& a, const Event& b) {
                 return a.timestamp < b.timestamp;
             });

        return result;
    }

    void eraseCustomer(const string& customerId) {
        auto it = customerEventIds.find(customerId);

        if (it != customerEventIds.end()) {
            for (const string& id : it->second) {
                events.erase(id);
            }

            customerEventIds.erase(it);
        }

        customers.erase(customerId);
    }

    size_t customerCount() const {
        return customers.size();
    }

    size_t eventCount() const {
        return events.size();
    }
};

// ============================================================
// 6. JOURNEY CLASSIFICATION
// ============================================================

class JourneyClassifier {
public:
    static JourneyStage classify(EventType type) {
        switch (type) {
            case EventType::Impression:
            case EventType::Click:
            case EventType::PageView:
                return JourneyStage::Awareness;

            case EventType::Search:
            case EventType::ProductView:
            case EventType::AddToCart:
                return JourneyStage::Consideration;

            case EventType::Checkout:
            case EventType::Purchase:
                return JourneyStage::Conversion;

            case EventType::Signup:
            case EventType::Support:
                return JourneyStage::Retention;
        }

        throw invalid_argument("Unknown event type");
    }
};

// ============================================================
// 7. SESSIONIZATION ENGINE
// ============================================================

class SessionAnalyzer {
private:
    long long inactivityThreshold;

public:
    explicit SessionAnalyzer(long long timeoutSeconds = 1800)
        : inactivityThreshold(timeoutSeconds) {

        if (timeoutSeconds <= 0) {
            throw invalid_argument("Invalid session timeout");
        }
    }

    vector<Session> analyze(vector<Event> events) const {
        sort(events.begin(), events.end(),
             [](const Event& a, const Event& b) {
                 if (a.customerId != b.customerId) {
                     return a.customerId < b.customerId;
                 }

                 return a.timestamp < b.timestamp;
             });

        vector<Session> sessions;

        for (const Event& event : events) {
            bool newSession = sessions.empty();

            if (!newSession) {
                const Session& previous = sessions.back();

                newSession =
                    previous.customerId != event.customerId ||
                    previous.sessionId != event.sessionId ||
                    event.timestamp - previous.end > inactivityThreshold;
            }

            if (newSession) {
                sessions.push_back({
                    event.customerId,
                    event.sessionId,
                    event.timestamp,
                    event.timestamp,
                    1,
                    event.channel,
                    event.page
                });
            } else {
                Session& current = sessions.back();

                current.end = event.timestamp;
                current.eventCount++;
                current.exitPage = event.page;
            }
        }

        return sessions;
    }
};

// ============================================================
// 8. FUNNEL ANALYSIS
// ============================================================

class FunnelAnalyzer {
private:
    vector<EventType> stages = {
        EventType::PageView,
        EventType::ProductView,
        EventType::AddToCart,
        EventType::Checkout,
        EventType::Purchase
    };

public:
    struct FunnelResult {
        EventType stage;
        int customers;
        double conversionRate;
        double dropOff;
    };

    vector<FunnelResult> analyze(
        const vector<Event>& events
    ) const {

        map<string, vector<Event>> journeys;

        for (const Event& event : events) {
            journeys[event.customerId].push_back(event);
        }

        vector<int> counts(stages.size(), 0);

        for (auto& [customerId, journey] : journeys) {
            sort(journey.begin(), journey.end(),
                 [](const Event& a, const Event& b) {
                     return a.timestamp < b.timestamp;
                 });

            size_t next = 0;

            for (const Event& event : journey) {
                if (event.type == stages[next]) {
                    counts[next]++;

                    next++;

                    if (next == stages.size()) {
                        break;
                    }
                }
            }
        }

        vector<FunnelResult> results;

        for (size_t i = 0; i < stages.size(); ++i) {
            double previous = i == 0
                ? counts[i]
                : counts[i - 1];

            double conversion = previous > 0
                ? counts[i] / previous
                : 0.0;

            double dropOff = i == 0 || previous == 0
                ? 0.0
                : 1.0 - conversion;

            results.push_back({
                stages[i],
                counts[i],
                conversion,
                dropOff
            });
        }

        return results;
    }
};

// ============================================================
// 9. ATTRIBUTION MODELS
// ============================================================

enum class AttributionModel {
    FirstTouch,
    LastTouch,
    Linear,
    PositionBased
};

class AttributionEngine {
public:
    static map<Channel, double> calculate(
        vector<Event> events,
        AttributionModel model
    ) {
        map<Channel, double> credits;

        if (events.empty()) {
            return credits;
        }

        sort(events.begin(), events.end(),
             [](const Event& a, const Event& b) {
                 return a.timestamp < b.timestamp;
             });

        if (model == AttributionModel::FirstTouch) {
            credits[events.front().channel] = 1.0;
        }

        else if (model == AttributionModel::LastTouch) {
            credits[events.back().channel] = 1.0;
        }

        else if (model == AttributionModel::Linear) {
            double credit = 1.0 / events.size();

            for (const Event& event : events) {
                credits[event.channel] += credit;
            }
        }

        else if (model == AttributionModel::PositionBased) {
            if (events.size() == 1) {
                credits[events.front().channel] = 1.0;
            } else {
                credits[events.front().channel] += 0.4;
                credits[events.back().channel] += 0.4;

                size_t middleCount = events.size() - 2;

                if (middleCount > 0) {
                    double middleCredit = 0.2 / middleCount;

                    for (size_t i = 1; i + 1 < events.size(); ++i) {
                        credits[events[i].channel] += middleCredit;
                    }
                }
            }
        }

        return credits;
    }

    static map<Channel, double> allocateRevenue(
        double revenue,
        const map<Channel, double>& credits
    ) {
        if (!isfinite(revenue) || revenue < 0) {
            throw invalid_argument("Invalid revenue");
        }

        double total = 0;

        for (const auto& [channel, credit] : credits) {
            if (!isfinite(credit) || credit < 0) {
                throw invalid_argument("Invalid attribution credit");
            }

            total += credit;
        }

        if (credits.empty() || abs(total - 1.0) > 1e-9) {
            throw invalid_argument("Attribution weights must total one");
        }

        map<Channel, double> result;

        for (const auto& [channel, credit] : credits) {
            result[channel] = revenue * credit;
        }

        return result;
    }
};

// ============================================================
// 10. BEHAVIORAL SEGMENTATION
// ============================================================

enum class Segment {
    Visitor,
    EngagedVisitor,
    CartAbandoner,
    ConvertedCustomer,
    RepeatCustomer,
    SupportEngaged
};

string toString(Segment segment) {
    switch (segment) {
        case Segment::Visitor: return "visitor";
        case Segment::EngagedVisitor: return "engaged_visitor";
        case Segment::CartAbandoner: return "cart_abandoner";
        case Segment::ConvertedCustomer: return "converted_customer";
        case Segment::RepeatCustomer: return "repeat_customer";
        case Segment::SupportEngaged: return "support_engaged";
    }

    throw invalid_argument("Unknown segment");
}

struct CustomerBehavior {
    int eventCount = 0;
    int purchases = 0;
    int cartEvents = 0;
    int supportEvents = 0;
    double revenue = 0;
};

class BehaviorAnalyzer {
public:
    static map<string, Segment> segmentCustomers(
        const vector<Event>& events
    ) {
        map<string, CustomerBehavior> profiles;

        for (const Event& event : events) {
            auto& profile = profiles[event.customerId];

            profile.eventCount++;

            if (event.type == EventType::Purchase) {
                profile.purchases++;
                profile.revenue += event.value;
            }

            if (event.type == EventType::AddToCart) {
                profile.cartEvents++;
            }

            if (event.type == EventType::Support) {
                profile.supportEvents++;
            }
        }

        map<string, Segment> result;

        for (const auto& [customerId, profile] : profiles) {
            Segment segment = Segment::Visitor;

            if (profile.supportEvents > 0) {
                segment = Segment::SupportEngaged;
            } else if (profile.purchases > 1) {
                segment = Segment::RepeatCustomer;
            } else if (profile.purchases == 1) {
                segment = Segment::ConvertedCustomer;
            } else if (profile.cartEvents > 0) {
                segment = Segment::CartAbandoner;
            } else if (profile.eventCount > 3) {
                segment = Segment::EngagedVisitor;
            }

            result[customerId] = segment;
        }

        return result;
    }

    static map<string, int> popularPages(
        const vector<Event>& events
    ) {
        map<string, int> pages;

        for (const Event& event : events) {
            if (event.type == EventType::PageView) {
                pages[event.page]++;
            }
        }

        return pages;
    }
};

// ============================================================
// 11. REVENUE AND CHANNEL REPORTING
// ============================================================

struct ChannelMetrics {
    int touchpoints = 0;
    set<string> customers;
    int purchases = 0;
    double revenue = 0;
};

class ChannelAnalyzer {
public:
    static map<Channel, ChannelMetrics> analyze(
        const vector<Event>& events
    ) {
        map<Channel, ChannelMetrics> metrics;

        for (const Event& event : events) {
            auto& metric = metrics[event.channel];

            metric.touchpoints++;
            metric.customers.insert(event.customerId);

            if (event.type == EventType::Purchase) {
                metric.purchases++;
                metric.revenue += event.value;
            }
        }

        return metrics;
    }
};

// ============================================================
// 12. REPORTING ENGINE
// ============================================================

class AnalyticsEngine {
private:
    const EventRepository& repository;

public:
    explicit AnalyticsEngine(const EventRepository& repo)
        : repository(repo) {}

    void generateReport() const {
        vector<Event> events = repository.getEvents();

        if (events.empty()) {
            cout << "No events available.\n";
            return;
        }

        unordered_set<string> customers;
        double revenue = 0;
        int purchases = 0;

        for (const Event& event : events) {
            customers.insert(event.customerId);

            if (event.type == EventType::Purchase) {
                revenue += event.value;
                purchases++;
            }
        }

        SessionAnalyzer sessionAnalyzer;
        auto sessions = sessionAnalyzer.analyze(events);

        FunnelAnalyzer funnelAnalyzer;
        auto funnel = funnelAnalyzer.analyze(events);

        auto channels = ChannelAnalyzer::analyze(events);

        cout << fixed << setprecision(2);

        cout << "\nCUSTOMER JOURNEY REPORT\n";
        cout << "==============================\n";

        cout << "Events: " << events.size() << "\n";
        cout << "Customers: " << customers.size() << "\n";
        cout << "Sessions: " << sessions.size() << "\n";
        cout << "Purchases: " << purchases << "\n";
        cout << "Revenue: INR " << revenue << "\n";

        cout << "\nCHANNEL PERFORMANCE\n";

        for (const auto& [channel, metric] : channels) {
            cout << toString(channel)
                 << " | events=" << metric.touchpoints
                 << " | customers=" << metric.customers.size()
                 << " | purchases=" << metric.purchases
                 << " | revenue=" << metric.revenue
                 << "\n";
        }

        cout << "\nCONVERSION FUNNEL\n";

        for (const auto& stage : funnel) {
            cout << toString(stage.stage)
                 << " | customers=" << stage.customers
                 << " | conversion=" << stage.conversionRate * 100
                 << "% | drop-off=" << stage.dropOff * 100
                 << "%\n";
        }

        cout << "\nCUSTOMER SEGMENTS\n";

        auto segments = BehaviorAnalyzer::segmentCustomers(events);

        for (const auto& [customerId, segment] : segments) {
            cout << customerId << " -> "
                 << toString(segment) << "\n";
        }
    }
};

// ============================================================
// 13. TESTING AND DEMONSTRATION
// ============================================================

void runTests(EventRepository& repository) {
    if (repository.eventCount() != 17) {
        throw runtime_error("Unexpected event count");
    }

    auto events = repository.getCustomerEvents("C001");

    if (events.size() != 6) {
        throw runtime_error("Customer journey count mismatch");
    }

    auto attribution = AttributionEngine::calculate(
        events,
        AttributionModel::Linear
    );

    double totalCredit = 0;

    for (const auto& [channel, credit] : attribution) {
        totalCredit += credit;
    }

    if (abs(totalCredit - 1.0) > 1e-9) {
        throw runtime_error("Attribution validation failed");
    }

    FunnelAnalyzer analyzer;
    auto funnel = analyzer.analyze(repository.getEvents());

    if (funnel.empty()) {
        throw runtime_error("Funnel analysis failed");
    }

    cout << "\nAll validation tests passed.\n";
}

int main() {
    try {
        EventRepository repository;

        vector<Customer> customers = {
            {"C001", Consent::Granted, "2026-10"},
            {"C002", Consent::Granted, "2026-10"},
            {"C003", Consent::Granted, "2026-10"},
            {"C004", Consent::Granted, "2026-10"},
            {"C005", Consent::Denied, "2026-10"}
        };

        for (const Customer& customer : customers) {
            repository.registerCustomer(customer);
        }

        map<string, vector<tuple<EventType, Channel, int>>> journeys;

        journeys["C001"] = {
            {EventType::Click, Channel::Social, 0},
            {EventType::PageView, Channel::OrganicSearch, 2},
            {EventType::ProductView, Channel::OrganicSearch, 5},
            {EventType::AddToCart, Channel::OrganicSearch, 10},
            {EventType::Checkout, Channel::OrganicSearch, 15},
            {EventType::Purchase, Channel::OrganicSearch, 20}
        };

        journeys["C002"] = {
            {EventType::Click, Channel::PaidSearch, 0},
            {EventType::PageView, Channel::PaidSearch, 3},
            {EventType::ProductView, Channel::PaidSearch, 7},
            {EventType::AddToCart, Channel::PaidSearch, 12}
        };

        journeys["C003"] = {
            {EventType::PageView, Channel::Direct, 0},
            {EventType::ProductView, Channel::Direct, 4},
            {EventType::Checkout, Channel::Direct, 8},
            {EventType::Purchase, Channel::Direct, 12}
        };

        journeys["C004"] = {
            {EventType::Impression, Channel::Display, 0},
            {EventType::PageView, Channel::Email, 3},
            {EventType::ProductView, Channel::Email, 7}
        };

        long long base = 1790845200LL;
        int id = 1;

        for (const auto& [customerId, journey] : journeys) {
            long long dayOffset = stoi(customerId.substr(3)) * 86400LL;

            for (const auto& [type, channel, minute] : journey) {
                Event event{
                    "EV" + to_string(id++),
                    customerId,
                    "SESSION-" + customerId,
                    type,
                    channel,
                    base + dayOffset + minute * 60LL,
                    "/" + toString(type),
                    type == EventType::Purchase ? 1499.0 : 0.0
                };

                repository.addEvent(event);
            }
        }

        AnalyticsEngine engine(repository);
        engine.generateReport();

        cout << "\nMULTI-TOUCH REVENUE ATTRIBUTION\n";

        auto customerEvents = repository.getCustomerEvents("C001");

        auto credits = AttributionEngine::calculate(
            customerEvents,
            AttributionModel::PositionBased
        );

        auto allocation = AttributionEngine::allocateRevenue(
            1499.0,
            credits
        );

        for (const auto& [channel, amount] : allocation) {
            cout << toString(channel)
                 << " -> INR " << amount << "\n";
        }

        runTests(repository);

        // Demonstrate privacy-related customer erasure.
        repository.eraseCustomer("C004");

        cout << "\nEvents after C004 erasure: "
             << repository.eventCount() << "\n";

    } catch (const exception& error) {
        cerr << "Analytics error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
