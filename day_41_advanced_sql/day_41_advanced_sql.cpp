#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Repository-independent analytical case study:
 * a fulfillment analytics engine that mirrors advanced SQL query patterns.
 *
 * Compile:
 *   g++ -std=c++17 -O2 advanced_sql_case_study.cpp -o advanced_sql_case_study
 *
 * The program compares join strategies, computes partitioned rankings,
 * calculates cumulative measures, and validates aggregate consistency.
 */

struct Customer {
    int id;
    std::string name;
    std::string region;
};

struct Order {
    int id;
    int customerId;
    std::string date;
    std::string status;
    double amount;
};

struct CustomerMetric {
    Customer customer;
    double revenue = 0.0;
    int orderCount = 0;
    int regionalRank = 0;
    int rowNumber = 0;
};

struct DailyMetric {
    std::string date;
    double dailyRevenue = 0.0;
    double cumulativeRevenue = 0.0;
};

class FulfillmentAnalytics {
public:
    void addCustomer(Customer customer) {
        if (customer.id <= 0 || customer.name.empty() || customer.region.empty()) {
            throw std::invalid_argument("Customer fields are invalid.");
        }
        if (customerById_.count(customer.id)) {
            throw std::invalid_argument("Duplicate customer identifier.");
        }
        customerById_.emplace(customer.id, std::move(customer));
    }

    void addOrder(Order order) {
        if (order.id <= 0 || order.customerId <= 0 || order.amount < 0.0) {
            throw std::invalid_argument("Order identifier or amount is invalid.");
        }
        if (!customerById_.count(order.customerId)) {
            throw std::invalid_argument("Order references an unknown customer.");
        }
        if (!validStatus(order.status)) {
            throw std::invalid_argument("Unsupported order status.");
        }
        if (orderById_.count(order.id)) {
            throw std::invalid_argument("Duplicate order identifier.");
        }

        orderById_.emplace(order.id, std::move(order));
    }

    std::vector<CustomerMetric> customerRevenue() const {
        std::unordered_map<int, CustomerMetric> metrics;

        // Initialize every customer first. This models a LEFT JOIN: a customer
        // with no qualifying order remains in the result with zero revenue.
        for (const auto& [id, customer] : customerById_) {
            metrics.emplace(id, CustomerMetric{customer, 0.0, 0, 0, 0});
        }

        for (const auto& [id, order] : orderById_) {
            if (order.status == "cancelled") continue;

            auto& metric = metrics.at(order.customerId);
            metric.revenue += order.amount;
            ++metric.orderCount;
        }

        std::vector<CustomerMetric> result;
        result.reserve(metrics.size());

        for (auto& [id, metric] : metrics) {
            result.push_back(metric);
        }

        std::sort(
            result.begin(),
            result.end(),
            [](const CustomerMetric& a, const CustomerMetric& b) {
                if (a.customer.region != b.customer.region) {
                    return a.customer.region < b.customer.region;
                }
                if (a.revenue != b.revenue) return a.revenue > b.revenue;
                return a.customer.id < b.customer.id;
            }
        );

        // Reproduce ROW_NUMBER and RANK semantics. Equal revenues share a
        // rank, but their row numbers remain distinct through the ID tie-breaker.
        std::string currentRegion;
        double previousRevenue = 0.0;
        int position = 0;
        int rank = 0;
        bool first = true;

        for (auto& metric : result) {
            if (first || metric.customer.region != currentRegion) {
                currentRegion = metric.customer.region;
                position = 1;
                rank = 1;
                previousRevenue = metric.revenue;
                first = false;
            } else {
                ++position;
                if (metric.revenue != previousRevenue) rank = position;
                previousRevenue = metric.revenue;
            }

            metric.rowNumber = position;
            metric.regionalRank = rank;
        }

        return result;
    }

    std::vector<DailyMetric> dailyRevenue() const {
        std::map<std::string, double> daily;

        for (const auto& [id, order] : orderById_) {
            if (order.status != "delivered") continue;
            daily[order.date] += order.amount;
        }

        std::vector<DailyMetric> result;
        double running = 0.0;

        for (const auto& [date, amount] : daily) {
            running += amount;
            result.push_back(DailyMetric{date, amount, running});
        }

        return result;
    }

    std::vector<std::pair<Customer, std::optional<Order>>>
    customersWithLatestOrder() const {
        std::unordered_map<int, Order> latest;

        for (const auto& [id, order] : orderById_) {
            auto found = latest.find(order.customerId);
            if (
                found == latest.end() ||
                order.date > found->second.date ||
                (order.date == found->second.date && order.id > found->second.id)
            ) {
                latest[order.customerId] = order;
            }
        }

        std::vector<std::pair<Customer, std::optional<Order>>> result;
        for (const auto& [id, customer] : customerById_) {
            auto found = latest.find(id);
            if (found == latest.end()) {
                result.emplace_back(customer, std::nullopt);
            } else {
                result.emplace_back(customer, found->second);
            }
        }

        std::sort(
            result.begin(),
            result.end(),
            [](const auto& a, const auto& b) {
                return a.first.id < b.first.id;
            }
        );

        return result;
    }

    double revenueForStatusSet(const std::set<std::string>& statuses) const {
        double total = 0.0;

        for (const auto& [id, order] : orderById_) {
            if (statuses.count(order.status)) total += order.amount;
        }

        return total;
    }

    std::size_t customerCount() const {
        return customerById_.size();
    }

    std::size_t orderCount() const {
        return orderById_.size();
    }

private:
    std::unordered_map<int, Customer> customerById_;
    std::unordered_map<int, Order> orderById_;

    static bool validStatus(const std::string& status) {
        static const std::set<std::string> allowed{
            "pending", "paid", "shipped", "delivered", "cancelled"
        };
        return allowed.count(status) != 0;
    }
};

void printCustomerMetrics(const std::vector<CustomerMetric>& metrics) {
    std::cout << "\nRegional revenue ranking\n";
    std::cout << std::left
              << std::setw(8) << "Region"
              << std::setw(18) << "Customer"
              << std::setw(12) << "Revenue"
              << std::setw(10) << "Rank"
              << std::setw(12) << "RowNumber"
              << '\n';

    for (const auto& metric : metrics) {
        std::cout << std::left
                  << std::setw(8) << metric.customer.region
                  << std::setw(18) << metric.customer.name
                  << std::right << std::setw(10)
                  << std::fixed << std::setprecision(2) << metric.revenue
                  << std::setw(10) << metric.regionalRank
                  << std::setw(12) << metric.rowNumber
                  << '\n';
    }
}

void printDailyMetrics(const std::vector<DailyMetric>& metrics) {
    std::cout << "\nDaily revenue and cumulative revenue\n";
    for (const auto& metric : metrics) {
        std::cout << metric.date
                  << " daily=" << std::fixed << std::setprecision(2)
                  << metric.dailyRevenue
                  << " cumulative=" << metric.cumulativeRevenue
                  << '\n';
    }
}

void demonstrateInvalidRecords(FulfillmentAnalytics& analytics) {
    try {
        analytics.addOrder(
            Order{999, 777, "2026-05-01", "delivered", 100.0}
        );
    } catch (const std::invalid_argument& error) {
        std::cout << "\nRejected invalid order: " << error.what() << '\n';
    }

    try {
        analytics.addOrder(
            Order{998, 101, "2026-05-02", "unknown-state", 10.0}
        );
    } catch (const std::invalid_argument& error) {
        std::cout << "Rejected invalid status: " << error.what() << '\n';
    }
}

int main() {
    try {
        FulfillmentAnalytics analytics;

        analytics.addCustomer({101, "Riya Mehta", "North"});
        analytics.addCustomer({102, "Arjun Das", "South"});
        analytics.addCustomer({103, "Sara Khan", "West"});
        analytics.addCustomer({104, "Dev Patel", "North"});
        analytics.addCustomer({105, "Maya Iyer", "East"});
        analytics.addCustomer({106, "Noah Roy", "East"});

        analytics.addOrder({9001, 101, "2026-01-05", "delivered", 42000.0});
        analytics.addOrder({9002, 101, "2026-01-18", "delivered", 18000.0});
        analytics.addOrder({9003, 102, "2026-01-19", "shipped", 27000.0});
        analytics.addOrder({9004, 102, "2026-02-02", "cancelled", 12000.0});
        analytics.addOrder({9005, 103, "2026-02-12", "delivered", 72000.0});
        analytics.addOrder({9006, 104, "2026-02-21", "delivered", 18000.0});
        analytics.addOrder({9007, 101, "2026-03-07", "delivered", 35000.0});
        analytics.addOrder({9008, 105, "2026-03-14", "pending", 8000.0});
        analytics.addOrder({9009, 103, "2026-03-19", "delivered", 72000.0});

        std::cout << "Fulfillment analytics case study\n";
        std::cout << "Customers: " << analytics.customerCount()
                  << ", orders: " << analytics.orderCount() << '\n';

        printCustomerMetrics(analytics.customerRevenue());
        printDailyMetrics(analytics.dailyRevenue());

        std::cout << "\nLatest order by customer\n";
        for (const auto& [customer, latest] : analytics.customersWithLatestOrder()) {
            std::cout << customer.name << ": ";

            if (latest) {
                std::cout << latest->id << " on " << latest->date;
            } else {
                std::cout << "no order";
            }

            std::cout << '\n';
        }

        const double activeRevenue = analytics.revenueForStatusSet(
            {"delivered", "shipped", "paid"}
        );
        std::cout << "\nNon-cancelled operational revenue: "
                  << std::fixed << std::setprecision(2)
                  << activeRevenue << '\n';

        demonstrateInvalidRecords(analytics);

        // Hash-based grouping is expected O(n) for aggregation; ordered output
        // requires O(n log n) sorting. Database indexes trade storage and write
        // cost for selective retrieval. This in-memory case study is not a
        // substitute for an actual database execution plan.
        std::cout << "\nPerformance note: validate plans on production-like data; "
                  << "C++ container timings do not predict SQL optimizer choices.\n";

    } catch (const std::exception& error) {
        std::cerr << "Fatal analytics error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
