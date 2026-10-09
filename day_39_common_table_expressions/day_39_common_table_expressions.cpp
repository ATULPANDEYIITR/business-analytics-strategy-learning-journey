#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * C++17 case study: analytical query engine for a distribution business.
 *
 * The implementation models the logical behavior of layered CTEs without
 * pretending to be a complete SQL parser. Each named stage materializes a
 * typed intermediate relation. Downstream stages consume earlier relations.
 */

struct Sale {
    int orderId;
    std::string region;
    std::string month;
    std::string product;
    int quantity;
    double unitPrice;
    double unitCost;
    std::string status;
};

struct RevenueRow {
    std::string region;
    std::string month;
    double revenue = 0.0;
    double profit = 0.0;
    int units = 0;
};

struct CustomerMetric {
    std::string region;
    double revenue = 0.0;
    double profit = 0.0;
    int orders = 0;
};

class RelationError : public std::runtime_error {
public:
    explicit RelationError(const std::string& message)
        : std::runtime_error(message) {}
};

class DistributionAnalytics {
private:
    std::vector<Sale> source_;

    static void validateSale(const Sale& sale) {
        if (sale.orderId <= 0) {
            throw RelationError("Order identifiers must be positive.");
        }
        if (sale.region.empty() || sale.month.empty() || sale.product.empty()) {
            throw RelationError("Region, month, and product are required.");
        }
        if (sale.quantity <= 0) {
            throw RelationError("Sale quantity must be positive.");
        }
        if (!std::isfinite(sale.unitPrice) ||
            !std::isfinite(sale.unitCost) ||
            sale.unitPrice < 0.0 || sale.unitCost < 0.0) {
            throw RelationError("Prices and costs must be finite and non-negative.");
        }
        if (sale.status != "completed" && sale.status != "cancelled" &&
            sale.status != "refunded" && sale.status != "pending") {
            throw RelationError("Unknown order status.");
        }
    }

    // This stage corresponds to a named CTE that filters the base relation.
    std::vector<Sale> eligibleSales() const {
        std::vector<Sale> result;
        for (const auto& sale : source_) {
            if (sale.status == "completed") {
                result.push_back(sale);
            }
        }
        return result;
    }

    // This stage aggregates eligible rows by region and month.
    std::vector<RevenueRow> monthlyRegionRevenue(
        const std::vector<Sale>& eligible) const {

        std::map<std::pair<std::string, std::string>, RevenueRow> groups;

        for (const auto& sale : eligible) {
            auto key = std::make_pair(sale.region, sale.month);
            auto& group = groups[key];
            group.region = sale.region;
            group.month = sale.month;
            group.revenue += sale.quantity * sale.unitPrice;
            group.profit += sale.quantity * (sale.unitPrice - sale.unitCost);
            group.units += sale.quantity;
        }

        std::vector<RevenueRow> result;
        result.reserve(groups.size());
        for (const auto& [key, row] : groups) {
            (void)key;
            result.push_back(row);
        }
        return result;
    }

    // This stage ranks regions after aggregating the intermediate relation.
    std::vector<CustomerMetric> regionalPerformance(
        const std::vector<Sale>& eligible) const {

        std::map<std::string, CustomerMetric> groups;
        std::unordered_map<std::string, std::set<int>> regionOrders;

        for (const auto& sale : eligible) {
            auto& metric = groups[sale.region];
            metric.region = sale.region;
            metric.revenue += sale.quantity * sale.unitPrice;
            metric.profit += sale.quantity * (sale.unitPrice - sale.unitCost);
            regionOrders[sale.region].insert(sale.orderId);
        }

        std::vector<CustomerMetric> result;
        for (auto& [region, metric] : groups) {
            metric.orders = static_cast<int>(regionOrders[region].size());
            result.push_back(metric);
        }

        std::sort(result.begin(), result.end(),
                  [](const CustomerMetric& left, const CustomerMetric& right) {
                      if (left.profit != right.profit) {
                          return left.profit > right.profit;
                      }
                      return left.region < right.region;
                  });
        return result;
    }

    // Revenue is calculated from already filtered rows, preventing cancelled
    // and refunded orders from leaking into performance indicators.
    std::map<std::string, double> monthlyRevenue(
        const std::vector<Sale>& eligible) const {

        std::map<std::string, double> result;
        for (const auto& sale : eligible) {
            result[sale.month] += sale.quantity * sale.unitPrice;
        }
        return result;
    }

public:
    explicit DistributionAnalytics(std::vector<Sale> source)
        : source_(std::move(source)) {
        for (const auto& sale : source_) {
            validateSale(sale);
        }
    }

    void printMonthlyRegionRevenue() const {
        const auto filtered = eligibleSales();
        const auto aggregated = monthlyRegionRevenue(filtered);

        std::cout << "\nMonthly revenue and gross profit by region\n";
        std::cout << std::left << std::setw(12) << "Region"
                  << std::setw(12) << "Month"
                  << std::right << std::setw(12) << "Revenue"
                  << std::setw(12) << "Profit"
                  << std::setw(10) << "Units" << '\n';

        for (const auto& row : aggregated) {
            std::cout << std::left << std::setw(12) << row.region
                      << std::setw(12) << row.month
                      << std::right << std::setw(12) << std::fixed
                      << std::setprecision(2) << row.revenue
                      << std::setw(12) << row.profit
                      << std::setw(10) << row.units << '\n';
        }
    }

    void printRegionalRanking() const {
        const auto filtered = eligibleSales();
        const auto ranking = regionalPerformance(filtered);

        std::cout << "\nRegional profitability ranking\n";
        std::cout << std::left << std::setw(12) << "Region"
                  << std::right << std::setw(12) << "Revenue"
                  << std::setw(12) << "Profit"
                  << std::setw(10) << "Orders" << '\n';

        for (const auto& metric : ranking) {
            std::cout << std::left << std::setw(12) << metric.region
                      << std::right << std::setw(12) << std::fixed
                      << std::setprecision(2) << metric.revenue
                      << std::setw(12) << metric.profit
                      << std::setw(10) << metric.orders << '\n';
        }
    }

    void printMonthOverMonthChange() const {
        const auto filtered = eligibleSales();
        const auto totals = monthlyRevenue(filtered);

        std::cout << "\nMonth-over-month revenue analysis\n";
        std::cout << std::left << std::setw(12) << "Month"
                  << std::right << std::setw(14) << "Revenue"
                  << std::setw(14) << "Change"
                  << std::setw(14) << "Change %" << '\n';

        bool hasPrevious = false;
        double previousRevenue = 0.0;

        for (const auto& [month, revenue] : totals) {
            std::cout << std::left << std::setw(12) << month
                      << std::right << std::setw(14) << std::fixed
                      << std::setprecision(2) << revenue;

            if (!hasPrevious) {
                std::cout << std::setw(14) << "N/A"
                          << std::setw(14) << "N/A" << '\n';
            } else {
                const double change = revenue - previousRevenue;
                std::cout << std::setw(14) << change;

                if (previousRevenue == 0.0) {
                    std::cout << std::setw(14) << "N/A";
                } else {
                    std::cout << std::setw(13)
                              << (change / previousRevenue * 100.0) << '%';
                }
                std::cout << '\n';
            }

            previousRevenue = revenue;
            hasPrevious = true;
        }
    }
};

int main() {
    try {
        std::vector<Sale> sales{
            {501, "North", "2025-01", "Industrial Sensor", 10, 180.0, 105.0, "completed"},
            {502, "South", "2025-01", "Control Unit", 4, 420.0, 290.0, "completed"},
            {503, "North", "2025-02", "Industrial Sensor", 14, 180.0, 105.0, "completed"},
            {504, "West", "2025-02", "Control Unit", 3, 420.0, 290.0, "completed"},
            {505, "South", "2025-02", "Industrial Sensor", 8, 175.0, 105.0, "cancelled"},
            {506, "North", "2025-03", "Control Unit", 6, 430.0, 290.0, "completed"},
            {507, "West", "2025-03", "Industrial Sensor", 12, 185.0, 105.0, "completed"},
            {508, "South", "2025-03", "Control Unit", 2, 420.0, 290.0, "refunded"},
            {509, "South", "2025-04", "Industrial Sensor", 16, 185.0, 105.0, "completed"},
            {510, "North", "2025-04", "Industrial Sensor", 5, 185.0, 105.0, "completed"}
        };

        DistributionAnalytics analytics(std::move(sales));
        analytics.printMonthlyRegionRevenue();
        analytics.printRegionalRanking();
        analytics.printMonthOverMonthChange();

        try {
            Sale invalid{0, "North", "2025-05", "Sensor", 1, 100.0, 60.0, "completed"};
            DistributionAnalytics rejected({invalid});
            (void)rejected;
        } catch (const RelationError& error) {
            std::cout << "\nExpected input validation failure: "
                      << error.what() << '\n';
        }

        // Materializing every stage costs additional memory but permits reuse.
        // For large datasets, database-side aggregation may be more efficient
        // than loading all rows into an application process.
    } catch (const std::exception& error) {
        std::cerr << "Analytics failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
