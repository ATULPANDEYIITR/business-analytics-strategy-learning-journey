#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * GROUP BY: Segmenting and Aggregating Business Data
 *
 * Case study:
 * A retail organization wants a merge-independent analytics engine that
 * evaluates sales performance across regions, channels, customer segments,
 * and product categories.
 *
 * The program deliberately uses C++ containers and algorithms to show how a
 * relational GROUP BY can be modeled in an in-memory analytics service.
 *
 * Compile:
 *   g++ -std=c++17 -O2 group_by_business_data.cpp -o group_by_business_data
 */

struct Sale {
    int id;
    std::string region;
    std::string channel;
    std::string category;
    std::string product;
    std::string customerSegment;
    int units;
    double revenue;
    double cost;
    double discount;

    double profit() const {
        return revenue - cost;
    }
};

struct GroupMetrics {
    int transactions = 0;
    int units = 0;
    double revenue = 0.0;
    double profit = 0.0;
    std::set<std::string> products;

    void absorb(const Sale& sale) {
        ++transactions;
        units += sale.units;
        revenue += sale.revenue;
        profit += sale.profit();
        products.insert(sale.product);
    }

    double averageOrderValue() const {
        return transactions == 0 ? 0.0 : revenue / transactions;
    }

    double margin() const {
        return revenue == 0.0 ? 0.0 : profit / revenue;
    }
};

std::vector<Sale> buildSales() {
    return {
        {1001, "North", "Online", "Electronics", "Laptop", "Enterprise", 4, 4800, 3600, 0.05},
        {1002, "North", "Retail", "Office", "Monitor", "SMB", 10, 3000, 2100, 0.00},
        {1003, "South", "Online", "Electronics", "Phone", "Consumer", 15, 9000, 6300, 0.10},
        {1004, "West", "Partner", "Software", "Analytics", "Enterprise", 3, 7500, 2250, 0.15},
        {1005, "East", "Retail", "Office", "Chair", "SMB", 20, 4000, 2600, 0.05},
        {1006, "North", "Online", "Software", "CRM", "Enterprise", 5, 10000, 3000, 0.08},
        {1007, "South", "Retail", "Electronics", "Laptop", "Consumer", 3, 3600, 2700, 0.03},
        {1008, "West", "Online", "Office", "Desk", "SMB", 12, 4800, 3000, 0.00},
        {1009, "East", "Partner", "Software", "Analytics", "Enterprise", 4, 10000, 3000, 0.12},
        {1010, "North", "Retail", "Electronics", "Phone", "Consumer", 8, 4800, 3360, 0.07},
        {1011, "South", "Online", "Software", "CRM", "SMB", 7, 8400, 2800, 0.05},
        {1012, "West", "Partner", "Electronics", "Laptop", "Enterprise", 6, 7200, 5400, 0.10},
        {1013, "East", "Retail", "Office", "Monitor", "Consumer", 14, 4200, 2940, 0.04},
        {1014, "North", "Online", "Software", "Analytics", "Enterprise", 2, 5000, 1500, 0.20},
        {1015, "South", "Partner", "Office", "Chair", "SMB", 25, 5000, 3250, 0.06}
    };
}

void validateSales(const std::vector<Sale>& sales) {
    std::set<int> identifiers;

    for (const Sale& sale : sales) {
        if (!identifiers.insert(sale.id).second) {
            throw std::invalid_argument("Duplicate sale ID: " + std::to_string(sale.id));
        }

        if (sale.units <= 0) {
            throw std::invalid_argument("Units must be positive for sale " + std::to_string(sale.id));
        }

        if (sale.revenue < 0.0 || sale.cost < 0.0) {
            throw std::invalid_argument("Negative monetary value for sale " + std::to_string(sale.id));
        }

        if (sale.cost > sale.revenue) {
            throw std::invalid_argument("Cost exceeds revenue for sale " + std::to_string(sale.id));
        }

        if (sale.discount < 0.0 || sale.discount > 1.0) {
            throw std::invalid_argument("Invalid discount for sale " + std::to_string(sale.id));
        }
    }
}

std::unordered_map<std::string, GroupMetrics>
groupByRegion(const std::vector<Sale>& sales) {
    std::unordered_map<std::string, GroupMetrics> groups;

    for (const Sale& sale : sales) {
        groups[sale.region].absorb(sale);
    }

    return groups;
}

using CompositeKey = std::pair<std::string, std::string>;

struct CompositeKeyHash {
    std::size_t operator()(const CompositeKey& key) const noexcept {
        std::size_t first = std::hash<std::string>{}(key.first);
        std::size_t second = std::hash<std::string>{}(key.second);

        return first ^ (second + 0x9e3779b9u + (first << 6) + (first >> 2));
    }
};

std::unordered_map<CompositeKey, GroupMetrics, CompositeKeyHash>
groupByRegionAndChannel(const std::vector<Sale>& sales) {
    std::unordered_map<CompositeKey, GroupMetrics, CompositeKeyHash> groups;

    for (const Sale& sale : sales) {
        groups[{sale.region, sale.channel}].absorb(sale);
    }

    return groups;
}

std::map<std::string, GroupMetrics>
groupByCategory(const std::vector<Sale>& sales) {
    std::map<std::string, GroupMetrics> groups;

    for (const Sale& sale : sales) {
        groups[sale.category].absorb(sale);
    }

    return groups;
}

void printMoney(double value) {
    std::cout << std::fixed << std::setprecision(2) << value;
}

void printRegionReport(const std::vector<Sale>& sales) {
    auto groups = groupByRegion(sales);

    std::vector<std::string> regions;
    regions.reserve(groups.size());

    for (const auto& [region, metrics] : groups) {
        regions.push_back(region);
    }

    std::sort(regions.begin(), regions.end());

    std::cout << "\n=== Regional Performance ===\n";

    for (const auto& region : regions) {
        const auto& metrics = groups.at(region);

        std::cout << region
                  << " | transactions=" << metrics.transactions
                  << " | units=" << metrics.units
                  << " | revenue=";
        printMoney(metrics.revenue);
        std::cout << " | profit=";
        printMoney(metrics.profit);
        std::cout << " | margin=";
        printMoney(metrics.margin() * 100);
        std::cout << "%\n";
    }
}

void printRegionChannelReport(const std::vector<Sale>& sales) {
    auto groups = groupByRegionAndChannel(sales);

    std::vector<std::pair<CompositeKey, GroupMetrics>> ordered(
        groups.begin(), groups.end()
    );

    std::sort(
        ordered.begin(),
        ordered.end(),
        [](const auto& left, const auto& right) {
            return left.first < right.first;
        }
    );

    std::cout << "\n=== Region + Channel Performance ===\n";

    for (const auto& [key, metrics] : ordered) {
        std::cout << key.first << " / " << key.second
                  << " | transactions=" << metrics.transactions
                  << " | revenue=";
        printMoney(metrics.revenue);
        std::cout << " | profit=";
        printMoney(metrics.profit);
        std::cout << '\n';
    }
}

void printConditionalAggregation(const std::vector<Sale>& sales) {
    struct ConditionalMetrics {
        double totalRevenue = 0;
        double onlineRevenue = 0;
        double softwareRevenue = 0;
        int enterpriseTransactions = 0;
    };

    std::map<std::string, ConditionalMetrics> groups;

    /*
     * Unlike filtering the whole input to Online sales, conditional
     * aggregation keeps every row in the regional group and selectively
     * contributes each row to the appropriate metric.
     */
    for (const Sale& sale : sales) {
        auto& metrics = groups[sale.region];

        metrics.totalRevenue += sale.revenue;

        if (sale.channel == "Online") {
            metrics.onlineRevenue += sale.revenue;
        }

        if (sale.category == "Software") {
            metrics.softwareRevenue += sale.revenue;
        }

        if (sale.customerSegment == "Enterprise") {
            ++metrics.enterpriseTransactions;
        }
    }

    std::cout << "\n=== Conditional Aggregation ===\n";

    for (const auto& [region, metrics] : groups) {
        std::cout << region
                  << " | total=";
        printMoney(metrics.totalRevenue);
        std::cout << " | online=";
        printMoney(metrics.onlineRevenue);
        std::cout << " | software=";
        printMoney(metrics.softwareRevenue);
        std::cout << " | enterprise_txns="
                  << metrics.enterpriseTransactions << '\n';
    }
}

void printHavingStyleReport(
    const std::vector<Sale>& sales,
    double minimumRevenue
) {
    auto groups = groupByRegion(sales);

    std::cout << "\n=== HAVING-Style Regional Filter ===\n";

    std::vector<std::pair<std::string, GroupMetrics>> ordered(
        groups.begin(), groups.end()
    );

    std::sort(
        ordered.begin(),
        ordered.end(),
        [](const auto& left, const auto& right) {
            return left.first < right.first;
        }
    );

    for (const auto& [region, metrics] : ordered) {
        /*
         * This condition is deliberately applied after the aggregate exists.
         * It therefore behaves like HAVING rather than a row-level WHERE.
         */
        if (metrics.revenue >= minimumRevenue) {
            std::cout << region << " | revenue=";
            printMoney(metrics.revenue);
            std::cout << " | transactions=" << metrics.transactions << '\n';
        }
    }
}

void printTopCategories(const std::vector<Sale>& sales) {
    auto groups = groupByCategory(sales);

    std::vector<std::pair<std::string, GroupMetrics>> categories(
        groups.begin(), groups.end()
    );

    std::sort(
        categories.begin(),
        categories.end(),
        [](const auto& left, const auto& right) {
            if (left.second.profit != right.second.profit) {
                return left.second.profit > right.second.profit;
            }

            return left.first < right.first;
        }
    );

    std::cout << "\n=== Categories Ranked by Profit ===\n";

    const std::size_t limit = std::min<std::size_t>(3, categories.size());

    for (std::size_t i = 0; i < limit; ++i) {
        const auto& [category, metrics] = categories[i];

        std::cout << category
                  << " | revenue=";
        printMoney(metrics.revenue);
        std::cout << " | profit=";
        printMoney(metrics.profit);
        std::cout << " | products=" << metrics.products.size()
                  << " | margin=";
        printMoney(metrics.margin() * 100);
        std::cout << "%\n";
    }
}

void printCustomerSegmentReport(const std::vector<Sale>& sales) {
    std::map<std::string, GroupMetrics> groups;

    for (const Sale& sale : sales) {
        groups[sale.customerSegment].absorb(sale);
    }

    double totalRevenue = 0.0;

    for (const auto& sale : sales) {
        totalRevenue += sale.revenue;
    }

    std::cout << "\n=== Customer Segment Analysis ===\n";

    for (const auto& [segment, metrics] : groups) {
        double share = totalRevenue == 0.0
            ? 0.0
            : metrics.revenue / totalRevenue;

        std::cout << segment
                  << " | transactions=" << metrics.transactions
                  << " | distinct_products=" << metrics.products.size()
                  << " | revenue=";
        printMoney(metrics.revenue);
        std::cout << " | revenue_share=";
        printMoney(share * 100);
        std::cout << "%\n";
    }
}

void demonstrateWeightedMargin(const std::vector<Sale>& sales) {
    auto groups = groupByCategory(sales);

    std::cout << "\n=== Weighted vs Transaction-Average Margin ===\n";

    for (const auto& [category, metrics] : groups) {
        double sumIndividualMargins = 0.0;
        int count = 0;

        for (const Sale& sale : sales) {
            if (sale.category == category) {
                sumIndividualMargins += sale.revenue == 0.0
                    ? 0.0
                    : sale.profit() / sale.revenue;
                ++count;
            }
        }

        double unweightedAverage = count == 0
            ? 0.0
            : sumIndividualMargins / count;

        std::cout << category
                  << " | aggregate_margin=";
        printMoney(metrics.margin() * 100);
        std::cout << "% | average_transaction_margin=";
        printMoney(unweightedAverage * 100);
        std::cout << "%\n";
    }
}

void demonstrateEmptyInput() {
    std::vector<Sale> empty;
    auto groups = groupByRegion(empty);

    std::cout << "\n=== Empty Input ===\n";
    std::cout << "Groups created: " << groups.size() << '\n';
}

void demonstrateInvalidInput() {
    std::vector<Sale> invalid = {
        {9999, "North", "Online", "Software", "CRM", "Enterprise",
         1, 100.0, 125.0, 0.05}
    };

    try {
        validateSales(invalid);
    } catch (const std::exception& error) {
        std::cout << "\n=== Validation Failure ===\n";
        std::cout << error.what() << '\n';
    }
}

int main() {
    try {
        const auto sales = buildSales();

        validateSales(sales);

        std::cout << "GROUP BY: Segmenting and Aggregating Business Data\n";
        std::cout << "Validated " << sales.size() << " transactions.\n";

        printRegionReport(sales);
        printRegionChannelReport(sales);
        printConditionalAggregation(sales);
        printHavingStyleReport(sales, 15000.0);
        printTopCategories(sales);
        printCustomerSegmentReport(sales);
        demonstrateWeightedMargin(sales);
        demonstrateEmptyInput();
        demonstrateInvalidInput();

        std::cout << "\n=== Complexity Notes ===\n";
        std::cout << "unordered_map grouping: approximately O(n) expected time.\n";
        std::cout << "map grouping: O(n log g) where g is the number of groups.\n";
        std::cout << "Sorting grouped results: O(g log g).\n";
        std::cout << "Each GroupMetrics object stores distinct products in a set.\n";

        /*
         * The case study illustrates an important analytical rule:
         * filtering before aggregation changes the population being measured.
         * Filtering after aggregation answers a different question.
         */
        std::cout << "\n=== Analytical Design Rule ===\n";
        std::cout << "Row-level filtering changes the input population; "
                     "group-level filtering changes which aggregate groups "
                     "appear in the result.\n";
    }
    catch (const std::exception& error) {
        std::cerr << "Fatal analytics error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
