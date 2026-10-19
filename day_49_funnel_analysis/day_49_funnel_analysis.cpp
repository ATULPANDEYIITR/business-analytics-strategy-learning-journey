#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

enum class Stage {
    Landing,
    Product,
    Cart,
    Checkout,
    Purchase
};

string stageName(Stage stage) {
    switch (stage) {
        case Stage::Landing: return "Visited Landing Page";
        case Stage::Product: return "Viewed Product";
        case Stage::Cart: return "Added to Cart";
        case Stage::Checkout: return "Started Checkout";
        case Stage::Purchase: return "Purchased";
    }

    throw invalid_argument("Unknown funnel stage");
}

int stageOrder(Stage stage) {
    return static_cast<int>(stage);
}

struct Event {
    Stage stage;
    int minute;
};

struct Pull {
    string customerId;
    string segment;
    vector<Event> events;
    double revenue = 0.0;

    bool reached(Stage stage) const {
        return any_of(
            events.begin(),
            events.end(),
            [stage](const Event& event) {
                return event.stage == stage;
            }
        );
    }

    optional<int> timestamp(Stage stage) const {
        for (const auto& event : events) {
            if (event.stage == stage) {
                return event.minute;
            }
        }

        return nullopt;
    }
};

struct StageMetric {
    Stage stage;
    size_t users = 0;
    optional<double> conversionFromPrevious;
    optional<double> dropOff;
    double conversionFromEntry = 0.0;
};

class FunnelValidation {
public:
    static void validateJourney(const Pull& journey) {
        if (journey.customerId.empty()) {
            throw invalid_argument("Customer ID cannot be empty.");
        }

        if (journey.segment.empty()) {
            throw invalid_argument("Customer segment cannot be empty.");
        }

        if (journey.revenue < 0.0) {
            throw invalid_argument("Revenue cannot be negative.");
        }

        set<int> seenStages;
        int previousOrder = -1;
        int previousMinute = -1;

        for (const auto& event : journey.events) {
            const int order = stageOrder(event.stage);

            if (!seenStages.insert(order).second) {
                throw invalid_argument(
                    "A customer cannot record the same funnel stage twice."
                );
            }

            if (order <= previousOrder) {
                throw invalid_argument(
                    "Funnel stages must occur in increasing order."
                );
            }

            if (event.minute < previousMinute) {
                throw invalid_argument(
                    "Event timestamps cannot move backwards."
                );
            }

            previousOrder = order;
            previousMinute = event.minute;
        }
    }
};

class RepositoryGovernanceCaseStudy {
private:
    vector<Pull> journeys;
    const vector<Stage> stages{
        Stage::Landing,
        Stage::Product,
        Stage::Cart,
        Stage::Checkout,
        Stage::Purchase
    };

public:
    void addJourney(Pull journey) {
        FunnelValidation::validateJourney(journey);

        const bool duplicate = any_of(
            journeys.begin(),
            journeys.end(),
            [&](const Pull& existing) {
                return existing.customerId == journey.customerId;
            }
        );

        if (duplicate) {
            throw invalid_argument(
                "Duplicate customer journey: " + journey.customerId
            );
        }

        journeys.push_back(move(journey));
    }

    vector<const Pull*> usersAt(Stage stage) const {
        vector<const Pull*> result;

        for (const auto& journey : journeys) {
            if (journey.reached(stage)) {
                result.push_back(&journey);
            }
        }

        return result;
    }

    vector<StageMetric> calculateStageMetrics() const {
        vector<StageMetric> metrics;

        if (journeys.empty()) {
            return metrics;
        }

        const size_t entryUsers = journeys.size();
        size_t previousUsers = 0;

        for (size_t index = 0; index < stages.size(); ++index) {
            const Stage stage = stages[index];
            const auto currentUsers = usersAt(stage);
            const size_t currentCount = currentUsers.size();

            StageMetric metric;
            metric.stage = stage;
            metric.users = currentCount;
            metric.conversionFromEntry =
                static_cast<double>(currentCount) /
                static_cast<double>(entryUsers);

            if (index > 0) {
                const double conversion =
                    previousUsers == 0
                        ? 0.0
                        : static_cast<double>(currentCount) /
                          static_cast<double>(previousUsers);

                metric.conversionFromPrevious = conversion;
                metric.dropOff = 1.0 - conversion;
            }

            metrics.push_back(metric);
            previousUsers = currentCount;
        }

        return metrics;
    }

    map<string, tuple<size_t, size_t, double>> segmentMetrics() const {
        map<string, vector<const Pull*>> grouped;

        for (const auto& journey : journeys) {
            grouped[journey.segment].push_back(&journey);
        }

        map<string, tuple<size_t, size_t, double>> result;

        for (const auto& [segment, segmentJourneys] : grouped) {
            size_t converters = 0;
            double revenue = 0.0;

            for (const Pull* journey : segmentJourneys) {
                if (journey->reached(Stage::Purchase)) {
                    ++converters;
                    revenue += journey->revenue;
                }
            }

            result[segment] = {
                segmentJourneys.size(),
                converters,
                revenue
            };
        }

        return result;
    }

    optional<StageMetric> largestDropOff() const {
        const auto metrics = calculateStageMetrics();

        optional<StageMetric> largest;

        for (const auto& metric : metrics) {
            if (!metric.dropOff.has_value()) {
                continue;
            }

            if (!largest.has_value() ||
                metric.dropOff.value() > largest->dropOff.value()) {
                largest = metric;
            }
        }

        return largest;
    }

    optional<double> medianTimeToConversion() const {
        vector<double> durations;

        for (const auto& journey : journeys) {
            const auto start = journey.timestamp(Stage::Landing);
            const auto end = journey.timestamp(Stage::Purchase);

            if (start.has_value() && end.has_value()) {
                durations.push_back(
                    static_cast<double>(end.value() - start.value())
                );
            }
        }

        if (durations.empty()) {
            return nullopt;
        }

        sort(durations.begin(), durations.end());

        const size_t middle = durations.size() / 2;

        if (durations.size() % 2 == 0) {
            return (durations[middle - 1] + durations[middle]) / 2.0;
        }

        return durations[middle];
    }

    map<string, size_t> observedPaths() const {
        map<string, size_t> paths;

        for (const auto& journey : journeys) {
            string path;

            for (const auto& stage : stages) {
                if (journey.reached(stage)) {
                    if (!path.empty()) {
                        path += " -> ";
                    }

                    path += stageName(stage);
                }
            }

            ++paths[path];
        }

        return paths;
    }

    void printReport() const {
        cout << "\nFUNNEL ANALYSIS\n";
        cout << string(78, '=') << '\n';

        for (const auto& metric : calculateStageMetrics()) {
            cout << left
                 << setw(24) << stageName(metric.stage)
                 << " users=" << setw(3) << metric.users
                 << " entry=" << fixed << setprecision(1)
                 << metric.conversionFromEntry * 100.0 << "%";

            if (metric.conversionFromPrevious.has_value()) {
                cout << " previous="
                     << metric.conversionFromPrevious.value() * 100.0
                     << "% dropOff="
                     << metric.dropOff.value() * 100.0
                     << "%";
            }

            cout << '\n';
        }

        const auto largest = largestDropOff();

        if (largest.has_value()) {
            cout << "\nLargest drop-off: "
                 << stageName(largest->stage)
                 << " (" << largest->dropOff.value() * 100.0
                 << "%)\n";
        }

        cout << "\nSEGMENT PERFORMANCE\n";
        cout << string(78, '-') << '\n';

        for (const auto& [segment, values] : segmentMetrics()) {
            const auto [users, converters, revenue] = values;

            const double rate =
                users == 0
                    ? 0.0
                    : static_cast<double>(converters) /
                      static_cast<double>(users);

            cout << left
                 << setw(10) << segment
                 << " users=" << setw(3) << users
                 << " converters=" << setw(3) << converters
                 << " conversion=" << fixed << setprecision(1)
                 << rate * 100.0
                 << "% revenue=$"
                 << setprecision(2) << revenue
                 << '\n';
        }

        cout << "\nTIME TO CONVERSION\n";
        cout << string(78, '-') << '\n';

        const auto median = medianTimeToConversion();

        if (median.has_value()) {
            cout << "Median time: "
                 << fixed << setprecision(1)
                 << median.value()
                 << " minutes\n";
        } else {
            cout << "No completed journeys are available.\n";
        }

        cout << "\nCUSTOMER PATHS\n";
        cout << string(78, '-') << '\n';

        for (const auto& [path, count] : observedPaths()) {
            cout << count << "  " << path << '\n';
        }
    }
};

Pull makeJourney(
    const string& customerId,
    const string& segment,
    initializer_list<Event> events,
    double revenue = 0.0
) {
    return Pull{
        customerId,
        segment,
        vector<Event>(events),
        revenue
    };
}

int main() {
    try {
        RepositoryGovernanceCaseStudy system;

        system.addJourney(
            makeJourney(
                "C001",
                "mobile",
                {
                    {Stage::Landing, 0},
                    {Stage::Product, 4},
                    {Stage::Cart, 9},
                    {Stage::Checkout, 15},
                    {Stage::Purchase, 23}
                },
                129.0
            )
        );

        system.addJourney(
            makeJourney(
                "C002",
                "mobile",
                {
                    {Stage::Landing, 1},
                    {Stage::Product, 6},
                    {Stage::Cart, 12},
                    {Stage::Checkout, 21}
                }
            )
        );

        system.addJourney(
            makeJourney(
                "C003",
                "desktop",
                {
                    {Stage::Landing, 2},
                    {Stage::Product, 5},
                    {Stage::Cart, 14},
                    {Stage::Checkout, 20},
                    {Stage::Purchase, 32}
                },
                249.0
            )
        );

        system.addJourney(
            makeJourney(
                "C004",
                "desktop",
                {
                    {Stage::Landing, 3},
                    {Stage::Product, 8}
                }
            )
        );

        system.addJourney(
            makeJourney(
                "C005",
                "mobile",
                {
                    {Stage::Landing, 10},
                    {Stage::Product, 14},
                    {Stage::Cart, 19}
                }
            )
        );

        system.addJourney(
            makeJourney(
                "C006",
                "desktop",
                {
                    {Stage::Landing, 11},
                    {Stage::Product, 16},
                    {Stage::Cart, 22},
                    {Stage::Checkout, 30},
                    {Stage::Purchase, 41}
                },
                89.0
            )
        );

        system.addJourney(
            makeJourney(
                "C007",
                "tablet",
                {
                    {Stage::Landing, 13},
                    {Stage::Product, 18},
                    {Stage::Cart, 26},
                    {Stage::Checkout, 40}
                }
            )
        );

        system.addJourney(
            makeJourney(
                "C008",
                "tablet",
                {
                    {Stage::Landing, 15},
                    {Stage::Product, 21}
                }
            )
        );

        system.addJourney(
            makeJourney(
                "C009",
                "mobile",
                {
                    {Stage::Landing, 18},
                    {Stage::Product, 23},
                    {Stage::Cart, 31},
                    {Stage::Checkout, 37},
                    {Stage::Purchase, 48}
                },
                159.0
            )
        );

        system.addJourney(
            makeJourney(
                "C010",
                "desktop",
                {
                    {Stage::Landing, 20},
                    {Stage::Product, 24},
                    {Stage::Cart, 30}
                }
            )
        );

        system.printReport();

        cout << "\nVALIDATION CASE\n";
        cout << string(78, '=') << '\n';

        try {
            system.addJourney(
                makeJourney(
                    "INVALID",
                    "mobile",
                    {
                        {Stage::Product, 50},
                        {Stage::Landing, 55}
                    }
                )
            );
        } catch (const exception& error) {
            cout << "Rejected invalid journey: "
                 << error.what() << '\n';
        }
    } catch (const exception& error) {
        cerr << "Funnel analysis failed: "
             << error.what() << '\n';
        return 1;
    }

    return 0;
}
