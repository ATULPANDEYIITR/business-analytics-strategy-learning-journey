#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

struct BusinessItem {
    std::string name;
    std::string category;
    double value;
};

struct ReviewRecord {
    std::string name;
    std::string category;
    double value;
    double share;
    double cumulative_share;
    std::size_t rank;
};

struct GovernancePolicy {
    double target_share = 0.80;
    std::size_t maximum_priority_items = 0;
};

class ParetoEngine {
public:
    explicit ParetoEngine(GovernancePolicy policy)
        : policy_(policy) {
        if (!(policy_.target_share > 0.0 &&
              policy_.target_share <= 1.0)) {
            throw std::invalid_argument(
                "Target share must be in the interval (0, 1]."
            );
        }
    }

    std::vector<ReviewRecord> analyze(
        const std::vector<BusinessItem>& items
    ) const {
        validate(items);

        std::vector<BusinessItem> ordered = items;

        std::sort(
            ordered.begin(),
            ordered.end(),
            [](const BusinessItem& a, const BusinessItem& b) {
                if (a.value != b.value) {
                    return a.value > b.value;
                }
                return a.name < b.name;
            }
        );

        const double total = std::accumulate(
            ordered.begin(),
            ordered.end(),
            0.0,
            [](double sum, const BusinessItem& item) {
                return sum + item.value;
            }
        );

        std::vector<ReviewRecord> results;
        results.reserve(ordered.size());

        double cumulative = 0.0;

        for (std::size_t index = 0; index < ordered.size(); ++index) {
            const auto& item = ordered[index];
            const double share = item.value / total;
            cumulative += share;

            results.push_back({
                item.name,
                item.category,
                item.value,
                share,
                cumulative,
                index + 1
            });
        }

        return results;
    }

    std::vector<ReviewRecord> select_priority_items(
        const std::vector<ReviewRecord>& results
    ) const {
        std::vector<ReviewRecord> selected;
        double cumulative = 0.0;

        for (const auto& record : results) {
            if (policy_.maximum_priority_items != 0 &&
                selected.size() >= policy_.maximum_priority_items) {
                break;
            }

            selected.push_back(record);
            cumulative += record.share;

            if (cumulative >= policy_.target_share) {
                break;
            }
        }

        return selected;
    }

    std::map<std::string, double> category_totals(
        const std::vector<BusinessItem>& items
    ) const {
        std::map<std::string, double> totals;

        for (const auto& item : items) {
            totals[item.category] += item.value;
        }

        return totals;
    }

    static double captured_share(
        const std::vector<ReviewRecord>& records
    ) {
        return std::accumulate(
            records.begin(),
            records.end(),
            0.0,
            [](double total, const ReviewRecord& record) {
                return total + record.share;
            }
        );
    }

private:
    GovernancePolicy policy_;

    static void validate(
        const std::vector<BusinessItem>& items
    ) {
        if (items.empty()) {
            throw std::invalid_argument(
                "At least one business item is required."
            );
        }

        std::unordered_set<std::string> names;
        double total = 0.0;

        for (const auto& item : items) {
            if (item.name.empty()) {
                throw std::invalid_argument(
                    "Business item name cannot be empty."
                );
            }

            if (item.category.empty()) {
                throw std::invalid_argument(
                    "Business item category cannot be empty."
                );
            }

            if (!std::isfinite(item.value) || item.value < 0.0) {
                throw std::invalid_argument(
                    "Business value must be finite and non-negative."
                );
            }

            if (!names.insert(item.name).second) {
                throw std::invalid_argument(
                    "Duplicate business item: " + item.name
                );
            }

            total += item.value;
        }

        if (!std::isfinite(total) || total <= 0.0) {
            throw std::invalid_argument(
                "Total business value must be greater than zero."
            );
        }
    }
};

static void print_report(
    const std::vector<ReviewRecord>& records
) {
    std::cout << "\nPARETO PRIORITIZATION ENGINE\n";
    std::cout << std::string(82, '=') << '\n';

    std::cout << std::left
              << std::setw(7) << "Rank"
              << std::setw(29) << "Business item"
              << std::setw(14) << "Value"
              << std::setw(12) << "Share"
              << std::setw(15) << "Cumulative"
              << '\n';

    std::cout << std::string(82, '-') << '\n';

    for (const auto& record : records) {
        std::cout << std::left
                  << std::setw(7) << record.rank
                  << std::setw(29) << record.name.substr(0, 28)
                  << std::right
                  << std::setw(14) << std::fixed
                  << std::setprecision(2) << record.value
                  << std::setw(11)
                  << std::setprecision(1)
                  << record.share * 100.0 << "%"
                  << std::setw(14)
                  << record.cumulative_share * 100.0 << "%"
                  << '\n';
    }
}

static void print_categories(
    const std::map<std::string, double>& categories
) {
    std::cout << "\nCATEGORY VALUE\n";
    std::cout << std::string(42, '-') << '\n';

    for (const auto& [category, value] : categories) {
        std::cout << std::left
                  << std::setw(28) << category
                  << std::right
                  << std::fixed
                  << std::setprecision(2)
                  << std::setw(12) << value
                  << '\n';
    }
}

static std::vector<BusinessItem> sample_data() {
    return {
        {"Enterprise accounts", "Customers", 420000.0},
        {"SMB accounts", "Customers", 160000.0},
        {"Support tickets", "Operations", 90000.0},
        {"Cloud infrastructure", "Technology", 75000.0},
        {"Marketing campaigns", "Marketing", 60000.0},
        {"Training programs", "People", 40000.0},
        {"Internal tooling", "Technology", 25000.0},
        {"Legacy reporting", "Operations", 15000.0},
        {"Office services", "Operations", 10000.0},
        {"Other requests", "Operations", 5000.0}
    };
}

static void run_tests() {
    const auto data = sample_data();

    ParetoEngine engine({0.80, 0});
    const auto results = engine.analyze(data);

    if (results.size() != data.size()) {
        throw std::runtime_error("Unexpected result count.");
    }

    if (results.front().name != "Enterprise accounts") {
        throw std::runtime_error("Ranking is incorrect.");
    }

    const double total_share =
        ParetoEngine::captured_share(results);

    if (std::abs(total_share - 1.0) > 1e-9) {
        throw std::runtime_error("Shares do not sum to one.");
    }

    bool rejected = false;

    try {
        engine.analyze({
            {"Invalid", "Test", 0.0}
        });
    } catch (const std::invalid_argument&) {
        rejected = true;
    }

    if (!rejected) {
        throw std::runtime_error(
            "Zero-total input should be rejected."
        );
    }

    std::cout << "\nSelf-tests passed.\n";
}

int main() {
    try {
        const auto data = sample_data();

        /*
         * The engine is deliberately independent of presentation.
         * A governance policy can limit how many high-value items
         * receive focused management attention.
         */
        ParetoEngine engine({
            0.80,
            0
        });

        const auto results = engine.analyze(data);
        const auto priority = engine.select_priority_items(results);

        print_report(results);
        print_categories(engine.category_totals(data));

        const double captured =
            ParetoEngine::captured_share(priority);

        std::cout << "\nPriority decision\n";
        std::cout << "-----------------\n";
        std::cout << "Selected items: "
                  << priority.size() << '\n';
        std::cout << "Value captured: "
                  << std::fixed
                  << std::setprecision(1)
                  << captured * 100.0
                  << "%\n";

        std::cout << "Items:\n";
        for (const auto& item : priority) {
            std::cout << "  - " << item.name << '\n';
        }

        run_tests();
    } catch (const std::exception& error) {
        std::cerr << "Analysis failed: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
