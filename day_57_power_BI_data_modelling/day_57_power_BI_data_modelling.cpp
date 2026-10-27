#include <algorithm>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

enum class RelationshipDirection {
    Single
};

enum class RelationshipCardinality {
    ManyToOne
};

struct DateDimension {
    int key;
    std::string calendarDate;
    int year;
    int quarter;
    int month;
};

struct CustomerDimension {
    int key;
    std::string id;
    std::string name;
    std::string segment;
    std::string region;
};

struct ProductDimension {
    int key;
    std::string id;
    std::string name;
    std::string category;
    std::string subcategory;
};

struct SalesFact {
    int key;
    int dateKey;
    int customerKey;
    int productKey;
    std::string orderId;
    int quantity;
    double unitPrice;
    double discountRate;

    double netSales() const {
        return quantity * unitPrice * (1.0 - discountRate);
    }
};

struct Relationship {
    std::string factColumn;
    std::string dimensionColumn;
    RelationshipCardinality cardinality;
    RelationshipDirection direction;
};

class ModelError : public std::runtime_error {
public:
    explicit ModelError(const std::string& message)
        : std::runtime_error(message) {}
};

class RepositorySalesModel {
private:
    std::unordered_map<int, DateDimension> dates_;
    std::unordered_map<int, CustomerDimension> customers_;
    std::unordered_map<int, ProductDimension> products_;
    std::vector<SalesFact> facts_;
    std::set<int> factKeys_;
    std::vector<Relationship> relationships_;

    static void require(bool condition, const std::string& message) {
        if (!condition) {
            throw ModelError(message);
        }
    }

public:
    RepositorySalesModel() {
        relationships_ = {
            {"dateKey", "dateKey",
             RelationshipCardinality::ManyToOne,
             RelationshipDirection::Single},
            {"customerKey", "customerKey",
             RelationshipCardinality::ManyToOne,
             RelationshipDirection::Single},
            {"productKey", "productKey",
             RelationshipCardinality::ManyToOne,
             RelationshipDirection::Single}
        };
    }

    void addDate(const DateDimension& row) {
        require(row.key > 0, "Date key must be positive.");
        require(!dates_.contains(row.key), "Duplicate date dimension key.");
        dates_.emplace(row.key, row);
    }

    void addCustomer(const CustomerDimension& row) {
        require(row.key > 0, "Customer key must be positive.");
        require(!customers_.contains(row.key),
                "Duplicate customer dimension key.");
        customers_.emplace(row.key, row);
    }

    void addProduct(const ProductDimension& row) {
        require(row.key > 0, "Product key must be positive.");
        require(!products_.contains(row.key),
                "Duplicate product dimension key.");
        products_.emplace(row.key, row);
    }

    void addFact(const SalesFact& fact) {
        require(!factKeys_.contains(fact.key),
                "Duplicate fact table key.");

        require(dates_.contains(fact.dateKey),
                "Fact references a missing date dimension row.");

        require(customers_.contains(fact.customerKey),
                "Fact references a missing customer dimension row.");

        require(products_.contains(fact.productKey),
                "Fact references a missing product dimension row.");

        require(fact.quantity > 0,
                "Fact quantity must be positive.");

        require(fact.unitPrice >= 0,
                "Unit price cannot be negative.");

        require(
            fact.discountRate >= 0.0 && fact.discountRate <= 1.0,
            "Discount rate must be between zero and one."
        );

        facts_.push_back(fact);
        factKeys_.insert(fact.key);
    }

    void validateModel() const {
        require(!dates_.empty(), "Date dimension is empty.");
        require(!customers_.empty(), "Customer dimension is empty.");
        require(!products_.empty(), "Product dimension is empty.");
        require(!facts_.empty(), "Fact table is empty.");

        for (const auto& relationship : relationships_) {
            require(
                relationship.cardinality ==
                    RelationshipCardinality::ManyToOne,
                "Fact relationships must be many-to-one."
            );

            require(
                relationship.direction == RelationshipDirection::Single,
                "Dimension filters must use single direction."
            );
        }

        for (const auto& fact : facts_) {
            require(dates_.contains(fact.dateKey),
                    "Broken date foreign-key relationship.");
            require(customers_.contains(fact.customerKey),
                    "Broken customer foreign-key relationship.");
            require(products_.contains(fact.productKey),
                    "Broken product foreign-key relationship.");
        }
    }

    std::vector<const SalesFact*> filter(
        const std::optional<int>& year = std::nullopt,
        const std::optional<std::string>& region = std::nullopt,
        const std::optional<std::string>& category = std::nullopt,
        const std::optional<std::string>& segment = std::nullopt
    ) const {
        std::vector<const SalesFact*> result;

        for (const auto& fact : facts_) {
            const auto& date = dates_.at(fact.dateKey);
            const auto& customer = customers_.at(fact.customerKey);
            const auto& product = products_.at(fact.productKey);

            if (year && date.year != *year) {
                continue;
            }

            if (region && customer.region != *region) {
                continue;
            }

            if (category && product.category != *category) {
                continue;
            }

            if (segment && customer.segment != *segment) {
                continue;
            }

            result.push_back(&fact);
        }

        return result;
    }

    static double totalNetSales(
        const std::vector<const SalesFact*>& facts
    ) {
        double total = 0.0;

        for (const SalesFact* fact : facts) {
            total += fact->netSales();
        }

        return total;
    }

    static int totalQuantity(
        const std::vector<const SalesFact*>& facts
    ) {
        int total = 0;

        for (const SalesFact* fact : facts) {
            total += fact->quantity;
        }

        return total;
    }

    std::map<std::string, double> salesByCategory(
        const std::vector<const SalesFact*>& facts
    ) const {
        std::map<std::string, double> result;

        for (const SalesFact* fact : facts) {
            const auto& category = products_.at(fact->productKey).category;
            result[category] += fact->netSales();
        }

        return result;
    }

    std::map<std::string, double> salesByRegion(
        const std::vector<const SalesFact*>& facts
    ) const {
        std::map<std::string, double> result;

        for (const SalesFact* fact : facts) {
            const auto& region = customers_.at(fact->customerKey).region;
            result[region] += fact->netSales();
        }

        return result;
    }

    std::size_t factCount() const {
        return facts_.size();
    }
};

int main() {
    try {
        RepositorySalesModel model;

        model.addDate({20260105, "2026-01-05", 2026, 1, 1});
        model.addDate({20260207, "2026-02-07", 2026, 1, 2});
        model.addDate({20260312, "2026-03-12", 2026, 1, 3});
        model.addDate({20260425, "2026-04-25", 2026, 2, 4});

        model.addCustomer(
            {1, "C001", "Apex Systems", "Enterprise", "North"}
        );
        model.addCustomer(
            {2, "C002", "Blue Retail", "SMB", "West"}
        );
        model.addCustomer(
            {3, "C003", "Cedar Health", "Enterprise", "South"}
        );
        model.addCustomer(
            {4, "C004", "Delta Labs", "Mid-Market", "East"}
        );

        model.addProduct(
            {1, "P001", "Analytics Platform", "Software", "Analytics"}
        );
        model.addProduct(
            {2, "P002", "Security Suite", "Software", "Security"}
        );
        model.addProduct(
            {3, "P003", "Cloud Appliance", "Hardware", "Infrastructure"}
        );
        model.addProduct(
            {4, "P004", "Support Contract", "Services", "Support"}
        );

        model.addFact(
            {1, 20260105, 1, 1, "SO1001", 3, 1200.0, 0.05}
        );
        model.addFact(
            {2, 20260207, 2, 2, "SO1002", 2, 800.0, 0.00}
        );
        model.addFact(
            {3, 20260312, 3, 3, "SO1003", 1, 4500.0, 0.10}
        );
        model.addFact(
            {4, 20260425, 4, 4, "SO1004", 5, 300.0, 0.05}
        );

        model.validateModel();

        const auto all = model.filter();
        const auto software = model.filter(
            std::nullopt,
            std::nullopt,
            std::string("Software")
        );
        const auto autoEnterprise = model.filter(
            std::nullopt,
            std::nullopt,
            std::nullopt,
            std::string("Enterprise")
        );

        std::cout << std::fixed << std::setprecision(2);
        std::cout << "POWER BI-STYLE GOVERNANCE MODEL\n";
        std::cout << "===============================\n";
        std::cout << "Fact rows: " << model.factCount() << '\n';
        std::cout << "Total net sales: $"
                  << RepositorySalesModel::totalNetSales(all) << '\n';
        std::cout << "Total quantity: "
                  << RepositorySalesModel::totalQuantity(all) << '\n';
        std::cout << "Software net sales: $"
                  << RepositorySalesModel::totalNetSales(software) << '\n';
        std::cout << "Enterprise net sales: $"
                  << RepositorySalesModel::totalNetSales(autoEnterprise)
                  << '\n';

        std::cout << "\nSales by category\n";
        for (const auto& [category, amount] :
             model.salesByCategory(all)) {
            std::cout << std::setw(15) << std::left
                      << category << " $" << amount << '\n';
        }

        std::cout << "\nSales by region\n";
        for (const auto& [region, amount] :
             model.salesByRegion(all)) {
            std::cout << std::setw(15) << std::left
                      << region << " $" << amount << '\n';
        }

        std::cout << "\nEdge-case validation\n";

        try {
            model.addFact(
                {1, 20260105, 1, 1, "DUPLICATE", 1, 100.0, 0.0}
            );
        } catch (const ModelError& error) {
            std::cout << "Rejected duplicate fact: "
                      << error.what() << '\n';
        }

        try {
            model.addFact(
                {99, 99999999, 1, 1, "BAD-FK", 1, 100.0, 0.0}
            );
        } catch (const ModelError& error) {
            std::cout << "Rejected invalid relationship: "
                      << error.what() << '\n';
        }

        std::cout << "\nEngineering characteristics\n";
        std::cout << "- unordered_map provides average O(1) dimension lookup.\n";
        std::cout << "- vector provides compact fact-row storage.\n";
        std::cout << "- map creates deterministic grouped report output.\n";
        std::cout << "- foreign-key validation prevents orphan fact rows.\n";
        std::cout << "- single-direction relationships reduce ambiguous paths.\n";
        std::cout << "- measures are computed after dimensional filtering.\n";

    } catch (const std::exception& error) {
        std::cerr << "Fatal model error: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
