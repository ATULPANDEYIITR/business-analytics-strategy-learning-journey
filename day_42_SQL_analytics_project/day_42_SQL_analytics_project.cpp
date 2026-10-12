#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Repository-independent retail analytics case study.
 *
 * The program models transaction facts and builds a governance-friendly
 * profitability engine. It distinguishes gross sales, discounts, returns,
 * recognized revenue, recognized cost, and contribution profit.
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic retail_case_study.cpp -o retail_case_study
 */

struct Transaction {
    std::string orderId;
    std::string customerId;
    std::string region;
    std::string category;
    std::string product;
    std::string month;
    int quantity;
    double unitPrice;
    double unitCost;
    double discount;
    bool returned;
};

struct Metrics {
    std::size_t transactionCount = 0;
    std::size_t returnedCount = 0;
    double grossSales = 0.0;
    double discountAmount = 0.0;
    double revenue = 0.0;
    double cost = 0.0;
    double profit = 0.0;

    double margin() const {
        return revenue == 0.0 ? 0.0 : profit / revenue;
    }

    double averageRevenue() const {
        return transactionCount == 0
            ? 0.0
            : revenue / static_cast<double>(transactionCount);
    }
};

struct ProductPerformance {
    std::string product;
    long long unitsSold = 0;
    double revenue = 0.0;
    double profit = 0.0;
};

class RetailAnalytics {
private:
    std::vector<Transaction> transactions_;

    static void validate(const Transaction& transaction) {
        if (transaction.orderId.empty()) {
            throw std::invalid_argument("Order ID cannot be empty");
        }
        if (transaction.customerId.empty()) {
            throw std::invalid_argument("Customer ID cannot be empty");
        }
        if (transaction.quantity <= 0) {
            throw std::invalid_argument("Quantity must be positive");
        }
        if (!std::isfinite(transaction.unitPrice) ||
            transaction.unitPrice < 0.0) {
            throw std::invalid_argument("Unit price must be finite and non-negative");
        }
        if (!std::isfinite(transaction.unitCost) ||
            transaction.unitCost < 0.0) {
            throw std::invalid_argument("Unit cost must be finite and non-negative");
        }
        if (!std::isfinite(transaction.discount) ||
            transaction.discount < 0.0 ||
            transaction.discount > 1.0) {
            throw std::invalid_argument("Discount must be between zero and one");
        }
        if (transaction.month.size() != 7 ||
            transaction.month[4] != '-') {
            throw std::invalid_argument("Month must use YYYY-MM format");
        }
    }

    static double gross(const Transaction& transaction) {
        return transaction.quantity * transaction.unitPrice;
    }

    static double discountValue(const Transaction& transaction) {
        return gross(transaction) * transaction.discount;
    }

    static double recognizedRevenue(const Transaction& transaction) {
        // A returned order contributes zero to recognized sales in this model.
        return transaction.returned
            ? 0.0
            : gross(transaction) - discountValue(transaction);
    }

    static double recognizedCost(const Transaction& transaction) {
        return transaction.returned
            ? 0.0
            : transaction.quantity * transaction.unitCost;
    }

public:
    explicit RetailAnalytics(std::vector<Transaction> transactions)
        : transactions_(std::move(transactions)) {
        std::set<std::string> orderIds;

        for (const auto& transaction : transactions_) {
            validate(transaction);
            if (!orderIds.insert(transaction.orderId).second) {
                throw std::invalid_argument(
                    "Duplicate order ID: " + transaction.orderId
                );
            }
        }
    }

    Metrics overall() const {
        Metrics metrics;

        for (const auto& transaction : transactions_) {
            ++metrics.transactionCount;
            metrics.grossSales += gross(transaction);
            metrics.discountAmount += discountValue(transaction);

            if (transaction.returned) {
                ++metrics.returnedCount;
                continue;
            }

            metrics.revenue += recognizedRevenue(transaction);
            metrics.cost += recognizedCost(transaction);
        }

        metrics.profit = metrics.revenue - metrics.cost;
        return metrics;
    }

    std::map<std::string, Metrics> byRegion() const {
        std::map<std::string, Metrics> grouped;

        for (const auto& transaction : transactions_) {
            auto& metrics = grouped[transaction.region];
            ++metrics.transactionCount;
            metrics.grossSales += gross(transaction);
            metrics.discountAmount += discountValue(transaction);

            if (transaction.returned) {
                ++metrics.returnedCount;
            } else {
                metrics.revenue += recognizedRevenue(transaction);
                metrics.cost += recognizedCost(transaction);
            }
        }

        for (auto& [region, metrics] : grouped) {
            (void)region;
            metrics.profit = metrics.revenue - metrics.cost;
        }

        return grouped;
    }

    std::map<std::string, Metrics> byMonth() const {
        std::map<std::string, Metrics> grouped;

        for (const auto& transaction : transactions_) {
            auto& metrics = grouped[transaction.month];
            ++metrics.transactionCount;
            metrics.grossSales += gross(transaction);
            metrics.discountAmount += discountValue(transaction);

            if (transaction.returned) {
                ++metrics.returnedCount;
            } else {
                metrics.revenue += recognizedRevenue(transaction);
                metrics.cost += recognizedCost(transaction);
            }
        }

        for (auto& [month, metrics] : grouped) {
            (void)month;
            metrics.profit = metrics.revenue - metrics.cost;
        }

        return grouped;
    }

    std::vector<ProductPerformance> productRanking() const {
        std::map<std::string, ProductPerformance> grouped;

        for (const auto& transaction : transactions_) {
            auto& product = grouped[transaction.product];
            product.product = transaction.product;

            if (!transaction.returned) {
                product.unitsSold += transaction.quantity;
                product.revenue += recognizedRevenue(transaction);
                product.profit +=
                    recognizedRevenue(transaction) - recognizedCost(transaction);
            }
        }

        std::vector<ProductPerformance> results;
        for (const auto& [name, product] : grouped) {
            (void)name;
            results.push_back(product);
        }

        std::sort(results.begin(), results.end(),
            [](const ProductPerformance& left,
               const ProductPerformance& right) {
                if (left.profit != right.profit) {
                    return left.profit > right.profit;
                }
                return left.product < right.product;
            });

        return results;
    }

    std::vector<std::pair<std::string, double>> monthlyMovingAverage(
        std::size_t horizon
    ) const {
        if (horizon == 0 || horizon > 24) {
            throw std::invalid_argument("Forecast horizon must be 1 to 24 months");
        }

        auto monthly = byMonth();
        if (monthly.empty()) return {};

        std::vector<double> history;
        for (const auto& [month, metrics] : monthly) {
            (void)month;
            history.push_back(metrics.revenue);
        }

        const std::string latestMonth = monthly.rbegin()->first;
        int year = std::stoi(latestMonth.substr(0, 4));
        int month = std::stoi(latestMonth.substr(5, 2));
        std::vector<std::pair<std::string, double>> forecast;

        for (std::size_t step = 0; step < horizon; ++step) {
            const std::size_t start = history.size() > 3
                ? history.size() - 3
                : 0;

            const double total = std::accumulate(
                history.begin() + static_cast<std::ptrdiff_t>(start),
                history.end(),
                0.0
            );

            const double prediction =
                total / static_cast<double>(history.size() - start);

            ++month;
            if (month > 12) {
                month = 1;
                ++year;
            }

            std::ostringstream label;
            label << year << '-'
                  << std::setw(2) << std::setfill('0') << month;

            forecast.emplace_back(label.str(), prediction);
            history.push_back(prediction);
        }

        return forecast;
    }

    std::vector<std::pair<std::string, double>> highValueOutliers() const {
        std::vector<double> values;
        values.reserve(transactions_.size());

        for (const auto& transaction : transactions_) {
            values.push_back(recognizedRevenue(transaction));
        }

        if (values.size() < 4) return {};

        std::sort(values.begin(), values.end());

        auto percentile = [&values](double fraction) {
            const double position =
                (values.size() - 1) * fraction;
            const auto lower = static_cast<std::size_t>(std::floor(position));
            const auto upper = static_cast<std::size_t>(std::ceil(position));

            if (lower == upper) return values[lower];

            return values[lower] * (upper - position)
                + values[upper] * (position - lower);
        };

        const double q1 = percentile(0.25);
        const double q3 = percentile(0.75);
        const double upperLimit = q3 + 1.5 * (q3 - q1);

        std::vector<std::pair<std::string, double>> outliers;

        for (const auto& transaction : transactions_) {
            const double revenue = recognizedRevenue(transaction);
            if (revenue > upperLimit) {
                outliers.emplace_back(transaction.orderId, revenue);
            }
        }

        return outliers;
    }
};

static void printMoney(double value) {
    std::cout << '$' << std::fixed << std::setprecision(2) << value;
}

static std::vector<Transaction> sampleTransactions() {
    return {
        {"R-1001", "C-101", "North", "Electronics", "Laptop", "2025-01",
            2, 850, 610, 0.05, false},
        {"R-1002", "C-102", "South", "Furniture", "Office Chair", "2025-01",
            3, 190, 118, 0.10, false},
        {"R-1003", "C-101", "North", "Electronics", "Monitor", "2025-02",
            4, 260, 175, 0.0, false},
        {"R-1004", "C-103", "East", "Stationery", "Notebook Pack", "2025-02",
            20, 12, 4, 0.15, false},
        {"R-1005", "C-104", "West", "Furniture", "Desk", "2025-03",
            1, 320, 220, 0.05, true},
        {"R-1006", "C-102", "South", "Electronics", "Laptop", "2025-03",
            1, 850, 610, 0.0, false},
        {"R-1007", "C-105", "Central", "Accessories", "Backpack", "2025-04",
            5, 55, 24, 0.10, false},
        {"R-1008", "C-106", "North", "Electronics", "Laptop", "2025-04",
            15, 850, 610, 0.0, false},
        {"R-1009", "C-107", "East", "Furniture", "Office Chair", "2025-05",
            2, 190, 118, 0.20, false},
        {"R-1010", "C-101", "North", "Electronics", "Monitor", "2025-05",
            3, 260, 175, 0.05, false},
        {"R-1011", "C-108", "West", "Accessories", "USB Hub", "2025-06",
            10, 28, 11, 0.10, false},
        {"R-1012", "C-109", "South", "Furniture", "Desk", "2025-06",
            2, 320, 220, 0.0, false},
    };
}

int main() {
    try {
        RetailAnalytics analytics(sampleTransactions());
        const Metrics metrics = analytics.overall();

        std::cout << "RETAIL PROFITABILITY CASE STUDY\n";
        std::cout << "========================================\n";
        std::cout << "Transactions: " << metrics.transactionCount << '\n';
        std::cout << "Returned: " << metrics.returnedCount << '\n';
        std::cout << "Gross sales: ";
        printMoney(metrics.grossSales);
        std::cout << "\nDiscounts: ";
        printMoney(metrics.discountAmount);
        std::cout << "\nRecognized revenue: ";
        printMoney(metrics.revenue);
        std::cout << "\nRecognized cost: ";
        printMoney(metrics.cost);
        std::cout << "\nContribution profit: ";
        printMoney(metrics.profit);
        std::cout << "\nProfit margin: "
                  << std::fixed << std::setprecision(2)
                  << metrics.margin() * 100.0 << "%\n";

        std::cout << "\nREGIONAL PERFORMANCE\n";
        std::cout << "----------------------------------------\n";

        for (const auto& [region, result] : analytics.byRegion()) {
            std::cout << region << " | Revenue ";
            printMoney(result.revenue);
            std::cout << " | Profit ";
            printMoney(result.profit);
            std::cout << " | Margin " << std::setprecision(2)
                      << result.margin() * 100.0 << "%\n";
        }

        std::cout << "\nPRODUCTS RANKED BY PROFIT\n";
        std::cout << "----------------------------------------\n";

        for (const auto& product : analytics.productRanking()) {
            std::cout << product.product
                      << " | Units " << product.unitsSold
                      << " | Revenue ";
            printMoney(product.revenue);
            std::cout << " | Profit ";
            printMoney(product.profit);
            std::cout << '\n';
        }

        std::cout << "\nBASELINE MONTHLY FORECAST\n";
        std::cout << "----------------------------------------\n";

        for (const auto& [month, revenue] :
             analytics.monthlyMovingAverage(3)) {
            std::cout << month << ": ";
            printMoney(revenue);
            std::cout << '\n';
        }

        std::cout << "\nHIGH-REVENUE OUTLIERS\n";
        std::cout << "----------------------------------------\n";

        for (const auto& [orderId, revenue] : analytics.highValueOutliers()) {
            std::cout << orderId << " | ";
            printMoney(revenue);
            std::cout << '\n';
        }

        // Invalid records must fail before they enter aggregate calculations.
        try {
            RetailAnalytics invalid({
                {"BAD-1", "C-1", "North", "Electronics", "Laptop",
                    "2025-01", 0, 850, 610, 0.05, false}
            });
            (void)invalid;
        } catch (const std::invalid_argument& error) {
            std::cout << "\nValidation correctly rejected an invalid row: "
                      << error.what() << '\n';
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Analytics failed: " << error.what() << '\n';
        return 1;
    }
}
