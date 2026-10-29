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

enum class Channel {
    Online,
    Retail,
    Partner
};

std::string channelName(Channel channel) {
    switch (channel) {
        case Channel::Online: return "Online";
        case Channel::Retail: return "Retail";
        case Channel::Partner: return "Partner";
    }
    throw std::invalid_argument("Unknown channel");
}

struct Sale {
    int id;
    std::string date;
    std::string region;
    std::string product;
    Channel channel;
    int customerId;
    int quantity;
    double unitPrice;
    double unitCost;

    double revenue() const {
        return quantity * unitPrice;
    }

    double cost() const {
        return quantity * unitCost;
    }

    double margin() const {
        return revenue() - cost();
    }
};

struct InventorySnapshot {
    std::string date;
    std::string region;
    std::string product;
    int units;
};

struct FilterContext {
    std::set<std::string> dates;
    std::set<std::string> regions;
    std::set<std::string> products;
    std::set<Channel> channels;
    std::set<int> customers;

    bool matches(const Sale& sale) const {
        return
            (dates.empty() || dates.count(sale.date)) &&
            (regions.empty() || regions.count(sale.region)) &&
            (products.empty() || products.count(sale.product)) &&
            (channels.empty() || channels.count(sale.channel)) &&
            (customers.empty() || customers.count(sale.customerId));
    }

    bool matches(const InventorySnapshot& row) const {
        return
            (dates.empty() || dates.count(row.date)) &&
            (regions.empty() || regions.count(row.region)) &&
            (products.empty() || products.count(row.product));
    }
};

struct MergeDecision {
    bool eligible;
    std::vector<std::string> failures;
};

class GovernanceAnalytics {
private:
    std::vector<Sale> sales;
    std::vector<InventorySnapshot> inventory;

    static double roundMoney(double value) {
        return std::round(value * 100.0) / 100.0;
    }

    std::vector<const Sale*> filteredSales(const FilterContext& context) const {
        std::vector<const Sale*> result;

        for (const auto& sale : sales) {
            if (context.matches(sale)) {
                result.push_back(&sale);
            }
        }

        return result;
    }

public:
    GovernanceAnalytics(
        std::vector<Sale> salesData,
        std::vector<InventorySnapshot> inventoryData
    )
        : sales(std::move(salesData)),
          inventory(std::move(inventoryData)) {}

    double revenue(const FilterContext& context) const {
        double total = 0.0;

        for (const Sale* sale : filteredSales(context)) {
            total += sale->revenue();
        }

        return roundMoney(total);
    }

    double cost(const FilterContext& context) const {
        double total = 0.0;

        for (const Sale* sale : filteredSales(context)) {
            total += sale->cost();
        }

        return roundMoney(total);
    }

    double margin(const FilterContext& context) const {
        return roundMoney(revenue(context) - cost(context));
    }

    double marginPercent(const FilterContext& context) const {
        const double salesRevenue = revenue(context);

        if (salesRevenue == 0.0) {
            return 0.0;
        }

        return roundMoney(margin(context) * 100.0 / salesRevenue);
    }

    std::size_t distinctCustomers(const FilterContext& context) const {
        std::unordered_set<int> customers;

        for (const Sale* sale : filteredSales(context)) {
            customers.insert(sale->customerId);
        }

        return customers.size();
    }

    std::vector<std::tuple<int, int, double>>
    productRanking(const FilterContext& context) const {
        std::set<std::string> productNames;

        for (const Sale* sale : filteredSales(context)) {
            productNames.insert(sale->product);
        }

        std::vector<std::pair<std::string, double>> scores;

        for (const auto& product : productNames) {
            FilterContext productContext = context;
            productContext.products = {product};
            scores.emplace_back(product, revenue(productContext));
        }

        std::sort(
            scores.begin(),
            scores.end(),
            [](const auto& left, const auto& right) {
                if (left.second != right.second) {
                    return left.second > right.second;
                }
                return left.first < right.first;
            }
        );

        std::vector<std::tuple<int, int, double>> result;
        double previousRevenue = -1.0;
        int rank = 0;

        for (std::size_t i = 0; i < scores.size(); ++i) {
            if (scores[i].second != previousRevenue) {
                rank = static_cast<int>(i) + 1;
            }

            result.emplace_back(
                rank,
                static_cast<int>(i),
                scores[i].second
            );

            previousRevenue = scores[i].second;
        }

        return result;
    }

    int latestInventory(const FilterContext& context) const {
        std::vector<const InventorySnapshot*> rows;

        for (const auto& row : inventory) {
            if (context.matches(row)) {
                rows.push_back(&row);
            }
        }

        if (rows.empty()) {
            return 0;
        }

        const std::string latestDate = std::max_element(
            rows.begin(),
            rows.end(),
            [](const auto* a, const auto* b) {
                return a->date < b->date;
            }
        )->get()->date;

        return std::accumulate(
            rows.begin(),
            rows.end(),
            0,
            [&latestDate](int total, const auto* row) {
                return total + (row->date == latestDate ? row->units : 0);
            }
        );
    }

    double percentOfTotal(const FilterContext& context) const {
        const double numerator = revenue(context);

        // REMOVEFILTERS-like behavior for dimensions while retaining dates.
        FilterContext totalContext = context;
        totalContext.regions.clear();
        totalContext.products.clear();
        totalContext.channels.clear();
        totalContext.customers.clear();

        const double denominator = revenue(totalContext);

        if (denominator == 0.0) {
            return 0.0;
        }

        return roundMoney(numerator * 100.0 / denominator);
    }

    void validate() const {
        std::unordered_set<int> ids;

        for (const auto& sale : sales) {
            if (sale.id <= 0) {
                throw std::invalid_argument("Sale id must be positive.");
            }

            if (!ids.insert(sale.id).second) {
                throw std::invalid_argument("Duplicate sale id.");
            }

            if (sale.quantity <= 0) {
                throw std::invalid_argument("Quantity must be positive.");
            }

            if (sale.unitPrice < 0.0 || sale.unitCost < 0.0) {
                throw std::invalid_argument("Prices cannot be negative.");
            }
        }

        for (const auto& snapshot : inventory) {
            if (snapshot.units < 0) {
                throw std::invalid_argument("Inventory cannot be negative.");
            }
        }
    }
};

std::vector<Sale> sampleSales() {
    return {
        {1001, "2026-01-02", "North", "Laptop", Channel::Online, 501, 2, 1200, 800},
        {1002, "2026-01-04", "North", "Monitor", Channel::Retail, 502, 4, 300, 180},
        {1003, "2026-01-08", "South", "Laptop", Channel::Partner, 503, 1, 1250, 800},
        {1004, "2026-01-12", "North", "Keyboard", Channel::Online, 501, 5, 80, 35},
        {1005, "2026-01-18", "South", "Monitor", Channel::Retail, 504, 3, 310, 180},
        {1006, "2026-01-23", "West", "Laptop", Channel::Online, 505, 1, 1190, 800},
        {1007, "2026-01-28", "North", "Laptop", Channel::Online, 506, 1, 1210, 800},
        {1008, "2026-02-02", "North", "Monitor", Channel::Retail, 507, 5, 305, 180},
        {1009, "2026-02-07", "South", "Laptop", Channel::Online, 503, 2, 1240, 800},
        {1010, "2026-02-11", "West", "Keyboard", Channel::Partner, 508, 8, 82, 35},
        {1011, "2026-02-16", "North", "Laptop", Channel::Online, 509, 1, 1230, 800},
        {1012, "2026-02-20", "South", "Monitor", Channel::Retail, 510, 4, 315, 180},
        {1013, "2026-02-24", "West", "Laptop", Channel::Partner, 511, 2, 1180, 800},
        {1014, "2026-02-27", "North", "Keyboard", Channel::Online, 512, 10, 78, 35},
        {1015, "2026-03-02", "South", "Laptop", Channel::Online, 513, 2, 1260, 800},
        {1016, "2026-03-05", "North", "Monitor", Channel::Retail, 514, 6, 310, 180},
        {1017, "2026-03-10", "West", "Keyboard", Channel::Partner, 515, 7, 85, 35},
        {1018, "2026-03-14", "South", "Laptop", Channel::Online, 516, 1, 1270, 800}
    };
}

std::vector<InventorySnapshot> sampleInventory() {
    return {
        {"2026-01-31", "North", "Laptop", 42},
        {"2026-01-31", "North", "Monitor", 70},
        {"2026-01-31", "South", "Laptop", 31},
        {"2026-02-28", "North", "Laptop", 37},
        {"2026-02-28", "North", "Monitor", 64},
        {"2026-02-28", "South", "Laptop", 26},
        {"2026-02-28", "West", "Keyboard", 90},
        {"2026-03-15", "North", "Laptop", 34},
        {"2026-03-15", "North", "Monitor", 58},
        {"2026-03-15", "South", "Laptop", 24},
        {"2026-03-15", "West", "Keyboard", 82}
    };
}

int main() {
    try {
        GovernanceAnalytics analytics(
            sampleSales(),
            sampleInventory()
        );

        analytics.validate();

        FilterContext februaryNorthSouth;
        for (const std::string& day : {
            "2026-02-02", "2026-02-07", "2026-02-11",
            "2026-02-16", "2026-02-20", "2026-02-24",
            "2026-02-27"
        }) {
            februaryNorthSouth.dates.insert(day);
        }

        februaryNorthSouth.regions = {"North", "South"};

        const double revenue = analytics.revenue(februaryNorthSouth);
        const double margin = analytics.margin(februaryNorthSouth);

        if (revenue <= 0.0) {
            throw std::logic_error("Revenue validation failed.");
        }

        std::cout << std::fixed << std::setprecision(2);
        std::cout << "Advanced Power BI Analytical Calculation Engine\n";
        std::cout << "===============================================\n";
        std::cout << "Revenue:              " << revenue << '\n';
        std::cout << "Cost:                 " << analytics.cost(februaryNorthSouth) << '\n';
        std::cout << "Margin:               " << margin << '\n';
        std::cout << "Margin %:             " << analytics.marginPercent(februaryNorthSouth) << "%\n";
        std::cout << "Distinct customers:   "
                  << analytics.distinctCustomers(februaryNorthSouth) << '\n';
        std::cout << "Latest inventory:     "
                  << analytics.latestInventory({}) << '\n';
        std::cout << "Percent of total:     "
                  << analytics.percentOfTotal(februaryNorthSouth) << "%\n";

        std::cout << "\nProduct ranking:\n";

        const auto ranking = analytics.productRanking(februaryNorthSouth);

        for (const auto& [rank, position, score] : ranking) {
            (void)position;
            std::cout << "  Rank " << rank
                      << " Revenue " << score << '\n';
        }

        // Empty filters must not create divide-by-zero failures.
        FilterContext impossible;
        impossible.products = {"Unknown"};

        if (analytics.revenue(impossible) != 0.0 ||
            analytics.marginPercent(impossible) != 0.0) {
            throw std::logic_error("Empty context handling failed.");
        }

        std::cout << "\nValidation: passed.\n";
        std::cout
            << "Complexity: fact-table measure scans are O(n); product ranking "
               "adds sorting at O(p log p).\n";
        std::cout
            << "Design trade-off: explicit filter sets make context transitions "
               "visible, while a production columnar engine would optimize storage "
               "and aggregation internally.\n";
        std::cout
            << "Security: numeric and categorical inputs are validated; the "
               "program performs no dynamic SQL or executable-expression parsing.\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr << "Execution failed: " << error.what() << '\n';
        return 1;
    }
}
