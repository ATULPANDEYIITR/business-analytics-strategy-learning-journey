/*
 * Advanced Excel: INDEX, MATCH, Dynamic Arrays, and Advanced Formulas
 * ===================================================================
 *
 * C++17 case study:
 *
 * A sales analytics engine models the same concepts used in an advanced
 * Excel workbook:
 *
 *   - INDEX-style positional retrieval
 *   - MATCH-style exact and approximate lookup
 *   - INDEX + MATCH
 *   - two-dimensional lookups
 *   - multi-criteria lookup
 *   - FILTER
 *   - UNIQUE
 *   - SORTBY
 *   - conditional aggregation
 *   - SUMPRODUCT
 *   - ranking
 *   - running totals
 *   - lookup indexes
 *   - validation and error handling
 *   - complexity and performance trade-offs
 *
 * Build:
 *   g++ -std=c++17 -O2 advanced_excel_formulas.cpp -o advanced_excel_formulas
 *
 * Run:
 *   ./advanced_excel_formulas
 */


#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;


// ============================================================================
// 1. DATA MODEL
// ============================================================================

struct SalesRecord {
    string orderId;
    string region;
    string salesperson;
    string product;
    string category;
    string month;
    int units;
    double revenue;
    double cost;

    double profit() const {
        return revenue - cost;
    }

    double margin() const {
        if (revenue == 0.0) {
            return 0.0;
        }

        return profit() / revenue;
    }
};


// ============================================================================
// 2. DISPLAY HELPERS
// ============================================================================

void section(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}


string money(double value) {
    ostringstream output;
    output << fixed << setprecision(2) << value;
    return output.str();
}


void printRecord(const SalesRecord& record) {
    cout
        << record.orderId << " | "
        << record.region << " | "
        << record.salesperson << " | "
        << record.product << " | "
        << record.month << " | Units="
        << record.units << " | Revenue="
        << money(record.revenue) << " | Profit="
        << money(record.profit()) << " | Margin="
        << fixed << setprecision(2)
        << record.margin() * 100.0 << "%\n";
}


// ============================================================================
// 3. INDEX-STYLE POSITIONAL ACCESS
// ============================================================================

template <typename T>
const T& excelIndex(
    const vector<T>& values,
    size_t rowNumber
) {
    /*
     * Excel positions start at 1.
     * C++ vector indexes start at 0.
     *
     * Converting the external spreadsheet-style position to an internal
     * zero-based index is therefore essential.
     */

    if (rowNumber == 0 || rowNumber > values.size()) {
        throw out_of_range("INDEX row is outside the supplied range.");
    }

    return values[rowNumber - 1];
}


template <typename T>
const T& excelIndex(
    const vector<vector<T>>& matrix,
    size_t rowNumber,
    size_t columnNumber
) {
    if (rowNumber == 0 || rowNumber > matrix.size()) {
        throw out_of_range("INDEX row is outside the supplied range.");
    }

    if (columnNumber == 0 ||
        columnNumber > matrix[rowNumber - 1].size()) {
        throw out_of_range("INDEX column is outside the supplied range.");
    }

    return matrix[rowNumber - 1][columnNumber - 1];
}


// ============================================================================
// 4. MATCH
// ============================================================================

template <typename T>
size_t excelMatchExact(
    const T& lookupValue,
    const vector<T>& values
) {
    /*
     * Returns a one-based position, matching Excel MATCH(..., 0).
     *
     * Complexity: O(n)
     */

    for (size_t index = 0; index < values.size(); ++index) {
        if (values[index] == lookupValue) {
            return index + 1;
        }
    }

    throw runtime_error("MATCH could not find the requested value.");
}


// ============================================================================
// 5. INDEX + MATCH
// ============================================================================

template <typename T>
const T& indexMatch(
    const vector<T>& returnValues,
    const vector<string>& lookupValues,
    const string& lookupValue
) {
    /*
     * Equivalent conceptually to:
     *
     * =INDEX(return_range,
     *        MATCH(lookup_value, lookup_range, 0))
     */

    if (returnValues.size() != lookupValues.size()) {
        throw invalid_argument(
            "INDEX and MATCH ranges must have equal lengths."
        );
    }

    size_t position = excelMatchExact(
        lookupValue,
        lookupValues
    );

    return excelIndex(returnValues, position);
}


// ============================================================================
// 6. TWO-WAY LOOKUP
// ============================================================================

double twoWayLookup(
    const vector<vector<double>>& table,
    const vector<string>& rowLabels,
    const vector<string>& columnLabels,
    const string& rowKey,
    const string& columnKey
) {
    /*
     * Equivalent to:
     *
     * =INDEX(
     *      data,
     *      MATCH(rowKey, rows, 0),
     *      MATCH(columnKey, columns, 0)
     * )
     */

    size_t rowPosition = excelMatchExact(rowKey, rowLabels);
    size_t columnPosition = excelMatchExact(columnKey, columnLabels);

    return excelIndex(
        table,
        rowPosition,
        columnPosition
    );
}


// ============================================================================
// 7. MULTI-CRITERIA LOOKUP
// ============================================================================

optional<SalesRecord> multiCriteriaLookup(
    const vector<SalesRecord>& data,
    const string& region,
    const string& product,
    const string& month
) {
    /*
     * A multi-condition Excel lookup often conceptually evaluates:
     *
     * (Region = selectedRegion)
     * *
     * (Product = selectedProduct)
     * *
     * (Month = selectedMonth)
     *
     * In C++, the logical AND expresses the same requirement directly.
     */

    for (const auto& record : data) {
        if (
            record.region == region &&
            record.product == product &&
            record.month == month
        ) {
            return record;
        }
    }

    return nullopt;
}


// ============================================================================
// 8. FILTER
// ============================================================================

template <typename T, typename Predicate>
vector<T> excelFilter(
    const vector<T>& values,
    Predicate predicate
) {
    /*
     * Models:
     *
     * =FILTER(array, include)
     *
     * The result may contain zero, one, or many rows.
     */

    vector<T> result;

    for (const auto& value : values) {
        if (predicate(value)) {
            result.push_back(value);
        }
    }

    return result;
}


// ============================================================================
// 9. UNIQUE
// ============================================================================

template <typename T>
vector<T> excelUnique(const vector<T>& values) {
    /*
     * A set tracks membership while the result vector preserves first-seen
     * order. This resembles the practical use of UNIQUE for reporting.
     */

    set<T> seen;
    vector<T> result;

    for (const auto& value : values) {
        if (seen.insert(value).second) {
            result.push_back(value);
        }
    }

    return result;
}


// ============================================================================
// 10. SORTBY
// ============================================================================

template <typename Predicate>
void excelSortBy(
    vector<SalesRecord>& data,
    Predicate predicate
) {
    /*
     * Equivalent conceptually to:
     *
     * =SORTBY(data, profit_range, -1)
     *
     * std::sort is O(n log n) average complexity.
     */

    sort(
        data.begin(),
        data.end(),
        predicate
    );
}


// ============================================================================
// 11. CONDITIONAL AGGREGATION
// ============================================================================

template <typename Predicate, typename ValueFunction>
double sumIf(
    const vector<SalesRecord>& data,
    Predicate predicate,
    ValueFunction valueFunction
) {
    double total = 0.0;

    for (const auto& record : data) {
        if (predicate(record)) {
            total += valueFunction(record);
        }
    }

    return total;
}


template <typename Predicate>
size_t countIf(
    const vector<SalesRecord>& data,
    Predicate predicate
) {
    size_t count = 0;

    for (const auto& record : data) {
        if (predicate(record)) {
            ++count;
        }
    }

    return count;
}


template <typename Predicate, typename ValueFunction>
double averageIf(
    const vector<SalesRecord>& data,
    Predicate predicate,
    ValueFunction valueFunction
) {
    double total = 0.0;
    size_t count = 0;

    for (const auto& record : data) {
        if (predicate(record)) {
            total += valueFunction(record);
            ++count;
        }
    }

    if (count == 0) {
        throw runtime_error(
            "AVERAGEIFS-style calculation has no qualifying rows."
        );
    }

    return total / static_cast<double>(count);
}


// ============================================================================
// 12. SUMPRODUCT
// ============================================================================

double sumProduct(
    const vector<double>& first,
    const vector<double>& second
) {
    if (first.size() != second.size()) {
        throw invalid_argument(
            "SUMPRODUCT arrays must have equal sizes."
        );
    }

    double total = 0.0;

    for (size_t index = 0; index < first.size(); ++index) {
        total += first[index] * second[index];
    }

    return total;
}


double weightedAverage(
    const vector<double>& values,
    const vector<double>& weights
) {
    double totalWeight = accumulate(
        weights.begin(),
        weights.end(),
        0.0
    );

    if (totalWeight == 0.0) {
        throw runtime_error(
            "Weighted average requires non-zero total weight."
        );
    }

    return sumProduct(values, weights) / totalWeight;
}


// ============================================================================
// 13. APPROXIMATE LOOKUP
// ============================================================================

string approximateLookup(
    double lookupValue,
    const vector<double>& thresholds,
    const vector<string>& labels
) {
    /*
     * This models:
     *
     * =INDEX(labels,
     *        MATCH(value, thresholds, 1))
     *
     * The thresholds must be sorted ascending.
     */

    if (thresholds.empty() || thresholds.size() != labels.size()) {
        throw invalid_argument(
            "Threshold and label ranges must have equal non-zero size."
        );
    }

    if (!is_sorted(thresholds.begin(), thresholds.end())) {
        throw invalid_argument(
            "Approximate lookup thresholds must be ascending."
        );
    }

    if (lookupValue < thresholds.front()) {
        throw out_of_range(
            "Lookup value is below the first threshold."
        );
    }

    auto iterator = upper_bound(
        thresholds.begin(),
        thresholds.end(),
        lookupValue
    );

    size_t index = static_cast<size_t>(
        distance(thresholds.begin(), iterator)
    ) - 1;

    return labels[index];
}


// ============================================================================
// 14. RANK
// ============================================================================

int rankDescending(
    double value,
    const vector<double>& values
) {
    /*
     * RANK.EQ in descending mode:
     *
     * rank = 1 + number of values strictly greater than current value
     *
     * Equal values receive the same rank.
     */

    int rank = 1;

    for (double other : values) {
        if (other > value) {
            ++rank;
        }
    }

    return rank;
}


// ============================================================================
// 15. RUNNING TOTAL
// ============================================================================

vector<double> runningTotal(
    const vector<double>& values
) {
    vector<double> result;
    result.reserve(values.size());

    double total = 0.0;

    for (double value : values) {
        total += value;
        result.push_back(total);
    }

    return result;
}


// ============================================================================
// 16. RUNNING AVERAGE
// ============================================================================

vector<double> runningAverage(
    const vector<double>& values
) {
    vector<double> result;
    result.reserve(values.size());

    double total = 0.0;

    for (size_t index = 0; index < values.size(); ++index) {
        total += values[index];

        result.push_back(
            total / static_cast<double>(index + 1)
        );
    }

    return result;
}


// ============================================================================
// 17. LOOKUP INDEX
// ============================================================================

class OrderIndex {
private:
    /*
     * unordered_map provides average O(1) exact lookup after construction.
     *
     * This models an important production principle:
     *
     * Repeatedly scanning a large worksheet range can be expensive.
     * If the same key is looked up many times, an index can avoid repeated
     * linear scans.
     */

    unordered_map<string, SalesRecord> index;

public:
    explicit OrderIndex(
        const vector<SalesRecord>& records
    ) {
        index.reserve(records.size());

        for (const auto& record : records) {
            index[record.orderId] = record;
        }
    }

    optional<SalesRecord> find(
        const string& orderId
    ) const {
        auto iterator = index.find(orderId);

        if (iterator == index.end()) {
            return nullopt;
        }

        return iterator->second;
    }
};


// ============================================================================
// 18. BUSINESS ANALYTICS CLASS
// ============================================================================

class SalesAnalytics {
private:
    vector<SalesRecord> records;

public:
    explicit SalesAnalytics(
        vector<SalesRecord> input
    )
        : records(move(input)) {
        validate();
    }

    void validate() const {
        set<string> orderIds;

        for (const auto& record : records) {
            if (record.orderId.empty()) {
                throw invalid_argument(
                    "Order ID cannot be empty."
                );
            }

            if (!orderIds.insert(record.orderId).second) {
                throw invalid_argument(
                    "Duplicate order ID: " + record.orderId
                );
            }

            if (record.units < 0) {
                throw invalid_argument(
                    "Units cannot be negative."
                );
            }

            if (record.revenue < 0 || record.cost < 0) {
                throw invalid_argument(
                    "Revenue and cost cannot be negative."
                );
            }
        }
    }

    const vector<SalesRecord>& data() const {
        return records;
    }

    double revenueForRegion(
        const string& region
    ) const {
        return sumIf(
            records,
            [&](const SalesRecord& record) {
                return record.region == region;
            },
            [](const SalesRecord& record) {
                return record.revenue;
            }
        );
    }

    double profitForRegion(
        const string& region
    ) const {
        return sumIf(
            records,
            [&](const SalesRecord& record) {
                return record.region == region;
            },
            [](const SalesRecord& record) {
                return record.profit();
            }
        );
    }

    vector<SalesRecord> highProfitOrders(
        double minimumProfit
    ) const {
        return excelFilter(
            records,
            [&](const SalesRecord& record) {
                return record.profit() >= minimumProfit;
            }
        );
    }
};


// ============================================================================
// 19. MAIN CASE STUDY
// ============================================================================

int main() {
    try {
        section(
            "ADVANCED EXCEL CASE STUDY: SALES ANALYTICS ENGINE"
        );

        vector<SalesRecord> records = {
            {"O1001", "North", "Asha", "Laptop Pro", "Computers", "Jan", 8, 96000, 72000},
            {"O1002", "South", "Ravi", "Laptop Pro", "Computers", "Jan", 6, 72000, 54000},
            {"O1003", "West", "Neha", "Tablet X", "Tablets", "Jan", 12, 60000, 42000},
            {"O1004", "East", "Vikram", "Phone Z", "Phones", "Jan", 20, 100000, 70000},
            {"O1005", "North", "Asha", "Tablet X", "Tablets", "Feb", 15, 75000, 52500},
            {"O1006", "South", "Ravi", "Phone Z", "Phones", "Feb", 17, 85000, 59500},
            {"O1007", "West", "Neha", "Laptop Pro", "Computers", "Feb", 10, 120000, 90000},
            {"O1008", "East", "Vikram", "Tablet X", "Tablets", "Feb", 9, 45000, 31500},
            {"O1009", "North", "Asha", "Phone Z", "Phones", "Mar", 25, 125000, 87500},
            {"O1010", "South", "Ravi", "Tablet X", "Tablets", "Mar", 14, 70000, 49000},
            {"O1011", "West", "Neha", "Phone Z", "Phones", "Mar", 22, 110000, 77000},
            {"O1012", "East", "Vikram", "Laptop Pro", "Computers", "Mar", 7, 84000, 63000}
        };


        // ====================================================================
        // A. VALIDATED APPLICATION MODEL
        // ====================================================================

        SalesAnalytics analytics(records);

        cout
            << "Validated records: "
            << analytics.data().size()
            << "\n";


        // ====================================================================
        // B. INDEX
        // ====================================================================

        section("1. INDEX");

        vector<string> regions = {
            "North",
            "South",
            "West",
            "East"
        };

        cout
            << "INDEX position 3: "
            << excelIndex(regions, 3)
            << "\n";


        // ====================================================================
        // C. MATCH
        // ====================================================================

        section("2. MATCH");

        size_t tabletPosition = excelMatchExact(
            string("Tablet X"),
            vector<string>{
                "Laptop Pro",
                "Tablet X",
                "Phone Z"
            }
        );

        cout
            << "MATCH(Tablet X): "
            << tabletPosition
            << "\n";


        // ====================================================================
        // D. INDEX + MATCH
        // ====================================================================

        section("3. INDEX + MATCH");

        vector<string> productNames = {
            "Laptop Pro",
            "Tablet X",
            "Phone Z"
        };

        vector<double> prices = {
            12000,
            5000,
            3000
        };

        double tabletPrice = indexMatch(
            prices,
            productNames,
            "Tablet X"
        );

        cout
            << "Tablet X price: "
            << money(tabletPrice)
            << "\n";


        // ====================================================================
        // E. TWO-WAY LOOKUP
        // ====================================================================

        section("4. TWO-WAY LOOKUP");

        vector<string> monthLabels = {
            "Jan",
            "Feb",
            "Mar"
        };

        vector<vector<double>> revenueTable = {
            {96000, 75000, 125000},
            {72000, 85000, 70000},
            {60000, 120000, 110000},
            {100000, 45000, 84000}
        };

        double westFebruary = twoWayLookup(
            revenueTable,
            regions,
            monthLabels,
            "West",
            "Feb"
        );

        cout
            << "West / Feb revenue: "
            << money(westFebruary)
            << "\n";


        // ====================================================================
        // F. MULTI-CRITERIA LOOKUP
        // ====================================================================

        section("5. MULTI-CRITERIA LOOKUP");

        auto lookupResult = multiCriteriaLookup(
            records,
            "North",
            "Tablet X",
            "Feb"
        );

        if (lookupResult.has_value()) {
            printRecord(lookupResult.value());
        } else {
            cout << "No matching record.\n";
        }


        // ====================================================================
        // G. FILTER
        // ====================================================================

        section("6. FILTER");

        vector<SalesRecord> northOrders = excelFilter(
            records,
            [](const SalesRecord& record) {
                return record.region == "North";
            }
        );

        cout
            << "North order count: "
            << northOrders.size()
            << "\n";

        for (const auto& record : northOrders) {
            printRecord(record);
        }

        vector<SalesRecord> highProfitOrders =
            analytics.highProfitOrders(30000);

        cout
            << "\nOrders with profit >= 30000: "
            << highProfitOrders.size()
            << "\n";

        for (const auto& record : highProfitOrders) {
            cout << record.orderId << " ";
        }

        cout << "\n";


        // ====================================================================
        // H. UNIQUE
        // ====================================================================

        section("7. UNIQUE");

        vector<string> allProducts;

        for (const auto& record : records) {
            allProducts.push_back(record.product);
        }

        vector<string> uniqueProducts =
            excelUnique(allProducts);

        cout << "Unique products: ";

        for (const auto& product : uniqueProducts) {
            cout << product << " ";
        }

        cout << "\n";


        // ====================================================================
        // I. SORTBY
        // ====================================================================

        section("8. SORTBY");

        vector<SalesRecord> sortedByProfit = records;

        excelSortBy(
            sortedByProfit,
            [](const SalesRecord& left,
               const SalesRecord& right) {
                return left.profit() > right.profit();
            }
        );

        cout << "Top five orders by profit:\n";

        for (size_t i = 0;
             i < min<size_t>(5, sortedByProfit.size());
             ++i) {
            printRecord(sortedByProfit[i]);
        }


        // ====================================================================
        // J. SUMIFS / COUNTIFS / AVERAGEIFS
        // ====================================================================

        section("9. CONDITIONAL AGGREGATION");

        double northRevenue = analytics.revenueForRegion(
            "North"
        );

        double northProfit = analytics.profitForRegion(
            "North"
        );

        size_t northCount = countIf(
            records,
            [](const SalesRecord& record) {
                return record.region == "North";
            }
        );

        double northAverageRevenue = averageIf(
            records,
            [](const SalesRecord& record) {
                return record.region == "North";
            },
            [](const SalesRecord& record) {
                return record.revenue;
            }
        );

        cout
            << "North revenue: "
            << money(northRevenue)
            << "\n";

        cout
            << "North profit: "
            << money(northProfit)
            << "\n";

        cout
            << "North orders: "
            << northCount
            << "\n";

        cout
            << "North average order revenue: "
            << money(northAverageRevenue)
            << "\n";


        // Multiple criteria.
        double northPhoneRevenue = sumIf(
            records,
            [](const SalesRecord& record) {
                return
                    record.region == "North" &&
                    record.product == "Phone Z";
            },
            [](const SalesRecord& record) {
                return record.revenue;
            }
        );

        cout
            << "North Phone Z revenue: "
            << money(northPhoneRevenue)
            << "\n";


        // ====================================================================
        // K. SUMPRODUCT
        // ====================================================================

        section("10. SUMPRODUCT");

        vector<double> values = {
            100,
            200,
            300
        };

        vector<double> weights = {
            2,
            3,
            5
        };

        cout
            << "Weighted average: "
            << money(
                weightedAverage(
                    values,
                    weights
                )
            )
            << "\n";


        // ====================================================================
        // L. APPROXIMATE LOOKUP
        // ====================================================================

        section("11. APPROXIMATE LOOKUP");

        vector<double> thresholds = {
            0,
            10000,
            50000,
            100000
        };

        vector<string> levels = {
            "Bronze",
            "Silver",
            "Gold",
            "Platinum"
        };

        for (double revenue : {
            5000.0,
            10000.0,
            25000.0,
            50000.0,
            75000.0,
            100000.0,
            150000.0
        }) {
            cout
                << fixed
                << setprecision(0)
                << revenue
                << " -> "
                << approximateLookup(
                    revenue,
                    thresholds,
                    levels
                )
                << "\n";
        }


        // ====================================================================
        // M. RANKING
        // ====================================================================

        section("12. RANKING");

        vector<double> profits;

        for (const auto& record : records) {
            profits.push_back(record.profit());
        }

        for (const auto& record : records) {
            cout
                << record.orderId
                << " | Profit="
                << money(record.profit())
                << " | Rank="
                << rankDescending(
                    record.profit(),
                    profits
                )
                << "\n";
        }


        // ====================================================================
        // N. RUNNING TOTAL
        // ====================================================================

        section("13. RUNNING TOTAL");

        vector<double> monthlyRevenue;

        for (const string& month : {
            string("Jan"),
            string("Feb"),
            string("Mar")
        }) {
            double monthRevenue = sumIf(
                records,
                [&](const SalesRecord& record) {
                    return record.month == month;
                },
                [](const SalesRecord& record) {
                    return record.revenue;
                }
            );

            monthlyRevenue.push_back(monthRevenue);
        }

        vector<double> totals =
            runningTotal(monthlyRevenue);

        vector<double> averages =
            runningAverage(monthlyRevenue);

        for (size_t index = 0;
             index < monthlyRevenue.size();
             ++index) {
            cout
                << "Month "
                << index + 1
                << " | Revenue="
                << money(monthlyRevenue[index])
                << " | Running="
                << money(totals[index])
                << " | Running Average="
                << money(averages[index])
                << "\n";
        }


        // ====================================================================
        // O. INDEXED EXACT LOOKUP
        // ====================================================================

        section("14. INDEXED LOOKUP FOR PERFORMANCE");

        OrderIndex orderIndex(records);

        auto indexedOrder = orderIndex.find("O1007");

        if (indexedOrder.has_value()) {
            printRecord(indexedOrder.value());
        }

        auto missingOrder = orderIndex.find("O9999");

        if (!missingOrder.has_value()) {
            cout << "O9999 -> Not Found\n";
        }


        // ====================================================================
        // P. EDGE CASES
        // ====================================================================

        section("15. EDGE CASES AND FAILURE CONDITIONS");

        try {
            excelIndex(
                regions,
                0
            );
        } catch (const exception& error) {
            cout
                << "INDEX invalid position: "
                << error.what()
                << "\n";
        }

        try {
            excelMatchExact(
                string("Unknown"),
                productNames
            );
        } catch (const exception& error) {
            cout
                << "MATCH missing value: "
                << error.what()
                << "\n";
        }

        try {
            approximateLookup(
                -10,
                thresholds,
                levels
            );
        } catch (const exception& error) {
            cout
                << "Approximate lookup failure: "
                << error.what()
                << "\n";
        }

        try {
            weightedAverage(
                vector<double>{10, 20},
                vector<double>{0, 0}
            );
        } catch (const exception& error) {
            cout
                << "Weighted-average failure: "
                << error.what()
                << "\n";
        }


        // ====================================================================
        // Q. COMPLEXITY
        // ====================================================================

        section("16. COMPLEXITY AND DESIGN TRADE-OFFS");

        cout
            << "Linear exact lookup: O(n)\n"
            << "Two independent MATCH operations: O(n + m) for linear scans\n"
            << "FILTER: O(n)\n"
            << "UNIQUE with ordered set: O(n log n)\n"
            << "SORTBY: O(n log n) average\n"
            << "SUMIFS-style scan: O(n)\n"
            << "SUMPRODUCT: O(n)\n"
            << "Index construction with unordered_map: O(n) average\n"
            << "Indexed exact lookup afterward: O(1) average\n";

        cout
            << "\nDesign trade-off:\n"
            << "An index consumes memory and has construction cost, but it can "
            << "be beneficial when many exact lookups are performed against "
            << "the same dataset.\n";


        // ====================================================================
        // R. FORMULA MAPPING
        // ====================================================================

        section("17. FORMULA-TO-IMPLEMENTATION MAPPING");

        cout
            << "INDEX       -> excelIndex()\n"
            << "MATCH       -> excelMatchExact()\n"
            << "INDEX+MATCH -> indexMatch()\n"
            << "2D lookup   -> twoWayLookup()\n"
            << "FILTER      -> excelFilter()\n"
            << "UNIQUE      -> excelUnique()\n"
            << "SORTBY      -> excelSortBy()\n"
            << "SUMIFS      -> sumIf()\n"
            << "COUNTIFS    -> countIf()\n"
            << "AVERAGEIFS  -> averageIf()\n"
            << "SUMPRODUCT  -> sumProduct()\n"
            << "RANK.EQ     -> rankDescending()\n"
            << "Running sum -> runningTotal()\n"
            << "Lookup index-> OrderIndex\n";


        // ====================================================================
        // S. PRODUCTION CONSIDERATIONS
        // ====================================================================

        section("18. PRODUCTION CONSIDERATIONS");

        cout
            << "1. Validate source data before calculating results.\n"
            << "2. Keep lookup keys unique when uniqueness is required.\n"
            << "3. Avoid approximate matching against unsorted thresholds.\n"
            << "4. Use explicit error handling for missing identifiers.\n"
            << "5. Keep calculation ranges appropriately sized.\n"
            << "6. Prefer reusable intermediate calculations for complex logic.\n"
            << "7. Use indexes when repeated exact lookups justify their memory cost.\n"
            << "8. Treat external data as untrusted input and validate it before "
               "using it in calculations.\n"
            << "9. Preserve auditability when advanced formulas are used in "
               "financial or operational workbooks.\n"
            << "10. Test boundary values, blanks, duplicates, missing values, "
               "zero denominators, and unexpected data types.\n";


        section("CASE STUDY COMPLETE");

        return 0;
    }
    catch (const exception& error) {
        cerr
            << "\nFatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
