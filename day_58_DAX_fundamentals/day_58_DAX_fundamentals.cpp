#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

enum class ReviewStatus {
    Pending,
    Passed,
    Failed
};

struct SalesRow {
    int orderId;
    std::string region;
    std::string product;
    std::string category;
    int quantity;
    double unitPrice;
    double unitCost;
};

struct MeasureResult {
    double sales = 0.0;
    double cost = 0.0;
    double profit = 0.0;
    double margin = 0.0;
    std::size_t orders = 0;
};

/*
 * The class represents a small analytical model.
 *
 * Row-level functions correspond to calculated-column expressions.
 * Aggregate functions correspond to measures.
 * Context filtering is explicit so the distinction between row context
 * and filter context remains visible in the implementation.
 */
class SalesModel {
private:
    std::vector<SalesRow> rows_;

    static void validateRow(const SalesRow& row,
                            std::unordered_set<int>& ids) {
        if (!ids.insert(row.orderId).second) {
            throw std::invalid_argument("Duplicate order ID");
        }

        if (row.quantity <= 0) {
            throw std::invalid_argument("Quantity must be positive");
        }

        if (row.unitPrice < 0.0 || row.unitCost < 0.0) {
            throw std::invalid_argument("Prices cannot be negative");
        }

        if (row.unitCost > row.unitPrice) {
            throw std::invalid_argument(
                "Unit cost cannot exceed unit price"
            );
        }
    }

public:
    explicit SalesModel(std::vector<SalesRow> rows)
        : rows_(std::move(rows)) {
        if (rows_.empty()) {
            throw std::invalid_argument(
                "Sales model cannot be empty"
            );
        }

        std::unordered_set<int> ids;

        for (const auto& row : rows_) {
            validateRow(row, ids);
        }
    }

    static double salesAmount(const SalesRow& row) {
        return row.quantity * row.unitPrice;
    }

    static double costAmount(const SalesRow& row) {
        return row.quantity * row.unitCost;
    }

    static double profitAmount(const SalesRow& row) {
        return salesAmount(row) - costAmount(row);
    }

    static double profitMargin(const SalesRow& row) {
        const double sales = salesAmount(row);
        return sales == 0.0 ? 0.0 : profitAmount(row) / sales;
    }

    static std::string salesBand(const SalesRow& row) {
        const double sales = salesAmount(row);

        if (sales >= 5000.0) {
            return "High";
        }

        if (sales >= 2000.0) {
            return "Medium";
        }

        return "Low";
    }

    std::vector<SalesRow> filter(
        const std::string& region = "",
        const std::string& category = "",
        const std::string& product = ""
    ) const {
        std::vector<SalesRow> result;

        for (const auto& row : rows_) {
            if (!region.empty() && row.region != region) {
                continue;
            }

            if (!category.empty() && row.category != category) {
                continue;
            }

            if (!product.empty() && row.product != product) {
                continue;
            }

            result.push_back(row);
        }

        return result;
    }

    MeasureResult evaluate(
        const std::vector<SalesRow>& context
    ) const {
        MeasureResult result;
        result.orders = context.size();

        for (const auto& row : context) {
            result.sales += salesAmount(row);
            result.cost += costAmount(row);
            result.profit += profitAmount(row);
        }

        result.margin =
            result.sales == 0.0
                ? 0.0
                : result.profit / result.sales;

        return result;
    }

    std::map<std::string, MeasureResult> summarize(
        bool byCategory
    ) const {
        std::map<std::string, std::vector<SalesRow>> groups;

        for (const auto& row : rows_) {
            const std::string& key =
                byCategory ? row.category : row.region;

            groups[key].push_back(row);
        }

        std::map<std::string, MeasureResult> result;

        for (const auto& [key, group] : groups) {
            result[key] = evaluate(group);
        }

        return result;
    }

    std::vector<std::pair<std::string, double>> topProducts(
        std::size_t limit
    ) const {
        if (limit == 0) {
            throw std::invalid_argument(
                "Top-product limit must be positive"
            );
        }

        std::unordered_map<std::string, double> totals;

        for (const auto& row : rows_) {
            totals[row.product] += salesAmount(row);
        }

        std::vector<std::pair<std::string, double>> result(
            totals.begin(),
            totals.end()
        );

        std::sort(
            result.begin(),
            result.end(),
            [](const auto& left, const auto& right) {
                if (left.second != right.second) {
                    return left.second > right.second;
                }

                return left.first < right.first;
            }
        );

        if (result.size() > limit) {
            result.resize(limit);
        }

        return result;
    }

    const std::vector<SalesRow>& rows() const {
        return rows_;
    }
};

static void printMoney(double value) {
    std::cout << "$"
              << std::fixed
              << std::setprecision(2)
              << value;
}

static void printMeasure(
    const std::string& name,
    const MeasureResult& result
) {
    std::cout << name << ": sales=";
    printMoney(result.sales);

    std::cout << ", cost=";
    printMoney(result.cost);

    std::cout << ", profit=";
    printMoney(result.profit);

    std::cout << ", margin="
              << std::fixed
              << std::setprecision(2)
              << result.margin * 100.0
              << "%, orders="
              << result.orders
              << '\n';
}

int main() {
    try {
        std::vector<SalesRow> rows = {
            {1001, "North", "Laptop", "Technology", 2, 1200, 850},
            {1002, "South", "Monitor", "Technology", 4, 350, 220},
            {1003, "North", "Desk", "Furniture", 3, 500, 310},
            {1004, "West", "Laptop", "Technology", 1, 1500, 980},
            {1005, "South", "Chair", "Furniture", 8, 180, 110},
            {1006, "West", "Desk", "Furniture", 2, 550, 320},
            {1007, "North", "Monitor", "Technology", 5, 325, 200},
            {1008, "South", "Laptop", "Technology", 3, 1100, 790}
        };

        SalesModel model(rows);

        const auto all = model.evaluate(model.rows());
        const auto north =
            model.evaluate(model.filter("North"));
        const auto northTechnology =
            model.evaluate(
                model.filter("North", "Technology")
            );
        const auto southTechnology =
            model.evaluate(
                model.filter("South", "Technology")
            );

        std::cout << "=== DAX FUNDAMENTALS MODEL ===\n";
        printMeasure("All data", all);
        printMeasure("North context", north);
        printMeasure(
            "North + Technology context",
            northTechnology
        );
        printMeasure(
            "South + Technology context",
            southTechnology
        );

        std::cout << "\n=== CALCULATED-COLUMN STYLE LOGIC ===\n";

        for (const auto& row : model.rows()) {
            std::cout << "Order "
                      << row.orderId
                      << ": sales=";
            printMoney(SalesModel::salesAmount(row));

            std::cout << ", profit=";
            printMoney(SalesModel::profitAmount(row));

            std::cout << ", margin="
                      << std::fixed
                      << std::setprecision(2)
                      << SalesModel::profitMargin(row) * 100.0
                      << "%, band="
                      << SalesModel::salesBand(row)
                      << '\n';
        }

        std::cout << "\n=== REGION MEASURES ===\n";

        for (const auto& [region, result] :
             model.summarize(false)) {
            printMeasure(region, result);
        }

        std::cout << "\n=== CATEGORY MEASURES ===\n";

        for (const auto& [category, result] :
             model.summarize(true)) {
            printMeasure(category, result);
        }

        std::cout << "\n=== TOP PRODUCTS ===\n";

        for (const auto& [product, sales] :
             model.topProducts(3)) {
            std::cout << product << ": ";
            printMoney(sales);
            std::cout << '\n';
        }

        /*
         * These checks verify the core analytical semantics.
         * Empty filter contexts are valid and return zero rather than
         * causing division-by-zero failures.
         */
        if (std::abs(all.sales - 10555.0) > 0.000001) {
            throw std::runtime_error("Unexpected total sales");
        }

        if (std::abs(all.profit - 3405.0) > 0.000001) {
            throw std::runtime_error("Unexpected total profit");
        }

        if (model.filter("North").size() != 3) {
            throw std::runtime_error("Unexpected North row count");
        }

        const auto empty =
            model.evaluate(model.filter("Unknown"));

        if (empty.sales != 0.0 || empty.margin != 0.0) {
            throw std::runtime_error(
                "Empty context handling failed"
            );
        }

        std::cout << "\nValidation checks: PASSED\n";
    }
    catch (const std::exception& ex) {
        std::cerr << "Model failure: "
                  << ex.what()
                  << '\n';
        return 1;
    }

    return 0;
}
