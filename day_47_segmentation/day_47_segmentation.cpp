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
#include <vector>

struct PullLikeCustomer {
    std::string id;
    int age;
    double income;
    std::string region;
};

struct PurchaseEvent {
    std::string customerId;
    std::string productId;
    double amount;
    int daysAgo;
};

struct Product {
    std::string id;
    std::string category;
    double price;
    double margin;
};

struct BehavioralMetrics {
    int frequency = 0;
    double monetary = 0.0;
    int recency = 999999;
};

class GovernanceAwareSegmentationEngine {
private:
    std::unordered_map<std::string, PullLikeCustomer> customers;
    std::unordered_map<std::string, Product> products;
    std::vector<PurchaseEvent> purchases;

    static double median(std::vector<double> values) {
        if (values.empty()) {
            throw std::invalid_argument("Median requires data.");
        }

        std::sort(values.begin(), values.end());
        const std::size_t middle = values.size() / 2;

        if (values.size() % 2 == 0) {
            return (values[middle - 1] + values[middle]) / 2.0;
        }

        return values[middle];
    }

public:
    void addCustomer(const PullLikeCustomer& customer) {
        if (customer.age < 18) {
            throw std::invalid_argument("Customer must be an adult.");
        }

        if (customer.income < 0) {
            throw std::invalid_argument("Income cannot be negative.");
        }

        customers.emplace(customer.id, customer);
    }

    void addProduct(const Product& product) {
        if (product.price < 0) {
            throw std::invalid_argument("Product price cannot be negative.");
        }

        if (product.margin < 0 || product.margin > 1) {
            throw std::invalid_argument("Margin must be between 0 and 1.");
        }

        products.emplace(product.id, product);
    }

    void recordPurchase(const PurchaseEvent& purchase) {
        if (!customers.contains(purchase.customerId)) {
            throw std::invalid_argument("Purchase references unknown customer.");
        }

        if (!products.contains(purchase.productId)) {
            throw std::invalid_argument("Purchase references unknown product.");
        }

        if (purchase.amount <= 0) {
            throw std::invalid_argument("Purchase amount must be positive.");
        }

        if (purchase.daysAgo < 0) {
            throw std::invalid_argument("Purchase cannot occur in the future.");
        }

        purchases.push_back(purchase);
    }

    std::map<std::string, std::set<std::string>> customerSegments() const {
        std::vector<double> incomes;

        for (const auto& [id, customer] : customers) {
            incomes.push_back(customer.income);
        }

        const double incomeMedian = median(incomes);

        std::map<std::string, std::set<std::string>> segments{
            {"young_high_income", {}},
            {"established_high_income", {}},
            {"value_conscious", {}}
        };

        for (const auto& [id, customer] : customers) {
            if (customer.age <= 34 && customer.income >= incomeMedian) {
                segments["young_high_income"].insert(id);
            }

            if (customer.age >= 35 && customer.income > incomeMedian) {
                segments["established_high_income"].insert(id);
            }

            if (customer.income < incomeMedian) {
                segments["value_conscious"].insert(id);
            }
        }

        return segments;
    }

    std::map<std::string, std::set<std::string>> productSegments() const {
        std::vector<double> prices;

        for (const auto& [id, product] : products) {
            prices.push_back(product.price);
        }

        const double priceMedian = median(prices);

        std::map<std::string, std::set<std::string>> segments{
            {"premium", {}},
            {"high_margin", {}},
            {"standard", {}}
        };

        for (const auto& [id, product] : products) {
            if (product.price > priceMedian) {
                segments["premium"].insert(id);
            }

            if (product.margin >= 0.30) {
                segments["high_margin"].insert(id);
            }

            if (product.price <= priceMedian) {
                segments["standard"].insert(id);
            }
        }

        return segments;
    }

    std::map<std::string, std::set<std::string>> geographicSegments() const {
        std::map<std::string, std::set<std::string>> segments;

        for (const auto& [id, customer] : customers) {
            segments[customer.region].insert(id);
        }

        return segments;
    }

    std::unordered_map<std::string, BehavioralMetrics> behavioralMetrics() const {
        std::unordered_map<std::string, BehavioralMetrics> metrics;

        for (const auto& [id, customer] : customers) {
            metrics[id] = BehavioralMetrics{};
        }

        for (const auto& purchase : purchases) {
            auto& metric = metrics.at(purchase.customerId);

            ++metric.frequency;
            metric.monetary += purchase.amount;
            metric.recency = std::min(metric.recency, purchase.daysAgo);
        }

        return metrics;
    }

    std::map<std::string, std::set<std::string>> behavioralSegments() const {
        const auto metrics = behavioralMetrics();

        std::vector<double> frequencies;
        std::vector<double> monetaryValues;

        for (const auto& [customerId, metric] : metrics) {
            frequencies.push_back(metric.frequency);
            monetaryValues.push_back(metric.monetary);
        }

        const double frequencyMedian = median(frequencies);
        const double monetaryMedian = median(monetaryValues);

        std::map<std::string, std::set<std::string>> segments{
            {"loyal_high_value", {}},
            {"recent_low_frequency", {}},
            {"at_risk", {}}
        };

        for (const auto& [customerId, metric] : metrics) {
            if (
                metric.frequency >= frequencyMedian &&
                metric.monetary >= monetaryMedian
            ) {
                segments["loyal_high_value"].insert(customerId);
            }

            if (
                metric.recency <= 30 &&
                metric.frequency < frequencyMedian
            ) {
                segments["recent_low_frequency"].insert(customerId);
            }

            if (metric.recency > 60) {
                segments["at_risk"].insert(customerId);
            }
        }

        return segments;
    }

    std::map<std::string, double> revenueByCategory() const {
        std::map<std::string, double> revenue;

        for (const auto& purchase : purchases) {
            const auto& product = products.at(purchase.productId);
            revenue[product.category] += purchase.amount;
        }

        return revenue;
    }

    void printSegments(
        const std::string& title,
        const std::map<std::string, std::set<std::string>>& segments
    ) const {
        std::cout << "\n" << title << "\n";

        for (const auto& [name, members] : segments) {
            std::cout << "  " << name << ": ";

            bool first = true;
            for (const auto& member : members) {
                if (!first) {
                    std::cout << ", ";
                }
                std::cout << member;
                first = false;
            }

            if (members.empty()) {
                std::cout << "none";
            }

            std::cout << "\n";
        }
    }
};

int main() {
    try {
        GovernanceAwareSegmentationEngine engine;

        engine.addCustomer({"C001", 27, 90000, "North"});
        engine.addCustomer({"C002", 42, 145000, "West"});
        engine.addCustomer({"C003", 31, 42000, "East"});
        engine.addCustomer({"C004", 55, 70000, "South"});
        engine.addCustomer({"C005", 23, 52000, "North"});
        engine.addCustomer({"C006", 38, 160000, "West"});

        engine.addProduct({"P001", "Electronics", 120000, 0.22});
        engine.addProduct({"P002", "Home", 18000, 0.35});
        engine.addProduct({"P003", "Household", 3500, 0.42});
        engine.addProduct({"P004", "Fashion", 6500, 0.48});
        engine.addProduct({"P005", "Electronics", 42000, 0.31});

        engine.recordPurchase({"C001", "P005", 42000, 12});
        engine.recordPurchase({"C001", "P003", 10500, 27});
        engine.recordPurchase({"C002", "P001", 120000, 7});
        engine.recordPurchase({"C002", "P002", 54000, 36});
        engine.recordPurchase({"C003", "P003", 14000, 16});
        engine.recordPurchase({"C004", "P002", 36000, 104});
        engine.recordPurchase({"C005", "P004", 6500, 14});
        engine.recordPurchase({"C006", "P001", 120000, 17});
        engine.recordPurchase({"C006", "P005", 84000, 49});

        engine.printSegments(
            "Customer segmentation",
            engine.customerSegments()
        );

        engine.printSegments(
            "Product segmentation",
            engine.productSegments()
        );

        engine.printSegments(
            "Geographic segmentation",
            engine.geographicSegments()
        );

        engine.printSegments(
            "Behavioral segmentation",
            engine.behavioralSegments()
        );

        std::cout << "\nRevenue by product category\n";
        for (const auto& [category, revenue] : engine.revenueByCategory()) {
            std::cout << "  " << std::setw(12) << std::left
                      << category << " ₹"
                      << std::fixed << std::setprecision(2)
                      << revenue << "\n";
        }

        /*
         * The engine rejects invalid states before the segmentation layer
         * consumes them. This keeps data-quality errors separate from
         * segmentation logic.
         */
        try {
            engine.recordPurchase({"C999", "P001", 5000, 1});
        } catch (const std::exception& error) {
            std::cout << "\nInvalid purchase rejected: "
                      << error.what() << "\n";
        }

        try {
            engine.addCustomer({"C007", 16, 30000, "North"});
        } catch (const std::exception& error) {
            std::cout << "Invalid customer rejected: "
                      << error.what() << "\n";
        }

    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
