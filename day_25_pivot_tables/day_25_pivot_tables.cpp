/*
 * Pivot Tables: Aggregating and Analyzing Business Data
 *
 * C++17 case study:
 * A retail analytics engine that transforms transaction-level sales data
 * into pivot-style management reports.
 *
 * The program demonstrates:
 * - Transaction modeling
 * - Derived measures
 * - Dimensions and measures
 * - Hash-based grouping
 * - Two-dimensional pivot tables
 * - Multiple aggregations
 * - Filtering
 * - Ranking
 * - Percentage contribution
 * - Drill-down
 * - Validation
 * - Conditional analysis
 * - Weighted averages
 * - Single-pass aggregation
 * - Complexity and design trade-offs
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

// -----------------------------------------------------------------------------
// 1. TRANSACTION MODEL
// -----------------------------------------------------------------------------

struct Sale {
    string orderId;
    string date;
    string region;
    string category;
    string product;
    string salesperson;
    string channel;

    int units{};
    double unitPrice{};
    double discount{};
    double costPerUnit{};

    double grossSales() const {
        return units * unitPrice;
    }

    double discountAmount() const {
        return grossSales() * discount;
    }

    double netSales() const {
        return grossSales() - discountAmount();
    }

    double totalCost() const {
        return units * costPerUnit;
    }

    double profit() const {
        return netSales() - totalCost();
    }

    double marginPercent() const {
        if (netSales() == 0.0) {
            return 0.0;
        }

        return profit() / netSales() * 100.0;
    }
};


// -----------------------------------------------------------------------------
// 2. SAMPLE TRANSACTION DATA
// -----------------------------------------------------------------------------

vector<Sale> createSalesData() {
    return {
        {"O1001", "2026-01-05", "North", "Electronics", "Laptop", "Asha", "Online", 5, 900, 0.05, 650},
        {"O1002", "2026-01-08", "North", "Electronics", "Monitor", "Ravi", "Retail", 8, 300, 0.02, 210},
        {"O1003", "2026-01-15", "South", "Furniture", "Desk", "Meera", "Online", 4, 450, 0.10, 300},
        {"O1004", "2026-01-21", "West", "Office", "Chair", "Arjun", "Retail", 12, 180, 0.05, 110},
        {"O1005", "2026-02-02", "East", "Electronics", "Laptop", "Asha", "Online", 3, 950, 0.00, 680},
        {"O1006", "2026-02-06", "North", "Furniture", "Desk", "Ravi", "Online", 7, 425, 0.08, 295},
        {"O1007", "2026-02-13", "South", "Office", "Chair", "Meera", "Retail", 15, 175, 0.03, 108},
        {"O1008", "2026-02-20", "West", "Electronics", "Monitor", "Arjun", "Online", 10, 290, 0.04, 205},
        {"O1009", "2026-03-03", "East", "Furniture", "Desk", "Asha", "Retail", 6, 470, 0.06, 310},
        {"O1010", "2026-03-09", "North", "Office", "Chair", "Ravi", "Online", 20, 165, 0.02, 105},
        {"O1011", "2026-03-18", "South", "Electronics", "Laptop", "Meera", "Retail", 4, 920, 0.07, 655},
        {"O1012", "2026-03-25", "West", "Furniture", "Desk", "Arjun", "Online", 5, 460, 0.05, 305}
    };
}


// -----------------------------------------------------------------------------
// 3. FORMATTING
// -----------------------------------------------------------------------------

string money(double value) {
    ostringstream output;
    output << fixed << setprecision(2) << value;
    return output.str();
}


// -----------------------------------------------------------------------------
// 4. DATA VALIDATION
// -----------------------------------------------------------------------------

vector<string> validateSale(const Sale& sale) {
    vector<string> errors;

    if (sale.orderId.empty()) {
        errors.push_back("Missing order ID.");
    }

    if (sale.units <= 0) {
        errors.push_back("Units must be positive.");
    }

    if (!isfinite(sale.unitPrice) || sale.unitPrice < 0.0) {
        errors.push_back("Unit price must be finite and non-negative.");
    }

    if (!isfinite(sale.discount) || sale.discount < 0.0 || sale.discount > 1.0) {
        errors.push_back("Discount must be between 0 and 1.");
    }

    if (!isfinite(sale.costPerUnit) || sale.costPerUnit < 0.0) {
        errors.push_back("Cost per unit must be finite and non-negative.");
    }

    return errors;
}

void validateDataset(const vector<Sale>& sales) {
    set<string> orderIds;

    for (const auto& sale : sales) {
        const auto errors = validateSale(sale);

        if (!errors.empty()) {
            throw runtime_error(
                "Invalid transaction " + sale.orderId +
                ": " + errors.front()
            );
        }

        if (!orderIds.insert(sale.orderId).second) {
            throw runtime_error(
                "Duplicate order ID: " + sale.orderId
            );
        }
    }
}


// -----------------------------------------------------------------------------
// 5. GENERIC GROUPED SUM
// -----------------------------------------------------------------------------

template <typename KeySelector, typename ValueSelector>
map<string, double> groupedSum(
    const vector<Sale>& sales,
    KeySelector keySelector,
    ValueSelector valueSelector
) {
    map<string, double> result;

    for (const auto& sale : sales) {
        result[keySelector(sale)] += valueSelector(sale);
    }

    return result;
}


// -----------------------------------------------------------------------------
// 6. MULTI-METRIC AGGREGATION
// -----------------------------------------------------------------------------

struct Metrics {
    int orders = 0;
    int units = 0;
    double sales = 0.0;
    double profit = 0.0;

    double averageOrder() const {
        return orders == 0 ? 0.0 : sales / orders;
    }
};

map<string, Metrics> aggregateByRegion(const vector<Sale>& sales) {
    map<string, Metrics> result;

    // Single pass: all four metrics are calculated while each transaction
    // is visited exactly once. This avoids repeatedly filtering the dataset.
    for (const auto& sale : sales) {
        Metrics& metrics = result[sale.region];

        ++metrics.orders;
        metrics.units += sale.units;
        metrics.sales += sale.netSales();
        metrics.profit += sale.profit();
    }

    return result;
}


// -----------------------------------------------------------------------------
// 7. TWO-DIMENSIONAL PIVOT
// -----------------------------------------------------------------------------

using Pivot2D = map<string, map<string, double>>;

Pivot2D buildRegionCategoryPivot(const vector<Sale>& sales) {
    Pivot2D pivot;

    for (const auto& sale : sales) {
        pivot[sale.region][sale.category] += sale.netSales();
    }

    return pivot;
}

void printPivot(const Pivot2D& pivot) {
    set<string> categories;

    for (const auto& [region, columns] : pivot) {
        for (const auto& [category, value] : columns) {
            categories.insert(category);
        }
    }

    cout << "\nREGION x CATEGORY SALES PIVOT\n";
    cout << left << setw(14) << "Region";

    for (const auto& category : categories) {
        cout << right << setw(16) << category;
    }

    cout << '\n';

    for (const auto& [region, columns] : pivot) {
        cout << left << setw(14) << region;

        for (const auto& category : categories) {
            const auto it = columns.find(category);
            const double value = it == columns.end() ? 0.0 : it->second;

            cout << right << setw(16) << money(value);
        }

        cout << '\n';
    }
}


// -----------------------------------------------------------------------------
// 8. FILTERING
// -----------------------------------------------------------------------------

template <typename Predicate>
vector<Sale> filterSales(
    const vector<Sale>& sales,
    Predicate predicate
) {
    vector<Sale> result;

    for (const auto& sale : sales) {
        if (predicate(sale)) {
            result.push_back(sale);
        }
    }

    return result;
}


// -----------------------------------------------------------------------------
// 9. RANKING
// -----------------------------------------------------------------------------

struct RankedValue {
    string key;
    double value;
};

vector<RankedValue> rankValues(const map<string, double>& values) {
    vector<RankedValue> ranked;

    for (const auto& [key, value] : values) {
        ranked.push_back({key, value});
    }

    sort(
        ranked.begin(),
        ranked.end(),
        [](const RankedValue& a, const RankedValue& b) {
            return a.value > b.value;
        }
    );

    return ranked;
}


// -----------------------------------------------------------------------------
// 10. PERCENTAGE OF TOTAL
// -----------------------------------------------------------------------------

map<string, double> percentageOfTotal(
    const map<string, double>& values
) {
    double total = 0.0;

    for (const auto& [key, value] : values) {
        total += value;
    }

    map<string, double> result;

    for (const auto& [key, value] : values) {
        result[key] = total == 0.0 ? 0.0 : value / total * 100.0;
    }

    return result;
}


// -----------------------------------------------------------------------------
// 11. CONDITIONAL AGGREGATION
// -----------------------------------------------------------------------------

template <typename Predicate, typename ValueSelector>
double conditionalSum(
    const vector<Sale>& sales,
    Predicate predicate,
    ValueSelector valueSelector
) {
    double total = 0.0;

    for (const auto& sale : sales) {
        if (predicate(sale)) {
            total += valueSelector(sale);
        }
    }

    return total;
}


// -----------------------------------------------------------------------------
// 12. WEIGHTED AVERAGE
// -----------------------------------------------------------------------------

template <typename ValueSelector, typename WeightSelector>
double weightedAverage(
    const vector<Sale>& sales,
    ValueSelector valueSelector,
    WeightSelector weightSelector
) {
    double weightedTotal = 0.0;
    double totalWeight = 0.0;

    for (const auto& sale : sales) {
        const double weight = weightSelector(sale);

        weightedTotal += valueSelector(sale) * weight;
        totalWeight += weight;
    }

    return totalWeight == 0.0
        ? 0.0
        : weightedTotal / totalWeight;
}


// -----------------------------------------------------------------------------
// 13. DRILL-DOWN
// -----------------------------------------------------------------------------

void drillDown(const vector<Sale>& sales, const string& region) {
    cout << "\nDRILL-DOWN FOR REGION: " << region << '\n';

    for (const auto& sale : sales) {
        if (sale.region == region) {
            cout
                << sale.orderId << " | "
                << sale.category << " | "
                << sale.product << " | units="
                << sale.units << " | sales="
                << money(sale.netSales()) << '\n';
        }
    }
}


// -----------------------------------------------------------------------------
// 14. PRODUCT PARETO ANALYSIS
// -----------------------------------------------------------------------------

void printPareto(const vector<Sale>& sales) {
    const auto productSales = groupedSum(
        sales,
        [](const Sale& sale) {
            return sale.product;
        },
        [](const Sale& sale) {
            return sale.netSales();
        }
    );

    const auto ranked = rankValues(productSales);

    double total = 0.0;

    for (const auto& item : ranked) {
        total += item.value;
    }

    double cumulative = 0.0;

    cout << "\nPRODUCT PARETO ANALYSIS\n";

    for (const auto& item : ranked) {
        cumulative += item.value;

        const double share =
            total == 0.0 ? 0.0 : item.value / total * 100.0;

        const double cumulativeShare =
            total == 0.0 ? 0.0 : cumulative / total * 100.0;

        cout
            << left << setw(12) << item.key
            << "share=" << fixed << setprecision(2)
            << share << "% "
            << "cumulative=" << cumulativeShare << "%\n";
    }
}


// -----------------------------------------------------------------------------
// 15. CATEGORY REPORT
// -----------------------------------------------------------------------------

void printCategoryReport(const vector<Sale>& sales) {
    const auto categorySales = groupedSum(
        sales,
        [](const Sale& sale) {
            return sale.category;
        },
        [](const Sale& sale) {
            return sale.netSales();
        }
    );

    const auto categoryProfit = groupedSum(
        sales,
        [](const Sale& sale) {
            return sale.category;
        },
        [](const Sale& sale) {
            return sale.profit();
        }
    );

    cout << "\nCATEGORY MANAGEMENT REPORT\n";
    cout
        << left << setw(15) << "Category"
        << right << setw(16) << "Sales"
        << setw(16) << "Profit"
        << setw(16) << "Share"
        << '\n';

    const auto shares = percentageOfTotal(categorySales);

    for (const auto& [category, salesValue] : categorySales) {
        cout
            << left << setw(15) << category
            << right << setw(16) << money(salesValue)
            << setw(16) << money(categoryProfit.at(category))
            << setw(15) << fixed << setprecision(2)
            << shares.at(category) << "%\n";
    }
}


// -----------------------------------------------------------------------------
// 16. MAIN CASE STUDY
// -----------------------------------------------------------------------------

int main() {
    try {
        const vector<Sale> sales = createSalesData();

        // Before analytical operations, validate the source data.
        // Aggregated numbers are only as trustworthy as the records behind them.
        validateDataset(sales);

        cout << "PIVOT TABLE BUSINESS ANALYTICS CASE STUDY\n";
        cout << "==========================================\n";

        // -----------------------------------------------------------------
        // Basic measures
        // -----------------------------------------------------------------

        const double totalSales = accumulate(
            sales.begin(),
            sales.end(),
            0.0,
            [](double total, const Sale& sale) {
                return total + sale.netSales();
            }
        );

        const double totalProfit = accumulate(
            sales.begin(),
            sales.end(),
            0.0,
            [](double total, const Sale& sale) {
                return total + sale.profit();
            }
        );

        const int totalUnits = accumulate(
            sales.begin(),
            sales.end(),
            0,
            [](int total, const Sale& sale) {
                return total + sale.units;
            }
        );

        cout << "\nBASIC MEASURES\n";
        cout << "Orders: " << sales.size() << '\n';
        cout << "Units: " << totalUnits << '\n';
        cout << "Net sales: " << money(totalSales) << '\n';
        cout << "Profit: " << money(totalProfit) << '\n';

        // -----------------------------------------------------------------
        // One-dimensional pivot
        // -----------------------------------------------------------------

        const auto regionalSales = groupedSum(
            sales,
            [](const Sale& sale) {
                return sale.region;
            },
            [](const Sale& sale) {
                return sale.netSales();
            }
        );

        cout << "\nSALES BY REGION\n";

        for (const auto& [region, value] : regionalSales) {
            cout << left << setw(10)
                 << region
                 << money(value)
                 << '\n';
        }

        // -----------------------------------------------------------------
        // Multiple metrics from one grouping operation
        // -----------------------------------------------------------------

        cout << "\nMULTI-METRIC REGION ANALYSIS\n";

        const auto regionMetrics = aggregateByRegion(sales);

        for (const auto& [region, metrics] : regionMetrics) {
            cout
                << left << setw(10) << region
                << "orders=" << metrics.orders
                << " units=" << metrics.units
                << " sales=" << money(metrics.sales)
                << " profit=" << money(metrics.profit)
                << " averageOrder=" << money(metrics.averageOrder())
                << '\n';
        }

        // -----------------------------------------------------------------
        // Two-dimensional pivot
        // -----------------------------------------------------------------

        printPivot(buildRegionCategoryPivot(sales));

        // -----------------------------------------------------------------
        // Filtered analysis
        // -----------------------------------------------------------------

        const auto online = filterSales(
            sales,
            [](const Sale& sale) {
                return sale.channel == "Online";
            }
        );

        const double onlineSales = accumulate(
            online.begin(),
            online.end(),
            0.0,
            [](double total, const Sale& sale) {
                return total + sale.netSales();
            }
        );

        cout << "\nFILTERED ONLINE ANALYSIS\n";
        cout << "Online orders: " << online.size() << '\n';
        cout << "Online sales: " << money(onlineSales) << '\n';

        // -----------------------------------------------------------------
        // Conditional aggregation
        // -----------------------------------------------------------------

        const double highProfitContribution = conditionalSum(
            sales,
            [](const Sale& sale) {
                return sale.profit() > 500.0;
            },
            [](const Sale& sale) {
                return sale.profit();
            }
        );

        cout << "\nCONDITIONAL AGGREGATION\n";
        cout << "Profit from orders with profit > 500: "
             << money(highProfitContribution) << '\n';

        // -----------------------------------------------------------------
        // Ranking
        // -----------------------------------------------------------------

        const auto categorySales = groupedSum(
            sales,
            [](const Sale& sale) {
                return sale.category;
            },
            [](const Sale& sale) {
                return sale.netSales();
            }
        );

        cout << "\nCATEGORY RANKING\n";

        int rank = 1;

        for (const auto& item : rankValues(categorySales)) {
            cout << rank++ << ". "
                 << item.key
                 << " = "
                 << money(item.value)
                 << '\n';
        }

        // -----------------------------------------------------------------
        // Weighted average
        // -----------------------------------------------------------------

        const double weightedPrice = weightedAverage(
            sales,
            [](const Sale& sale) {
                return sale.unitPrice * (1.0 - sale.discount);
            },
            [](const Sale& sale) {
                return static_cast<double>(sale.units);
            }
        );

        cout << "\nWEIGHTED AVERAGE\n";
        cout << "Weighted selling price: "
             << money(weightedPrice)
             << '\n';

        // -----------------------------------------------------------------
        // Drill-down
        // -----------------------------------------------------------------

        drillDown(sales, "North");

        // -----------------------------------------------------------------
        // Pareto analysis
        // -----------------------------------------------------------------

        printPareto(sales);

        // -----------------------------------------------------------------
        // Management report
        // -----------------------------------------------------------------

        printCategoryReport(sales);

        // -----------------------------------------------------------------
        // Complexity discussion represented in output
        // -----------------------------------------------------------------

        cout << "\nPERFORMANCE DESIGN\n";
        cout << "Single-pass grouped aggregation: approximately O(N).\n";
        cout << "Sorting ranked groups: O(K log K), where K is group count.\n";
        cout << "Two-dimensional pivot construction: approximately O(N).\n";
        cout << "Ordered std::map provides O(log K) insertion/lookup.\n";
        cout << "Hash-based unordered_map can provide average O(1) grouping.\n";
        cout << "The best structure depends on ordering, memory, and workload needs.\n";

        // -----------------------------------------------------------------
        // Important analytical caveat
        // -----------------------------------------------------------------

        cout << "\nANALYTICAL CAVEATS\n";
        cout << "A pivot summarizes records but does not establish causation.\n";
        cout << "Simple averages may be misleading when transaction sizes differ.\n";
        cout << "Missing, duplicated, or incorrectly classified records can distort results.\n";
        cout << "The source data should remain available for drill-down and auditability.\n";

        cout << "\nCASE STUDY COMPLETED SUCCESSFULLY.\n";
    }
    catch (const exception& error) {
        cerr << "ERROR: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
