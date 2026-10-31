#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

enum class Segment {
    HighValue,
    Growth,
    AtRisk,
    Standard
};

struct SalesRecord {
    std::string orderId;
    std::string date;
    std::string region;
    std::string salesperson;
    std::string customer;
    std::string product;
    int units;
    double unitPrice;
    double discountRate;
    double costPerUnit;

    double grossSales() const {
        return units * unitPrice;
    }

    double netSales() const {
        return grossSales() * (1.0 - discountRate);
    }

    double profit() const {
        return netSales() - units * costPerUnit;
    }

    double margin() const {
        return netSales() == 0.0 ? 0.0 : profit() / netSales();
    }
};

class AnalyticsEngine {
private:
    std::vector<SalesRecord> records;

    static void validate(const SalesRecord& r) {
        if (r.orderId.empty()) {
            throw std::invalid_argument("Order ID cannot be empty.");
        }
        if (r.units <= 0) {
            throw std::invalid_argument(r.orderId + ": invalid units.");
        }
        if (r.unitPrice < 0 || r.costPerUnit < 0) {
            throw std::invalid_argument(r.orderId + ": negative price.");
        }
        if (r.discountRate < 0 || r.discountRate > 1) {
            throw std::invalid_argument(r.orderId + ": invalid discount.");
        }
        if (r.costPerUnit > r.unitPrice) {
            throw std::invalid_argument(
                r.orderId + ": cost exceeds selling price."
            );
        }
    }

public:
    explicit AnalyticsEngine(std::vector<SalesRecord> input)
        : records(std::move(input)) {
        for (const auto& record : records) {
            validate(record);
        }
    }

    double totalSales() const {
        return std::accumulate(
            records.begin(),
            records.end(),
            0.0,
            [](double total, const SalesRecord& r) {
                return total + r.netSales();
            }
        );
    }

    double totalProfit() const {
        return std::accumulate(
            records.begin(),
            records.end(),
            0.0,
            [](double total, const SalesRecord& r) {
                return total + r.profit();
            }
        );
    }

    std::map<std::string, double> salesByRegion() const {
        std::map<std::string, double> result;
        for (const auto& r : records) {
            result[r.region] += r.netSales();
        }
        return result;
    }

    std::map<std::string, double> profitByProduct() const {
        std::map<std::string, double> result;
        for (const auto& r : records) {
            result[r.product] += r.profit();
        }
        return result;
    }

    std::map<std::string, double> salesByCustomer() const {
        std::map<std::string, double> result;
        for (const auto& r : records) {
            result[r.customer] += r.netSales();
        }
        return result;
    }

    std::map<std::string, Segment> segmentCustomers() const {
        std::map<std::string, Segment> result;
        const auto sales = salesByCustomer();

        for (const auto& [customer, revenue] : sales) {
            double profit = 0.0;

            for (const auto& r : records) {
                if (r.customer == customer) {
                    profit += r.profit();
                }
            }

            const double margin = revenue == 0.0 ? 0.0 : profit / revenue;

            if (revenue >= 15000.0 && margin >= 0.30) {
                result[customer] = Segment::HighValue;
            } else if (revenue >= 10000.0) {
                result[customer] = Segment::Growth;
            } else if (margin < 0.25) {
                result[customer] = Segment::AtRisk;
            } else {
                result[customer] = Segment::Standard;
            }
        }

        return result;
    }

    void validateBusinessRules() const {
        if (records.empty()) {
            throw std::runtime_error("Dataset cannot be empty.");
        }

        std::map<std::string, bool> orderIds;
        for (const auto& r : records) {
            if (orderIds[r.orderId]) {
                throw std::runtime_error("Duplicate order ID: " + r.orderId);
            }
            orderIds[r.orderId] = true;

            if (r.netSales() < 0 || r.profit() < -r.netSales()) {
                throw std::runtime_error(
                    "Financial invariant failed for " + r.orderId
                );
            }
        }
    }

    static std::string segmentName(Segment segment) {
        switch (segment) {
            case Segment::HighValue: return "High Value";
            case Segment::Growth: return "Growth";
            case Segment::AtRisk: return "At Risk";
            case Segment::Standard: return "Standard";
        }
        throw std::logic_error("Unknown segment.");
    }
};

int main() {
    try {
        std::vector<SalesRecord> records = {
            {"O1001", "2026-01-05", "North", "Asha", "Acme", "Analytics", 12, 850, .05, 510},
            {"O1002", "2026-01-09", "South", "Ravi", "Beta", "Automation", 8, 1200, .10, 720},
            {"O1003", "2026-01-15", "North", "Asha", "Delta", "Analytics", 5, 850, 0, 510},
            {"O1004", "2026-02-03", "West", "Neha", "Acme", "Security", 15, 700, .08, 420},
            {"O1005", "2026-02-11", "South", "Ravi", "Gamma", "Analytics", 20, 850, .12, 510},
            {"O1006", "2026-02-19", "West", "Neha", "Delta", "Automation", 7, 1200, .05, 720},
            {"O1007", "2026-03-02", "North", "Asha", "Beta", "Security", 10, 700, .03, 420},
            {"O1008", "2026-03-12", "South", "Ravi", "Acme", "Analytics", 16, 850, .07, 510},
            {"O1009", "2026-03-20", "West", "Neha", "Gamma", "Security", 6, 700, .15, 420},
            {"O1010", "2026-03-25", "North", "Asha", "Delta", "Automation", 11, 1200, .06, 720}
        };

        AnalyticsEngine engine(records);
        engine.validateBusinessRules();

        const double sales = engine.totalSales();
        const double profit = engine.totalProfit();

        std::cout << std::fixed << std::setprecision(2);
        std::cout << "BUSINESS ANALYTICS REPORT\n";
        std::cout << "========================\n";
        std::cout << "Orders:       " << records.size() << '\n';
        std::cout << "Net sales:    $" << sales << '\n';
        std::cout << "Profit:       $" << profit << '\n';
        std::cout << "Margin:       " << (profit / sales) * 100.0 << "%\n";

        std::cout << "\nSales by region\n";
        for (const auto& [region, value] : engine.salesByRegion()) {
            std::cout << "  " << region << ": $" << value << '\n';
        }

        std::cout << "\nProfit by product\n";
        for (const auto& [product, value] : engine.profitByProduct()) {
            std::cout << "  " << product << ": $" << value << '\n';
        }

        std::cout << "\nCustomer segments\n";
        for (const auto& [customer, segment] : engine.segmentCustomers()) {
            std::cout << "  " << customer << ": "
                      << AnalyticsEngine::segmentName(segment) << '\n';
        }

        std::cout << "\nBusiness controls passed.\n";
        std::cout << "Complexity: grouping is O(n) for each aggregation; "
                     "customer segmentation is O(c*n).\n";
        std::cout << "Production control: validate imported data before "
                     "performing financial aggregation.\n";
    } catch (const std::exception& error) {
        std::cerr << "Analytics failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
